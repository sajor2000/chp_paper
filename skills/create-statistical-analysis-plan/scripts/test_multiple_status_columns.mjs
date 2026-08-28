import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const fixturePath = path.resolve(scriptDir, '../references/test-fixtures/multiple-status-columns.json');
const builderPath = path.resolve(scriptDir, 'build_sap.mjs');
const validatorPath = path.resolve(scriptDir, 'validate_sap.mjs');
const templatePath = path.resolve(scriptDir, '../assets/SAP_Analysis_Plan_Template.xlsx');
const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'sap-multiple-status-'));
const validWorkbookPath = path.join(tempDir, 'valid.xlsx');
const invalidSpecPath = path.join(tempDir, 'invalid.json');
const require = createRequire(path.join(process.cwd(), 'package.json'));
const { FileBlob, SpreadsheetFile } = require('@oai/artifact-tool');
const caseIndex = process.argv.indexOf('--case');
const testCase = caseIndex >= 0 ? process.argv[caseIndex + 1] : 'all';
assert.ok(['all', 'builder', 'validator'].includes(testCase), `unknown --case ${testCase}`);

function run(scriptPath, args) {
  return spawnSync(process.execPath, [scriptPath, ...args], {
    cwd: process.cwd(),
    encoding: 'utf8',
  });
}

const failures = [];
if (testCase === 'all' || testCase === 'builder') {
  const buildValid = run(builderPath, ['--spec', fixturePath, '--output', validWorkbookPath]);
  assert.equal(buildValid.status, 0, `fixture build failed:\n${buildValid.stdout}\n${buildValid.stderr}`);
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(validWorkbookPath));
  const protocol = wb.worksheets.getItem('Protocol');
  assert.ok(protocol, 'fixture workbook must contain Protocol');
  const reviewValidation = protocol.getRange('B5').dataValidation;
  const approvalValidation = protocol.getRange('C5').dataValidation;
  if (JSON.stringify(reviewValidation?.rule?.values) !== JSON.stringify(['Blocked', 'Open'])) {
    failures.push('Review Status must receive list validation');
  }
  if (JSON.stringify(approvalValidation?.rule?.values) !== JSON.stringify(['Blocked', 'Open'])) {
    failures.push('Approval Status must receive list validation');
  }
}

if (testCase === 'all' || testCase === 'validator') {
  const invalidSpec = JSON.parse(await fs.readFile(fixturePath, 'utf8'));
  invalidSpec.annexes[0].rows[0]['Approval Status'] = 'Outside vocabulary';
  await fs.writeFile(invalidSpecPath, `${JSON.stringify(invalidSpec, null, 2)}\n`);
  const validateInvalid = run(validatorPath, ['--workbook', templatePath, '--spec', invalidSpecPath]);
  if (validateInvalid.status === 0) {
    failures.push('validator must reject a value outside the vocabulary in every Status column');
  } else if (!/Approval Status.*outside validation\.statusValues: Outside vocabulary/.test(validateInvalid.stderr)) {
    failures.push(`validator rejection did not identify Approval Status:\n${validateInvalid.stderr}`);
  }
}

assert.deepEqual(failures, [], `multiple status-column regression failed:\n- ${failures.join('\n- ')}`);

console.log('multiple status-column regression PASSED');
