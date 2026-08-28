import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';

const require = createRequire(path.join(process.cwd(), 'package.json'));
const { FileBlob, SpreadsheetFile } = require('@oai/artifact-tool');

function arg(name) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : undefined; }
const workbookPath = path.resolve(arg('--workbook') ?? '');
const specPath = arg('--spec') ? path.resolve(arg('--spec')) : undefined;
const spec = specPath ? JSON.parse(await fs.readFile(specPath, 'utf8')) : {};
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const failures = [];
const names = wb.worksheets.items.map((s) => s.name);
const front = ['Overview', 'Outputs', 'Master Variables'];
if (JSON.stringify(names.slice(0, 3)) !== JSON.stringify(front)) failures.push(`first sheets must be ${front.join(', ')}`);

const statusValues = spec.validation?.statusValues ?? [];
if (statusValues.length && `"${statusValues.join(',')}"`.length > 255) failures.push('validation.statusValues exceeds Excel inline-list limit of 255 characters');
for (const annex of spec.annexes ?? []) {
  const statusColumns = (annex.columns ?? []).filter((column) => /status/i.test(column));
  if (!statusColumns.length || !statusValues.length) continue;
  for (const statusColumn of statusColumns) {
    for (const row of annex.rows ?? []) {
      const value = row[statusColumn];
      if (value && !statusValues.includes(value)) failures.push(`${annex.name} ${statusColumn} uses status outside validation.statusValues: ${value}`);
    }
  }
}

const headers = {
  Overview: ['Analysis', 'Claim', 'Unit of Analysis', 'Data File(s)', 'Analysis Question', 'Primary Method', 'Secondary Methods', 'Site Script'],
  Outputs: ['Output File', 'Subfolder', 'Dataset / Cohort Scope', 'Script Section', 'Contents', 'Role at Coordinating Center', 'Interpretation'],
};
for (const [sheetName, expected] of Object.entries(headers)) {
  const s = wb.worksheets.getItem(sheetName);
  if (!s) { failures.push(`missing ${sheetName}`); continue; }
  const got = s.getRange(`A1:${String.fromCharCode(64 + expected.length)}1`).values[0];
  if (JSON.stringify(got) !== JSON.stringify(expected)) failures.push(`${sheetName} header mismatch`);
}
for (const sheetName of ['Overview', 'Master Variables']) {
  const s = wb.worksheets.getItem(sheetName);
  if (s && s.tables.items.length < 1) failures.push(`${sheetName} must contain a filterable table`);
}
for (const name of spec.validation?.requiredAnnexes ?? []) if (!names.includes(name)) failures.push(`missing annex ${name}`);
if (names.some((x) => x.length > 31)) failures.push('sheet name exceeds Excel 31-character limit');
if (new Set(names).size !== names.length) failures.push('duplicate sheet names');

const errorScan = await wb.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A', options: { useRegex: true, maxResults: 300 }, summary: 'formula errors' });
if (/"matchCount":\s*[1-9]/.test(errorScan.ndjson ?? '')) failures.push('formula error tokens found');

if (failures.length) { console.error(`SAP validation FAILED\n- ${failures.join('\n- ')}`); process.exit(1); }
console.log(`SAP validation PASSED: ${names.length} sheets; ${names.join(', ')}`);
