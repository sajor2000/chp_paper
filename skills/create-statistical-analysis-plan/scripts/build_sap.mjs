import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';

const require = createRequire(path.join(process.cwd(), 'package.json'));
const { SpreadsheetFile, Workbook } = require('@oai/artifact-tool');

function arg(name) {
  const i = process.argv.indexOf(name);
  if (i < 0 || !process.argv[i + 1]) throw new Error(`Missing ${name}`);
  return process.argv[i + 1];
}

const specPath = path.resolve(arg('--spec'));
const outputPath = path.resolve(arg('--output'));
const spec = JSON.parse(await fs.readFile(specPath, 'utf8'));
const wb = Workbook.create();

const BLUE = '#1F4E79';
const LIGHT = '#F2F2F2';
const BORDER = '#D9E1F2';
const WHITE = '#FFFFFF';
const CATEGORY = ['#D9EAD3', '#D9EAF7', '#FFF2CC', '#FCE5CD', '#EADCF8', '#DDEBF7', '#E2F0D9', '#F4CCCC'];
const DEFAULT_STATUS_VALUES = ['Fixed', 'Required', 'Open', 'Pending', 'NOT PASSED', 'Not applicable'];

const overviewColumns = ['Analysis', 'Claim', 'Unit of Analysis', 'Data File(s)', 'Analysis Question', 'Primary Method', 'Secondary Methods', 'Site Script'];
const outputColumns = ['Output File', 'Subfolder', 'Dataset / Cohort Scope', 'Script Section', 'Contents', 'Role at Coordinating Center', 'Interpretation'];
const variableColumns = ['Category', 'Variable', 'Description', 'Type', 'Format / Values', 'File', ...(spec.analysisColumns ?? []), 'Notes / Resolved Decisions'];

function colLetter(n) {
  let s = '';
  while (n > 0) { n--; s = String.fromCharCode(65 + (n % 26)) + s; n = Math.floor(n / 26); }
  return s;
}

function writeRow(sheet, row, columns, values) {
  sheet.getRange(`A${row}:${colLetter(columns.length)}${row}`).values = [columns.map((c) => values?.[c] ?? '')];
}

function baseSheet(name) {
  const s = wb.worksheets.add(name);
  s.showGridLines = false;
  return s;
}

function styleHeader(sheet, row, count) {
  const r = sheet.getRange(`A${row}:${colLetter(count)}${row}`);
  r.format = { fill: BLUE, font: { name: 'Calibri', size: 10, bold: true, color: WHITE }, wrapText: true, verticalAlignment: 'center', borders: { preset: 'all', style: 'thin', color: BORDER }, rowHeight: 30 };
}

function styleRows(sheet, start, end, count) {
  if (end < start) return;
  for (let r = start; r <= end; r++) {
    const range = sheet.getRange(`A${r}:${colLetter(count)}${r}`);
    range.format = { fill: r % 2 ? WHITE : LIGHT, font: { name: 'Calibri', size: 10 }, wrapText: true, verticalAlignment: 'top', borders: { preset: 'all', style: 'thin', color: BORDER } };
  }
}

function setWidths(sheet, widths) {
  widths.forEach((w, i) => { sheet.getRange(`${colLetter(i + 1)}:${colLetter(i + 1)}`).format.columnWidth = w; });
}

function addOperationalTable(sheet, range, name) {
  const table = sheet.tables.add(range, true, name);
  table.showHeaders = true;
  table.showFilterButton = true;
  return table;
}

function addStatusControls(sheet, columnIndex, startRow, endRow) {
  if (columnIndex < 0 || endRow < startRow) return;
  const letter = colLetter(columnIndex + 1);
  const range = sheet.getRange(`${letter}${startRow}:${letter}${endRow}`);
  range.dataValidation = { rule: { type: 'list', values: spec.validation?.statusValues ?? DEFAULT_STATUS_VALUES } };
  range.conditionalFormats.add('containsText', { text: 'NOT PASSED', format: { fill: '#F4CCCC', font: { bold: true, color: '#9C0006' } } });
  range.conditionalFormats.add('containsText', { text: 'Blocked', format: { fill: '#F4CCCC', font: { bold: true, color: '#9C0006' } } });
  range.conditionalFormats.add('containsText', { text: 'PENDING', format: { fill: '#FFF2CC', font: { color: '#7F6000' } } });
  range.conditionalFormats.add('containsText', { text: 'Pending', format: { fill: '#FFF2CC', font: { color: '#7F6000' } } });
  range.conditionalFormats.add('containsText', { text: 'Open', format: { fill: '#FFF2CC', font: { color: '#7F6000' } } });
  range.conditionalFormats.add('containsText', { text: 'Recheck', format: { fill: '#FFF2CC', font: { color: '#7F6000' } } });
  range.conditionalFormats.add('containsText', { text: 'Fixed', format: { fill: '#E2F0D9', font: { bold: true, color: '#006100' } } });
  range.conditionalFormats.add('containsText', { text: 'Complete', format: { fill: '#E2F0D9', font: { bold: true, color: '#006100' } } });
}

{
  const s = baseSheet('Overview');
  writeRow(s, 1, overviewColumns, Object.fromEntries(overviewColumns.map((x) => [x, x])));
  (spec.overview ?? []).forEach((row, i) => writeRow(s, i + 2, overviewColumns, row));
  addOperationalTable(s, `A1:H${Math.max(2, (spec.overview ?? []).length + 1)}`, 'OverviewTable');
  styleHeader(s, 1, overviewColumns.length);
  styleRows(s, 2, (spec.overview ?? []).length + 1, overviewColumns.length);
  setWidths(s, [21, 22, 19, 22, 38, 34, 34, 23]);
  s.freezePanes.freezeRows(1);
  s.getRange(`A1:H${Math.max(2, (spec.overview ?? []).length + 1)}`).format.autofitRows();
}

{
  const s = baseSheet('Outputs');
  writeRow(s, 1, outputColumns, Object.fromEntries(outputColumns.map((x) => [x, x])));
  styleHeader(s, 1, outputColumns.length);
  let r = 2;
  for (const section of spec.outputs ?? []) {
    s.getRange(`A${r}:G${r}`).merge();
    s.getRange(`A${r}`).values = [[section.section]];
    s.getRange(`A${r}:G${r}`).format = { fill: BLUE, font: { name: 'Calibri', size: 10, bold: true, color: WHITE }, rowHeight: 20, verticalAlignment: 'center' };
    r++;
    for (const row of section.rows ?? []) { writeRow(s, r, outputColumns, row); styleRows(s, r, r, outputColumns.length); r++; }
  }
  setWidths(s, [28, 20, 30, 25, 40, 31, 42]);
  s.freezePanes.freezeRows(1);
  s.getRange(`A1:G${Math.max(2, r - 1)}`).format.autofitRows();
}

{
  const s = baseSheet('Master Variables');
  for (let r = 1; r <= 2; r++) {
    s.getRange(`A${r}:${colLetter(variableColumns.length)}${r}`).merge();
    s.getRange(`A${r}`).values = [[(spec.variableNotes ?? [])[r - 1] ?? '']];
    s.getRange(`A${r}:${colLetter(variableColumns.length)}${r}`).format = { fill: BLUE, font: { name: 'Calibri', size: 10, bold: true, color: WHITE }, wrapText: true, rowHeight: 26, verticalAlignment: 'center' };
  }
  writeRow(s, 3, variableColumns, Object.fromEntries(variableColumns.map((x) => [x, x])));
  const colorMap = new Map();
  (spec.variables ?? []).forEach((row, i) => {
    const rr = i + 4;
    writeRow(s, rr, variableColumns, row);
  });
  addOperationalTable(s, `A3:${colLetter(variableColumns.length)}${Math.max(4, (spec.variables ?? []).length + 3)}`, 'MasterVariablesTable');
  styleHeader(s, 3, variableColumns.length);
  (spec.variables ?? []).forEach((row, i) => {
    const rr = i + 4;
    styleRows(s, rr, rr, variableColumns.length);
    const cat = row.Category ?? '';
    if (!colorMap.has(cat)) colorMap.set(cat, CATEGORY[colorMap.size % CATEGORY.length]);
    s.getRange(`A${rr}`).format.fill = colorMap.get(cat);
    s.getRange(`A${rr}`).format.font = { name: 'Calibri', size: 10, bold: true };
  });
  const widths = [20, 24, 42, 16, 28, 25, ...Array((spec.analysisColumns ?? []).length).fill(15), 46];
  setWidths(s, widths);
  s.freezePanes.freezeRows(3);
  s.getRange(`A3:${colLetter(variableColumns.length)}${Math.max(4, (spec.variables ?? []).length + 3)}`).format.autofitRows();
}

for (const annex of spec.annexes ?? []) {
  const cols = annex.columns ?? [];
  const s = baseSheet(annex.name);
  const last = colLetter(Math.max(1, cols.length));
  s.getRange(`A1:${last}1`).merge();
  s.getRange('A1').values = [[annex.title ?? annex.name]];
  s.getRange(`A1:${last}1`).format = { fill: BLUE, font: { name: 'Calibri', size: 14, bold: true, color: WHITE }, rowHeight: 28, verticalAlignment: 'center' };
  s.getRange(`A2:${last}2`).merge();
  s.getRange('A2').values = [[annex.note ?? '']];
  s.getRange(`A2:${last}2`).format = { fill: '#D9EAF7', font: { name: 'Calibri', size: 10, italic: true, color: '#17365D' }, wrapText: true, rowHeight: 30, verticalAlignment: 'center' };
  writeRow(s, 4, cols, Object.fromEntries(cols.map((x) => [x, x])));
  styleHeader(s, 4, cols.length);
  (annex.rows ?? []).forEach((row, i) => writeRow(s, i + 5, cols, row));
  styleRows(s, 5, (annex.rows ?? []).length + 4, cols.length);
  cols.forEach((column, columnIndex) => {
    if (/status/i.test(column)) addStatusControls(s, columnIndex, 5, (annex.rows ?? []).length + 4);
  });
  setWidths(s, cols.map((c) => /description|definition|decision|rationale|interpret|requirement|language|method|notes/i.test(c) ? 42 : /source|reference|file|output/i.test(c) ? 30 : 19));
  s.freezePanes.freezeRows(4);
  s.getRange(`A1:${last}${Math.max(5, (annex.rows ?? []).length + 4)}`).format.autofitRows();
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const blob = await SpreadsheetFile.exportXlsx(wb);
await blob.save(outputPath);
console.log(`Built ${outputPath} with ${wb.worksheets.items.length} sheets`);
