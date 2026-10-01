// Run against an isolated copy of the delivered app with a fresh DATA_DIR.
// Usage: node tasks/sheet-score-diagnosis/repro.mjs http://127.0.0.1:<port>
const base = process.argv[2];
if (!base || !/^http:\/\/127\.0\.0\.1:\d+$/.test(base)) {
  throw new Error('Pass an isolated http://127.0.0.1:<port> app URL');
}

async function request(method, path, body) {
  const response = await fetch(base + path, {
    method,
    headers: { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return { status: response.status, body: await response.json() };
}

const listed = await request('GET', '/api/workbooks');
const seed = listed.body.workbooks.find((w) => w.name === 'Q3 Sales');
if (!seed) throw new Error('Q3 Sales seed is absent');
const seeded = (await request('GET', `/api/workbooks/${seed.id}`)).body.worksheets[0];

const created = (await request('POST', '/api/workbooks', { name: 'Diagnosis probe' })).body;
const id = created.id;
const sourceId = created.worksheets[0].id;
for (const [coord, input] of Object.entries({
  A1: 'Region', B1: 'Sales', A2: 'East', B2: '1200', A3: 'North', B3: 'N/A',
})) {
  await request('PUT', `/api/workbooks/${id}/worksheets/${sourceId}/cells/${coord}`, { input });
}
const withPivot = (await request('POST', `/api/workbooks/${id}/worksheets/${sourceId}/pivot`, {
  sourceRange: { startRow: 1, startCol: 1, endRow: 3, endCol: 2 },
})).body;
const pivot = await request('PUT', `/api/workbooks/${id}/worksheets/${withPivot.lastActiveWorksheet}/pivot`, {
  rows: 'Region', columns: null, values: 'Sales', summarizeBy: 'SUM',
});

await request('PUT', `/api/workbooks/${id}/worksheets/${sourceId}/validation-rules`, {
  rules: [{ type: 'numberRange', anchor: { row: 5, col: 1 }, focus: { row: 5, col: 1 }, min: 0, max: 100 }],
});
const formula = await request('PUT', `/api/workbooks/${id}/worksheets/${sourceId}/cells/A5`, { input: '=101' });

console.log(JSON.stringify({
  seed: { A1: seeded.cells.A1 ?? '', B1: seeded.cells.B1 ?? '', C1: seeded.cells.C1 ?? '', A2: seeded.cells.A2 ?? '', B2: seeded.cells.B2 ?? '' },
  mixedPivot: { status: pivot.status, error: pivot.body.error ?? null },
  validatedFormula: { status: formula.status, display: formula.body.worksheets?.find((w) => w.id === sourceId)?.results.A5 ?? null },
}, null, 2));
