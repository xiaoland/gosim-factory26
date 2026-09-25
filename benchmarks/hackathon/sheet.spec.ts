import { cell, editCell, expect, openWorkbook, scenario, selectRange, start } from './support';

const unique = () => `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

async function sheetMenu(page: any, name: string, item: string) {
  await page.getByRole('button', { name: `Worksheet options for ${name}` }).click();
  await page.getByRole('menuitem', { name: item, exact: true }).click();
}

async function dataMenu(page: any, item: string) {
  await page.getByRole('button', { name: 'Data', exact: true }).click();
  await page.getByRole('menuitem', { name: item, exact: true }).click();
}

scenario('sheet-req-1-1-1', 'View and Open a Workbook', async ({ page, prepare, verify }) => {
  let editorUrl = '';
  await prepare('open seeded workbook', async () => {
    await start(page);
    await expect(page.getByRole('link', { name: 'Q3 Sales', exact: true })).toBeVisible();
    await expect(page.getByText(/Last updated:/).first()).toBeVisible();
    await page.getByRole('link', { name: 'Q3 Sales', exact: true }).click();
    editorUrl = page.url();
  });
  await verify('expose accessible editor and stable address', async () => {
    await expect(page.getByRole('grid', { name: 'Worksheet grid' })).toHaveAttribute('aria-multiselectable', 'true');
    await expect(page.getByRole('tab', { name: 'Sheet1' })).toHaveAttribute('aria-selected', 'true');
    await expect(cell(page, 'A1')).toContainText('Region');
    await page.reload();
    await expect(page).toHaveURL(editorUrl);
    await expect(page.getByText('Q3 Sales', { exact: true }).first()).toBeVisible();
  });
});

scenario('sheet-req-1-2-1', 'Create a Blank Workbook', async ({ page, prepare, verify }) => {
  await prepare('open blank workbook creation', async () => { await start(page); await page.getByRole('button', { name: 'New blank workbook' }).click(); });
  await verify('create and enter a blank Sheet1', async () => {
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('tab', { name: 'Sheet1' })).toHaveAttribute('aria-selected', 'true');
    await expect(cell(page, 'A1')).toHaveAttribute('aria-selected', 'true');
    await page.reload();
    await expect(page.getByRole('tab', { name: 'Sheet1' })).toHaveAttribute('aria-selected', 'true');
  });
});

scenario('sheet-req-1-2-2', 'Rename a Workbook', async ({ page, prepare, verify }) => {
  const name = `Workbook ${unique()}`;
  await prepare('open workbook editor', () => openWorkbook(page));
  await verify('reject empty and persist valid rename', async () => {
    await page.getByRole('button', { name: 'Rename workbook' }).click();
    await page.getByLabel('Workbook name').fill('   ');
    await page.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(page.getByText('Workbook name cannot be empty')).toBeVisible();
    await page.getByLabel('Workbook name').fill(`  ${name}  `);
    await page.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(page.getByText(name, { exact: true }).first()).toBeVisible();
    await page.reload(); await expect(page.getByText(name, { exact: true }).first()).toBeVisible();
  });
});

scenario('sheet-req-1-3-1', 'Import CSV to Create a Workbook', async ({ page, prepare, verify }) => {
  const filename = `import-${unique()}.csv`;
  await prepare('open CSV import', async () => { await start(page); await page.getByRole('button', { name: 'Import CSV' }).click(); });
  await verify('import quoted multilingual CSV and persist it', async () => {
    await page.getByLabel('CSV file').setInputFiles({ name: filename, mimeType: 'text/csv', buffer: Buffer.from('Name,Note,Value\n中文,"a,b",12\nLine,"one\ntwo",') });
    await page.getByRole('button', { name: 'Confirm import' }).click();
    await expect(page.getByText(filename.slice(0, -4), { exact: true }).first()).toBeVisible();
    await expect(cell(page, 'A2')).toContainText('中文');
    await expect(cell(page, 'B2')).toContainText('a,b');
    await page.reload(); await expect(cell(page, 'A2')).toContainText('中文');
  });
});

scenario('sheet-req-1-3-2', 'Export the Current Worksheet as CSV', async ({ page, prepare, verify }) => {
  await prepare('open seeded workbook', () => openWorkbook(page));
  await verify('download current grid without changing it', async () => {
    const before = await cell(page, 'A1').textContent();
    const download = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Export CSV' }).click()]).then(([value]) => value);
    expect(download.suggestedFilename()).toMatch(/\.csv$/);
    expect((await download.createReadStream()) !== null).toBeTruthy();
    await expect(cell(page, 'A1')).toHaveText(before || '');
    await page.reload(); await expect(cell(page, 'A1')).toHaveText(before || '');
  });
});

scenario('sheet-req-2-1-1', 'Add a Worksheet', async ({ page, prepare, verify }) => {
  await prepare('open workbook', () => openWorkbook(page));
  await verify('add blank active Sheet2 and persist it', async () => {
    await page.getByRole('button', { name: 'Add worksheet' }).click();
    await expect(page.getByRole('tab', { name: 'Sheet2' })).toHaveAttribute('aria-selected', 'true');
    await expect(cell(page, 'A1')).toHaveAttribute('aria-selected', 'true');
    await page.reload(); await expect(page.getByRole('tab', { name: 'Sheet2' })).toBeVisible();
  });
});

scenario('sheet-req-2-1-2', 'Switch Worksheets', async ({ page, prepare, verify }) => {
  await prepare('create second worksheet', async () => { await openWorkbook(page); if (!await page.getByRole('tab', { name: 'Sheet2' }).count()) await page.getByRole('button', { name: 'Add worksheet' }).click(); await editCell(page, 'A1', 'Second sheet'); });
  await verify('switch isolated worksheet state and persist active tab', async () => {
    await page.getByRole('tab', { name: 'Sheet1' }).click(); await expect(cell(page, 'A1')).not.toContainText('Second sheet');
    await page.getByRole('tab', { name: 'Sheet2' }).click(); await expect(cell(page, 'A1')).toContainText('Second sheet');
    await page.reload(); await expect(page.getByRole('tab', { name: 'Sheet2' })).toHaveAttribute('aria-selected', 'true');
  });
});

scenario('sheet-req-2-1-3', 'Rename a Worksheet', async ({ page, prepare, verify }) => {
  await prepare('open workbook', () => openWorkbook(page));
  await verify('reject empty then persist unique name', async () => {
    await sheetMenu(page, 'Sheet1', 'Rename');
    const dialog = page.getByRole('dialog', { name: 'Rename worksheet' });
    await dialog.getByLabel('Worksheet name').fill(' '); await dialog.getByRole('button', { name: 'Save' }).click();
    await expect(dialog.getByText('Worksheet name cannot be empty')).toBeVisible();
    await dialog.getByLabel('Worksheet name').fill('Data'); await dialog.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByRole('tab', { name: 'Data' })).toBeVisible(); await page.reload(); await expect(page.getByRole('tab', { name: 'Data' })).toBeVisible();
  });
});

scenario('sheet-req-2-1-4', 'Delete a Worksheet', async ({ page, prepare, verify }) => {
  await prepare('create second worksheet', async () => { await openWorkbook(page); if (!await page.getByRole('tab', { name: 'Sheet2' }).count()) await page.getByRole('button', { name: 'Add worksheet' }).click(); });
  await verify('delete Sheet2 and retain Sheet1', async () => {
    await sheetMenu(page, 'Sheet2', 'Delete');
    await expect(page.getByRole('dialog', { name: 'Delete worksheet' })).toContainText('Sheet2');
    await page.getByRole('button', { name: 'Delete worksheet' }).click();
    await expect(page.getByRole('tab', { name: 'Sheet2' })).toHaveCount(0);
    await page.reload(); await expect(page.getByRole('tab', { name: 'Sheet1' })).toBeVisible();
  });
});

scenario('sheet-req-2-2-1', 'Insert and Delete Rows', async ({ page, prepare, verify }) => {
  await prepare('prepare row values', async () => { await openWorkbook(page); await editCell(page, 'A1', 'Item'); await editCell(page, 'A2', 'Pen'); });
  await verify('insert and delete a complete row', async () => {
    await page.getByRole('rowheader', { name: '2', exact: true }).click({ button: 'right' });
    await page.getByRole('menuitem', { name: 'Insert 1 row above' }).click();
    await expect(cell(page, 'A3')).toContainText('Pen');
    await page.getByRole('rowheader', { name: '2', exact: true }).click({ button: 'right' }); await page.getByRole('menuitem', { name: 'Delete row' }).click();
    await expect(cell(page, 'A2')).toContainText('Pen'); await page.reload(); await expect(cell(page, 'A2')).toContainText('Pen');
  });
});

scenario('sheet-req-2-2-2', 'Insert and Delete Columns', async ({ page, prepare, verify }) => {
  await prepare('prepare column values', async () => { await openWorkbook(page); await editCell(page, 'A1', 'Item'); await editCell(page, 'B1', 'Qty'); });
  await verify('insert and delete a complete column', async () => {
    await page.getByRole('columnheader', { name: 'B', exact: true }).click({ button: 'right' }); await page.getByRole('menuitem', { name: 'Insert 1 column left' }).click();
    await expect(cell(page, 'C1')).toContainText('Qty');
    await page.getByRole('columnheader', { name: 'B', exact: true }).click({ button: 'right' }); await page.getByRole('menuitem', { name: 'Delete column' }).click();
    await expect(cell(page, 'B1')).toContainText('Qty'); await page.reload(); await expect(cell(page, 'B1')).toContainText('Qty');
  });
});

scenario('sheet-req-3-1-1', 'Edit a Cell Through the Grid or Formula Bar', async ({ page, prepare, verify }) => {
  await prepare('open workbook', () => openWorkbook(page));
  await verify('commit values and preserve original formula', async () => {
    await editCell(page, 'A1', '2'); await editCell(page, 'B1', '3'); await editCell(page, 'C1', '=A1+B1');
    await expect(cell(page, 'C1')).toContainText('5'); await cell(page, 'C1').click(); await expect(page.getByLabel('Formula bar')).toHaveValue('=A1+B1');
    await page.reload(); await expect(cell(page, 'C1')).toContainText('5');
  });
});

scenario('sheet-req-3-1-2', 'Paste Two-Dimensional Table Data', async ({ page, prepare, verify }) => {
  await prepare('open workbook and grant clipboard', async () => { await openWorkbook(page); await page.context().grantPermissions(['clipboard-read', 'clipboard-write']); });
  await verify('paste an atomic rectangle', async () => {
    await page.evaluate(() => navigator.clipboard.writeText('Item\tQty\nPen\t4'));
    await cell(page, 'A1').click(); await page.keyboard.press('Control+V');
    await expect(cell(page, 'A1')).toContainText('Item'); await expect(cell(page, 'B2')).toContainText('4');
    await page.reload(); await expect(cell(page, 'B2')).toContainText('4');
  });
});

scenario('sheet-req-3-1-3', 'Select a Rectangular Cell Range', async ({ page, prepare, verify }) => {
  await prepare('open workbook', () => openWorkbook(page));
  await verify('persist complete rectangular ARIA selection', async () => { await selectRange(page, 'A1', 'B2'); await expect(cell(page, 'C1')).toHaveAttribute('aria-selected', 'false'); await page.reload(); await expect(cell(page, 'A1')).toHaveAttribute('aria-selected', 'true'); await expect(cell(page, 'B2')).toHaveAttribute('aria-selected', 'true'); });
});

scenario('sheet-req-3-2-1', 'Copy, Cut, and Paste Cell Ranges', async ({ page, prepare, verify }) => {
  await prepare('prepare source range', async () => { await openWorkbook(page); await editCell(page, 'A1', 'Item'); await editCell(page, 'B1', 'Qty'); await editCell(page, 'A2', 'Pen'); await editCell(page, 'B2', '4'); });
  await verify('copy rectangle preserving source', async () => { await selectRange(page, 'A1', 'B2'); await page.keyboard.press('Control+C'); await cell(page, 'D1').click(); await page.keyboard.press('Control+V'); await expect(cell(page, 'D1')).toContainText('Item'); await expect(cell(page, 'E2')).toContainText('4'); await expect(cell(page, 'A1')).toContainText('Item'); await page.reload(); await expect(cell(page, 'E2')).toContainText('4'); });
});

scenario('sheet-req-3-2-2', 'Undo and Redo Recent Operations', async ({ page, prepare, verify }) => {
  const other = `Undo isolation ${unique()}`;
  await prepare('create another workbook and edit Q3 Sales', async () => {
    await start(page);
    await page.getByRole('button', { name: 'New blank workbook' }).click();
    await page.getByLabel('Workbook name').fill(other);
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('link', { name: other, exact: true })).toBeVisible();
    await openWorkbook(page);
    await editCell(page, 'A1', 'Before');
    await editCell(page, 'A1', 'After');
  });
  await verify('undo redo and isolate another workbook', async () => {
    await page.getByRole('button', { name: 'Undo' }).click();
    await expect(cell(page, 'A1')).toContainText('Before');
    await page.getByRole('button', { name: 'Redo' }).click();
    await expect(cell(page, 'A1')).toContainText('After');
    await start(page);
    await page.getByRole('link', { name: other, exact: true }).click();
    await expect(page.getByText(other, { exact: true }).first()).toBeVisible();
    await page.getByRole('button', { name: 'Undo' }).click();
    await expect(page.getByText(other, { exact: true }).first()).toBeVisible();
    await expect(cell(page, 'A1')).toBeEmpty();
  });
});

scenario('sheet-req-4-1-1', 'Calculate Basic Expressions and Aggregate Functions', async ({ page, prepare, verify }) => {
  await prepare('prepare numeric values', async () => { await openWorkbook(page); await editCell(page, 'A1', '2'); await editCell(page, 'B1', '3'); await editCell(page, 'A2', '5'); });
  await verify('calculate references and aggregate functions', async () => { await editCell(page, 'C1', '=A1+B1'); await editCell(page, 'C2', '=SUM(A1:B1)'); await editCell(page, 'C3', '=AVERAGE(A1:A2)'); await expect(cell(page, 'C1')).toContainText('5'); await expect(cell(page, 'C2')).toContainText('5'); await expect(cell(page, 'C3')).toContainText('3.5'); await cell(page, 'C2').click(); await expect(page.getByLabel('Formula bar')).toHaveValue('=SUM(A1:B1)'); });
});

scenario('sheet-req-4-1-2', 'Copy Formulas and Adjust Relative References', async ({ page, prepare, verify }) => {
  await prepare('prepare source formula', async () => { await openWorkbook(page); await editCell(page, 'A1', '2'); await editCell(page, 'B1', '3'); await editCell(page, 'C1', '=A1+$B$1'); });
  await verify('adjust relative and retain absolute references', async () => { await cell(page, 'C1').click(); await page.keyboard.press('Control+C'); await cell(page, 'C2').click(); await page.keyboard.press('Control+V'); await cell(page, 'C2').click(); await expect(page.getByLabel('Formula bar')).toHaveValue('=A2+$B$1'); await page.reload(); await cell(page, 'C2').click(); await expect(page.getByLabel('Formula bar')).toHaveValue('=A2+$B$1'); });
});

scenario('sheet-req-4-2-1', 'Recalculate Dependent Formulas After Source Data Changes', async ({ page, prepare, verify }) => {
  await prepare('prepare dependency chain', async () => { await openWorkbook(page); await editCell(page, 'A1', '2'); await editCell(page, 'B1', '=A1+1'); await editCell(page, 'C1', '=B1*2'); });
  await verify('recalculate direct and indirect dependencies', async () => { await expect(cell(page, 'C1')).toContainText('6'); await editCell(page, 'A1', '4'); await expect(cell(page, 'B1')).toContainText('5'); await expect(cell(page, 'C1')).toContainText('10'); await page.reload(); await expect(cell(page, 'C1')).toContainText('10'); });
});

scenario('sheet-req-4-2-2', 'Display and Fix Formula Errors', async ({ page, prepare, verify }) => {
  await prepare('open workbook', () => openWorkbook(page));
  await verify('show stable errors and recover', async () => { await editCell(page, 'A1', '=1/0'); await expect(cell(page, 'A1')).toContainText('#DIV/0!'); await cell(page, 'A1').click(); await expect(page.getByLabel('Formula bar')).toHaveValue('=1/0'); await editCell(page, 'B1', '=UNKNOWN(1)'); await expect(cell(page, 'B1')).toContainText('#NAME?'); await editCell(page, 'A1', '=1+1'); await expect(cell(page, 'A1')).toContainText('2'); await page.reload(); await expect(cell(page, 'A1')).toContainText('2'); });
});

async function prepareSales(page: any) {
  await openWorkbook(page);
  const rows = [['Region', 'Sales', 'Status'], ['East', '1200', 'Open'], ['North', '800', 'Closed'], ['South', '700', 'Open']];
  for (let row = 0; row < rows.length; row++) for (let col = 0; col < 3; col++) await editCell(page, `${String.fromCharCode(65 + col)}${row + 1}`, rows[row][col]);
}

scenario('sheet-req-5-1-1', 'Sort a Data Range by a Specified Column', async ({ page, prepare, verify }) => {
  await prepare('prepare sales table and selection', async () => { await prepareSales(page); await selectRange(page, 'A1', 'C4'); });
  await verify('sort selected records with header preserved', async () => { await dataMenu(page, 'Sort range'); await page.getByLabel('Sort by').selectOption({ label: 'Sales' }); await page.getByLabel('Order').selectOption({ label: 'Ascending' }); await page.getByRole('checkbox', { name: 'Data has header row' }).check(); await page.getByRole('button', { name: 'Sort', exact: true }).click(); await expect(cell(page, 'A1')).toContainText('Region'); await expect(cell(page, 'A2')).toContainText('South'); await expect(cell(page, 'A4')).toContainText('East'); await page.reload(); await expect(cell(page, 'A2')).toContainText('South'); });
});

scenario('sheet-req-5-1-2', 'Filter Rows by Value or Condition', async ({ page, prepare, verify }) => {
  await prepare('prepare sales table and filter', async () => { await prepareSales(page); await selectRange(page, 'A1', 'C4'); await dataMenu(page, 'Create filter'); });
  await verify('filter values without deleting records', async () => { await page.getByRole('button', { name: 'Filter Status' }).click(); await page.getByRole('button', { name: 'Clear selection' }).click(); await page.getByRole('checkbox', { name: 'Open' }).check(); await page.getByRole('button', { name: 'Apply' }).click(); await expect(page.getByText('North', { exact: true })).toBeHidden(); await page.reload(); await expect(page.getByText('North', { exact: true })).toBeHidden(); await dataMenu(page, 'Clear filter'); await expect(page.getByText('North', { exact: true })).toBeVisible(); });
});

scenario('sheet-req-5-2-1', 'Set Dropdown or Numeric Validation for a Range', async ({ page, prepare, verify }) => {
  await prepare('select validation range', async () => { await openWorkbook(page); await selectRange(page, 'B2', 'B3'); await dataMenu(page, 'Data validation'); });
  await verify('persist and enforce numeric range atomically', async () => { await page.getByLabel('Rule type').selectOption({ label: 'Number range' }); await page.getByLabel('Minimum').fill('0'); await page.getByLabel('Maximum').fill('100'); await page.getByRole('button', { name: 'Save' }).click(); await editCell(page, 'B2', '50'); await editCell(page, 'B3', '101'); await expect(page.getByText('Please enter a number from 0 to 100')).toBeVisible(); await expect(cell(page, 'B2')).toContainText('50'); await expect(cell(page, 'B3')).not.toContainText('101'); await page.reload(); await editCell(page, 'B3', '101'); await expect(page.getByText('Please enter a number from 0 to 100')).toBeVisible(); });
});

scenario('sheet-req-5-3-1', 'Create and Refresh a Basic Pivot Table', async ({ page, prepare, verify }) => {
  await prepare('prepare source table and open pivot creation', async () => { await prepareSales(page); await selectRange(page, 'A1', 'C4'); await dataMenu(page, 'Create pivot table'); });
  await verify('create apply persist and refresh Pivot1', async () => { await expect(page.getByRole('dialog', { name: 'Create pivot table' })).toContainText(/Source range: A1:C4/); await page.getByRole('radio', { name: 'New worksheet' }).check(); await page.getByRole('button', { name: 'Create', exact: true }).click(); const editor = page.getByRole('region', { name: 'Pivot table editor' }); await editor.getByLabel('Rows').selectOption({ label: 'Region' }); await editor.getByLabel('Values').selectOption({ label: 'Sales' }); await editor.getByLabel('Summarize by').selectOption({ label: 'SUM' }); await editor.getByRole('button', { name: 'Apply' }).click(); await expect(page.getByRole('tab', { name: 'Pivot1' })).toBeVisible(); await expect(cell(page, 'A1')).toContainText('Region'); await expect(cell(page, 'B1')).toContainText('SUM of Sales'); await expect(page.getByText('Grand Total')).toBeVisible(); await page.reload(); await expect(page.getByRole('tab', { name: 'Pivot1' })).toBeVisible(); await page.getByRole('button', { name: 'Refresh pivot table' }).click(); await expect(page.getByText('Grand Total')).toBeVisible(); });
});
