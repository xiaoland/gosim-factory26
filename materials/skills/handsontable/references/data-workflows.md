# Data Workflows (Save, Sync, Validate, Import/Export)

> Last verified: July 2026 · against Handsontable 18.0 docs (handsontable/handsontable@develop docs source)
> Factory adaptation: October 2026 · save/sync examples checked against the 18.0 API contract; no application execution claimed.

End-to-end data patterns: persisting edits, syncing grids, dependent dropdowns, bulk validation,
import/export, and undo/redo. Framework is labeled per snippet (React uses
`@handsontable/react-wrapper`; vanilla uses `handsontable/base` + `registerAllModules()`).

## Saving to a backend

### The `afterChange` hook and its changes array

Track edits with `afterChange`. It receives `(changes, source)`; **always guard against
`source === 'loadData'`** or the initial data load will trigger a save. Each entry in `changes`
is a tuple `[row, prop, oldValue, newValue]`:

```javascript
afterChange(changes, source) {
  if (source === 'loadData' || !changes) {
    return;
  }
  changes.forEach(([row, prop, oldValue, newValue]) => {
    const column = this.propToCol(prop); // the visual column index
  });
}
```

`prop` is a property name with object data, a column index with array data, and — with function
data sources — the accessor function itself; normalize with `propToCol()`. Inside the hook, POST
`changes` (or `hot.getData()` for the full dataset) to your endpoint.

`afterChange` does **not** fire for structural changes such as row moves — listen to
`afterRowMove` and read the new order with `getData()`. If your save logic writes several
confirmed values back to the grid at once, wrap the writes in `batch()` so it re-renders once.

Docs: https://handsontable.com/docs/react-data-grid/saving-data/

### Debounced auto-save with serial writes

For cell edits to existing object rows, use immutable, unique string `id` values and retain
snapshots by ID. Convert the hook's visual index before reading source data. This local queue
sends one batch at a time; edits made during a request remain pending for a later batch.

```typescript
// Vanilla / TypeScript; use the same handler via React's afterChange prop.
type SavedRow = { id: string; [prop: string]: unknown };
const dirtyRows = new Map<string, SavedRow>();
let saveTimeout: ReturnType<typeof setTimeout> | null = null;
let saveQueue = Promise.resolve();

function scheduleSave() {
  if (saveTimeout !== null) clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    saveTimeout = null;
    saveQueue = saveQueue.then(async () => {
      const batch = new Map(dirtyRows);
      dirtyRows.clear();
      if (batch.size === 0) return;
      try {
        await saveRowsToBackend([...batch.values()]);
      } catch (error) {
        // A later local edit owns the newer snapshot for the same object.
        batch.forEach((row, id) => {
          if (!dirtyRows.has(id)) dirtyRows.set(id, row);
        });
        showSaveError(error); // display the failure and offer Retry -> scheduleSave()
      }
    });
  }, 800);
}

// in the grid settings:
afterChange(changes, source) {
  if (!changes || source === 'loadData') return;
  changes.forEach(([visualRow, _prop, oldValue, newValue]) => {
    if (oldValue === newValue) return;
    const physicalRow = hot.toPhysicalRow(visualRow);
    if (physicalRow === null || physicalRow === undefined) {
      throw new Error(`No source row for visual row ${visualRow}`);
    }
    const row = hot.getSourceDataAtRow(physicalRow) as SavedRow;
    dirtyRows.set(row.id, structuredClone(row));
  });
  scheduleSave();
}
```

`saveRowsToBackend` is the application's adapter: serialize the supplied snapshot, reject on
non-success HTTP responses, and resolve only after persistence is acknowledged. `showSaveError`
is a non-throwing UI callback that keeps the unsaved state visible and binds Retry to
`scheduleSave()`. A failed batch stays pending; a later edit or explicit Retry sends it again.
There is no automatic retry timer. Keep unsaved state while a debounce, request or dirty batch
exists, and dispose the timer only as part of a lifecycle that preserves or resolves those edits.

Serialization prevents overlapping writes from this queue when a completed response means the
server has finished that write. It does not order other tabs or users, or a timed-out request
that the server may still commit. Those cases need backend version/conflict control or a protocol
that both deduplicates retries and preserves write order; a UI request counter alone cannot protect stored
values. Treat row insertion, deletion, ID changes and dataset replacement as separate persistence
operations, rather than applying this cell-edit example to them.

Docs: https://handsontable.com/docs/18.0/javascript-data-grid/api/hooks/#afterchange · https://handsontable.com/docs/18.0/javascript-data-grid/api/core/#getsourcedataatrow

### `loadData()` vs `updateData()`

Both take the new dataset as their only argument — `hot.loadData(newDataset)` /
`hot.updateData(newDataset)` — and differ in what they reset:

| Method | Resets sort order | Resets selection | Resets column order | Use when |
|---|---|---|---|---|
| `loadData()` | Yes | Yes | Yes | Initial load, schema change, or hard reset |
| `updateData()` | No | No | No | Periodic refresh or live-data feed |

- `loadData()` fires `beforeLoadData` / `afterLoadData`; `updateData()` fires `beforeUpdateData`
  / `afterUpdateData`. `updateSettings({ data })` also replaces data; since v12 it uses
  `updateData()` under the hood (except the initial call, which uses `loadData()`).
- Refresh pattern: `loadData()` for the first fetch, `updateData()` for every later refresh so
  the user's sort/selection survives. On a failed refresh, call neither — existing data is valid.
- v17.1+ adds the `dataProvider` option (`rowId`, `fetchRows`, `onRowsCreate`, `onRowsUpdate`,
  `onRowsRemove`) for backend-driven pagination/sorting/CRUD; `multiColumnSorting` is
  incompatible with it — use `columnSorting` only.

Docs: https://handsontable.com/docs/react-data-grid/binding-to-data/ · https://handsontable.com/docs/react-data-grid/recipes/data-management/load-data-rest-api/

## Syncing grids / programmatic writes

Use stable business IDs across independently sorted, moved or trimmed grids. In this React
example both datasets are object rows with unique immutable `id` values and every changed
master object has exactly one detail object. `toDetailRow` maps fields without changing that ID.

```jsx
const SOURCE_SYNC_FROM_MASTER = 'sync-from-master';

const syncDetailRow = (masterRow) => {
  // ponytail: linear ID lookup; maintain an ID index if large grids make this costly.
  const detailPhysicalRow = detailHot.getSourceData()
    .findIndex((row) => row.id === masterRow.id);
  if (detailPhysicalRow === -1) {
    throw new Error(`Missing detail object ${masterRow.id}`);
  }
  const detailRow = toDetailRow(masterRow);
  detailHot.batch(() => {
    Object.entries(detailRow).forEach(([prop, value]) => {
      if (prop !== 'id') {
        detailHot.setSourceDataAtCell(detailPhysicalRow, prop, value, SOURCE_SYNC_FROM_MASTER);
      }
    });
  });
};

const handleMasterAfterChange = (changes, source) => {
  if (!changes || source === SOURCE_SYNC_FROM_MASTER || source === 'loadData') return;
  const changedVisualRows = new Set(changes.map(([visualRow]) => visualRow));
  changedVisualRows.forEach((visualRow) => {
    const physicalRow = masterHot.toPhysicalRow(visualRow);
    if (physicalRow === null || physicalRow === undefined) {
      throw new Error(`No source row for visual row ${visualRow}`);
    }
    syncDetailRow(masterHot.getSourceDataAtRow(physicalRow));
  });
};
```

Source writes use physical rows and object property names, including trimmed detail rows.
Observe them with `afterSetSourceDataAtCell` when needed, and guard the custom source there to
prevent a reverse sync loop. `batch()` combines renders. A `setDataAtCell` alternative needs
both destination visual row and column conversion; never reuse the master's row number.
If ordinary edit validation or `afterChange`-based saving is required, use converted visual
writes for visible rows, or explicitly validate and persist the source updates.
This example uses a linear ID lookup; maintain an ID index only if dataset size warrants it,
and update that index with structural changes. If missing details are valid, implement their
creation or exclusion explicitly instead of silently dropping a synchronization failure.

Docs: https://handsontable.com/docs/18.0/javascript-data-grid/api/core/#setsourcedataatcell · https://handsontable.com/docs/18.0/javascript-data-grid/api/hooks/#afterchange

## Dependent dropdowns

Drive a child `dropdown` column's `source` from the parent column's value with a per-row
`setCellMeta` swap, then call `render()`. Condensed from the recipe (React):

```jsx
// React
const CATEGORY_COL = 0;
const SUBCATEGORY_COL = 1;

const dependencyMap = {
  Fruit: ['Apple', 'Banana', 'Orange'],
  Vegetable: ['Carrot', 'Pea', 'Broccoli'],
};

const optionsForCategory = (category) => dependencyMap[category] ?? [];

function afterChange(changes, source) {
  if (!hot || source === 'loadData' || !changes) {
    return;
  }
  for (const change of changes) {
    const [row, prop, oldVal, newVal] = change;
    if (prop !== CATEGORY_COL || oldVal === newVal) {
      continue;
    }

    const next = optionsForCategory(String(newVal));
    hot.setCellMeta(row, SUBCATEGORY_COL, 'source', next);
    hot.setDataAtCell(row, SUBCATEGORY_COL, next[0] ?? ''); // reset stale child value
  }
  hot.render();
}
```

`setCellMeta(row, col, 'source', newOptions)` replaces the dropdown options for a single cell
only; `hot.render()` after `setCellMeta` is required for the editor to pick up the new options.
Run the same per-row `setCellMeta` loop from `afterInit` (loop `hot.countRows()`, read each
parent with `getDataAtCell(row, CATEGORY_COL)`) so every row is consistent on load.

Docs: https://handsontable.com/docs/react-data-grid/recipes/editing-validation/dependent-dropdowns/

## Row validation with error summary

Bulk-validate on Submit with a rule map keyed by column index, highlight failures with the
built-in `htInvalid` class via `setCellMeta`, list issues outside the grid, and auto-clear on
re-edit. Condensed from the recipe (React):

```jsx
// React
/** Column index -> returns `null` when valid, otherwise an error message. */
const validationRules = {
  0: (value) => (String(value ?? '').trim().length > 0 ? null : 'Item name is required'),
}; // ...one rule per validated column

function handleSubmit() {
  // 1. clear prior highlights: removeCellMeta(r, c, 'className') / (r, c, 'title')
  //    for every key in invalidCellsRef, then clear the Set
  // 2. scan every row against the rule map
  const newIssues = [];
  for (let row = 0; row < hot.countRows(); row++) {
    for (let col = 0; col < hot.countCols(); col++) {
      const rule = validationRules[col];
      if (!rule) continue;
      const message = rule(hot.getDataAtCell(row, col));
      if (message !== null) newIssues.push({ row, col, message });
    }
  }
  // 3. highlight failures and render
  newIssues.forEach((issue) => {
    hot.setCellMeta(issue.row, issue.col, 'className', 'htInvalid');
    hot.setCellMeta(issue.row, issue.col, 'title', issue.message); // native tooltip
    invalidCellsRef.current.add(cellKey(issue.row, issue.col));
  });
  hot.render();
  setIssues(newIssues); // external error list, e.g. "Row 3, Unit price: must be greater than 0"
}

function afterChange(changes, source) {
  if (!hot || source === 'loadData' || !changes) {
    return;
  }
  for (const change of changes) {
    const [row, prop] = change;
    const col = typeof prop === 'string' ? hot.propToCol(prop) : prop;
    const key = cellKey(row, col);
    if (!invalidCellsRef.current.has(key)) continue;
    // auto-clear the invalid state as soon as the user edits the cell
    hot.removeCellMeta(row, col, 'className');
    hot.removeCellMeta(row, col, 'title');
    invalidCellsRef.current.delete(key);
  }
  hot.render();
}
```

`cellKey(row, col)` is a `` `${row}:${col}` `` helper backing the invalid-cell `Set`. For
async per-edit validation instead of on-Submit, use cell validators.

Docs: https://handsontable.com/docs/react-data-grid/recipes/editing-validation/row-validation-error-summary/

## Import: CSV (PapaParse) and Excel (SheetJS)

Parse in the browser, then rebuild the grid's column shape from the detected header row.

```javascript
// CSV via PapaParse — header row becomes object keys, types inferred
PapaRef.parse(file, {
  header: true,
  dynamicTyping: true,
  skipEmptyLines: 'greedy',
  transformHeader: (h) => h.trim(),
  complete: (results) => { /* results.data + results.meta.fields */ },
});

// Excel via SheetJS — first sheet, row 0 as header line
const workbook = XLSXRef.read(buf, { type: 'array' }); // buf = await file.arrayBuffer()
const sheet = workbook.Sheets[workbook.SheetNames[0]];
const matrix = XLSXRef.utils.sheet_to_json(sheet, { header: 1, defval: null, raw: true });
```

Both parsers converge on `{ headers: string[], rows: object[] }`. Infer column types, then apply
them with `updateSettings()` **before** `loadData()`:

```javascript
function columnsFromHeaders(headers, rows) {
  return headers.map((data) => {
    const values = rows.map((row) => row[data]).filter((v) => v !== null);
    if (values.length > 0 && values.every((v) => typeof v === 'number')) {
      return { data, type: 'numeric' };
    }
    if (values.length > 0 && values.every((v) => typeof v === 'boolean')) {
      return { data, type: 'checkbox' };
    }
    return { data, type: 'text' };
  });
}
// re-import into an existing instance:
hot.updateSettings({ colHeaders: headers, columns });
hot.loadData(rows);
```

`updateSettings` must run before `loadData` so Handsontable knows which keys to read from the row
objects. Normalize empty cells to `null` so the grid shows blanks instead of `"undefined"`.

Docs: https://handsontable.com/docs/react-data-grid/recipes/import-export/import-csv-excel/

## Export: CSV, XLSX, PDF

### CSV — `ExportFile` plugin

Methods: `downloadFile(format, options)` (synchronous, text formats only), `exportAsBlob(format, options)`, `exportAsString(format, options)`.

```jsx
// React
const exportPlugin = hotRef.current?.hotInstance?.getPlugin('exportFile');
exportPlugin?.downloadFile('csv', {
  columnDelimiter: ',',
  colHeaders: false,
  exportHiddenColumns: true,
  exportHiddenRows: true,
  filename: 'Handsontable-CSV-file_[YYYY]-[MM]-[DD]',
  rowDelimiter: '\r\n',
  rowHeaders: true,
  sanitizeValues: true, // OWASP CSV-injection rules; also accepts RegExp or (value) => value
});
```

Other options: `bom` (default `true`), `fileExtension`, `mimeType`, `range`
(`[startRow, startColumn, endRow, endColumn]`, visual indexes). CSV export is raw data only — no
formulas, styling, or formatting. `sanitizeValues` guards against CSV/formula injection;
a `RegExp` escapes matching values, a function replaces them with its return value.

Docs: https://handsontable.com/docs/react-data-grid/export-to-csv/

### XLSX (v17.1+) — `downloadFileAsync` + ExcelJS peer dep

Install ExcelJS (`^4.4.0`), register it as the engine, then use the async methods
(`downloadFile` does not support XLSX):

```jsx
// React
import ExcelJS from 'exceljs';

<HotTable exportFile={{ engines: { xlsx: ExcelJS } }} />

const exportPlugin = hotRef.current?.hotInstance?.getPlugin('exportFile');
await exportPlugin?.downloadFileAsync('xlsx', { filename: 'my-report' });
// or: const blob = await exportPlugin.exportAsBlob('xlsx', { filename: 'my-report' });
```

XLSX export preserves what CSV can't: cell types (`numeric`, `date`, `time`, `checkbox`) as
native Excel types, DOM-derived styling (font, fill, alignment, `CustomBorders`), column/nested
headers, merged cells, frozen panes, and — with `exportFormulas: true` — HyperFormula and
ColumnSummary cells as live Excel formulas. `sheets: [{ instance, name, ... }]` exports multiple
grids into one workbook; the context menu gains an **Export to Excel** item once an ExcelJS
engine is configured.

Docs: https://handsontable.com/docs/react-data-grid/export-to-excel/

### PDF — `getData()` + jsPDF AutoTable

No built-in PDF export; read the grid and hand it to jsPDF + jspdf-autotable:

```javascript
// import { jsPDF } from 'jspdf'; import { autoTable } from 'jspdf-autotable';
const body = hot.getData(); // 2D array in current visual order (sorting included)
const head = [Array.from({ length: hot.countCols() }, (_, col) => String(hot.getColHeader(col)))];
const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
autoTable(doc, { head, body, showHead: 'everyPage' });
doc.save('export.pdf');
```

Docs: https://handsontable.com/docs/react-data-grid/recipes/import-export/export-to-pdf/

## Undo/redo with a custom UI

Enable with `undoRedo: true`, drive it via `getPlugin('undoRedo')`, keep button state in sync
from hooks:

```typescript
// Vanilla (React: same calls via hotRef.current?.hotInstance)
const syncHistoryButtons = () => {
  const undoRedoPlugin = hot.getPlugin('undoRedo');
  undoButton.disabled = !undoRedoPlugin.isUndoAvailable();
  redoButton.disabled = !undoRedoPlugin.isRedoAvailable();
};

undoButton.addEventListener('click', () => hot.getPlugin('undoRedo').undo());
redoButton.addEventListener('click', () => hot.getPlugin('undoRedo').redo());

hot.updateSettings({
  afterChange: () => syncHistoryButtons(),
  afterUndo: () => syncHistoryButtons(),
  afterRedo: () => syncHistoryButtons(),
});
syncHistoryButtons(); // both buttons start disabled — the stack is empty
```

Docs: https://handsontable.com/docs/react-data-grid/recipes/data-management/undo-redo-custom-ui/

## Pitfalls

- **Save loop from a missing source guard.** Any `afterChange` handler that writes data must
  bail on `source === 'loadData'` — and on your own custom source string when its writes land
  back in a grid it observes (`setDataAtCell(changes, 'my-source')` + guard).
- **`loadData()` resets grid state.** Since v12 it resets configuration options and index mapper
  information — sorting, selection, and column order all revert. Use `updateData()` to refresh.
- **`afterChange` misses structural changes.** Row moves don't fire it; listen to `afterRowMove`
  and read the result with `getData()`.
- **`prop` isn't always a column index.** With object data it's a property name; with function
  data sources it's the accessor function — normalize with `hot.propToCol(prop)`.
- **Changing column shape at import time:** call `updateSettings({ colHeaders, columns })`
  *before* `loadData(rows)`, or the grid won't know which keys to read from the new row objects.
- **`setCellMeta` changes aren't visible until `hot.render()`** — dropdown `source` swaps and
  `htInvalid` highlights both need it. Wrap bulk programmatic writes in `batch()`.

Docs index: https://handsontable.com/docs/react-data-grid/recipes/
