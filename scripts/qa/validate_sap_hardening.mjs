import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';

function arg(name, required = true) {
  const i = process.argv.indexOf(name);
  const value = i >= 0 ? process.argv[i + 1] : undefined;
  if (required && !value) throw new Error(`Missing ${name}`);
  return value;
}

const specPath = path.resolve(arg('--spec'));
const narrativePath = path.resolve(arg('--narrative'));
const workbookArg = arg('--workbook', false);
const spec = JSON.parse(await fs.readFile(specPath, 'utf8'));
const narrative = await fs.readFile(narrativePath, 'utf8');
const specText = JSON.stringify(spec);
const failures = [];

function requireText(haystack, needle, label) {
  if (!haystack.includes(needle)) failures.push(`${label}: missing ${needle}`);
}

function forbidText(haystack, needle, label) {
  if (haystack.includes(needle)) failures.push(`${label}: forbidden ${needle}`);
}

for (const [needle, label] of [
  ['two-sided 97.5% confidence intervals', 'primary multiplicity'],
  ['OLS remains the principal estimator', 'principal model'],
  ['model-sensitive', 'spatial interpretation'],
  ['9999 conditional random permutations', 'Moran implementation'],
  ['annual observed-adult records', 'pooled EHR interpretation'],
  ['sum(matched annual ACS adult-population denominators)', 'capture formula'],
  ['precision-weighted sensitivity', 'outcome uncertainty'],
]) requireText(narrative, needle, label);

forbidText(
  narrative,
  'spatial-error estimate becomes the principal reported estimate',
  'principal model',
);
requireText(specText, 'Biostat Handoff', 'handoff sheet');
requireText(specText, 'Fixed Scoring Rule', 'selection anchors');
requireText(specText, '97.5% CIs', 'workbook multiplicity');
requireText(specText, 'Narrative SAP Section', 'traceability');

if (workbookArg) {
  const require = createRequire(path.join(process.cwd(), 'package.json'));
  const { FileBlob, SpreadsheetFile } = require('@oai/artifact-tool');
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.resolve(workbookArg)));
  const names = wb.worksheets.items.map((sheet) => sheet.name);
  const expected = ['Overview', 'Outputs', 'Master Variables', 'Biostat Handoff'];
  if (JSON.stringify(names.slice(0, 4)) !== JSON.stringify(expected)) {
    failures.push(`sheet order: ${JSON.stringify(names.slice(0, 4))}`);
  }
  const workbookText = wb.worksheets.items
    .flatMap((sheet) => sheet.getUsedRange(true)?.values?.flat(2) ?? [])
    .filter((value) => value !== null && value !== undefined)
    .join('\n');
  for (const needle of [
    '97.5% CIs',
    'OLS remains principal',
    'model-sensitive',
    'Fixed Scoring Rule',
  ]) requireText(workbookText, needle, 'workbook');
}

if (failures.length) {
  console.error(`SAP hardening contract FAILED\n- ${failures.join('\n- ')}`);
  process.exit(1);
}

console.log('SAP hardening contract PASSED');
