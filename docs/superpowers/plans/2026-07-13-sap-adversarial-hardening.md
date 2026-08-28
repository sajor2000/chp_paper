# ChicagoHealthMap SAP Adversarial Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a self-contained, biostatistician-executable ChicagoHealthMap SAP workbook that resolves every adversarial finding while preserving all S4-S7 blockers and the approved noncausal scientific design.

**Architecture:** The narrative SAP defines the complete scientific protocol, `docs/analysis/sap_workbook_spec.json` defines workbook content, and the repository-owned SAP skill deterministically generates and validates Excel. A project-specific contract prevents drift across narrative, JSON, and workbook; the generic builder supplies tables, filters, status controls, and visual consistency.

**Tech Stack:** Markdown, JSON, JavaScript ES modules, bundled Node.js, `@oai/artifact-tool`, Excel `.xlsx`, git.

## Global Constraints

- Do not write analysis or pipeline code and do not pass S4, S5, S6, or S7.
- Never hand-edit `ChicagoHealthMap_Draft_SAP.xlsx`; regenerate it from the committed JSON specification.
- Keep `Overview`, `Outputs`, and `Master Variables` as sheets 1-3; add `Biostat Handoff` as sheet 4.
- Use two-sided 97.5% Bonferroni-compatible confidence intervals for C1 and C2; nominal 95% intervals must be explicitly labeled estimation context or secondary.
- Unweighted OLS with HC3 remains the principal estimator; observed coefficient changes never switch the principal model.
- Preserve the reference pattern: Calibri 10, `#1F4E79` headers, alternating rows, section bands, category fills, wrapped text, and frozen panes.
- Use only the dependency runtime returned by `codex_app__load_workspace_dependencies`; do not use another spreadsheet library.
- Preserve missing, suppressed, unreliable, structural-zero, and true-zero states as distinct categories.
- Treat EHR relationships as ecological, associational, and noncausal; retain the FQHC/CBO question-formulation boundary.

---

### Task 1: Add a cross-artifact adversarial contract and correct the scientific sources

**Files:**
- Create: `scripts/qa/validate_sap_hardening.mjs`
- Modify: `docs/analysis/statistical_analysis_plan.md:132-177,200-248,286-321`
- Modify: `docs/analysis/sap_workbook_spec.json`
- Test: `scripts/qa/validate_sap_hardening.mjs`

**Interfaces:**
- Consumes: `--spec <json>`, `--narrative <markdown>`, and optional `--workbook <xlsx>`.
- Produces: exit `0` with `SAP hardening contract PASSED`; otherwise exit `1` with one line per missing or forbidden rule.

- [ ] **Step 1: Write the failing content contract**

Create `scripts/qa/validate_sap_hardening.mjs`:

```js
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

forbidText(narrative, 'spatial-error estimate becomes the principal reported estimate', 'principal model');
requireText(specText, 'Biostat Handoff', 'handoff sheet');
requireText(specText, 'Fixed Scoring Rule', 'selection anchors');
requireText(specText, '97.5% CIs', 'workbook multiplicity');
requireText(specText, 'Narrative SAP Section', 'traceability');

if (workbookArg) {
  const require = createRequire(path.join(process.cwd(), 'package.json'));
  const { FileBlob, SpreadsheetFile } = require('@oai/artifact-tool');
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.resolve(workbookArg)));
  const names = wb.worksheets.items.map((s) => s.name);
  const expected = ['Overview', 'Outputs', 'Master Variables', 'Biostat Handoff'];
  if (JSON.stringify(names.slice(0, 4)) !== JSON.stringify(expected)) {
    failures.push(`sheet order: ${JSON.stringify(names.slice(0, 4))}`);
  }
  const workbookText = wb.worksheets.items
    .flatMap((s) => s.getUsedRange(true)?.values?.flat(2) ?? [])
    .filter((v) => v !== null && v !== undefined)
    .join('\n');
  for (const needle of ['97.5% CIs', 'OLS remains principal', 'model-sensitive', 'Fixed Scoring Rule']) {
    requireText(workbookText, needle, 'workbook');
  }
}

if (failures.length) {
  console.error(`SAP hardening contract FAILED\n- ${failures.join('\n- ')}`);
  process.exit(1);
}
console.log('SAP hardening contract PASSED');
```

- [ ] **Step 2: Run the contract against current sources to verify RED**

```bash
node scripts/qa/validate_sap_hardening.mjs \
  --spec docs/analysis/sap_workbook_spec.json \
  --narrative docs/analysis/statistical_analysis_plan.md
```

Expected: exit `1` with missing-rule failures including `OLS remains the principal estimator`, `annual observed-adult records`, `capture formula`, `Biostat Handoff`, `Fixed Scoring Rule`, and `Narrative SAP Section`.

- [ ] **Step 3: Correct the narrative SAP**

Apply these exact changes:

```text
Section 7:
- Label the pooled exposure “denominator-weighted 2022-2024 annual EHR-diagnosed proportion among observed CAPriCORN adults.”
- State that annual observed-adult records may include the same adult in multiple years and do not estimate unique-person 3-year prevalence.
- Define capture_2022_2024 = sum(eligible annual EHR adult denominators) / sum(matched annual ACS adult-population denominators).
- Require an S4 EHR-year-to-ACS mapping table with release, 60-month period, universe, vintage, and rationale.

Section 12:
- Replace the generic score table with the eight fixed scoring rules already present in the approved scientific-analysis plan.
- Add independent blinded scoring, anchor-based reconciliation, retained original/reconciled scores, bundle rules, portfolio threshold, and tie-breakers.

Section 14:
- State “OLS remains the principal estimator.”
- Retain the Moran threshold and mandatory spatial-error sensitivity.
- Remove promotion of spatial error based on sign or >20% coefficient change.
- Label >20% or sign-change discrepancies “model-sensitive” and display both estimates equally.

Sections 18-20:
- Keep existing missingness thresholds.
- Define population-weighted sensitivity weights as aligned ACS adult population.
- Add the life-expectancy uncertainty rule and precision-weighted sensitivity.
```

- [ ] **Step 4: Update the JSON content**

Set:

```json
"metadata": {
  "version": "0.3-draft",
  "status": "DO NOT ANALYZE — Gates S4, S5, and S6 not passed"
}
```

Add `Biostat Handoff` as the first annex. Replace abbreviated scientific rows with exact narrative rules. Every critical annex must include `Narrative SAP Section` or `Decision Reference`.

Replace `Case Selection` columns with:

```json
["Domain", "Maximum Points", "Fixed Scoring Rule", "Hard Gate", "Required Evidence", "Narrative SAP Section", "Status"]
```

Use all fixed score anchors verbatim. Update every confirmatory row from `95% CI` to `97.5% CI`; retain 95% only where explicitly labeled `nominal estimation context` or `secondary`.

- [ ] **Step 5: Verify GREEN**

Run the Step 2 command again. Expected: `SAP hardening contract PASSED`.

- [ ] **Step 6: Commit the consistent scientific sources**

```bash
git add scripts/qa/validate_sap_hardening.mjs \
  docs/analysis/statistical_analysis_plan.md \
  docs/analysis/sap_workbook_spec.json
git diff --cached --check
git commit -m "docs: harden SAP scientific decision rules"
```

---

### Task 2: Add reusable workbook usability controls

**Files:**
- Modify: `skills/create-statistical-analysis-plan/scripts/build_sap.mjs`
- Modify: `skills/create-statistical-analysis-plan/scripts/validate_sap.mjs`
- Modify: `skills/create-statistical-analysis-plan/SKILL.md`
- Modify: `skills/create-statistical-analysis-plan/references/spec-schema.md`
- Modify: `skills/create-statistical-analysis-plan/references/scientific-rigor.md`
- Modify: `skills/create-statistical-analysis-plan/references/example_spec.json`
- Modify: `skills/create-statistical-analysis-plan/assets/SAP_Analysis_Plan_Template.xlsx`

**Interfaces:**
- Consumes: optional `validation.statusValues` and annex columns containing `Status`.
- Produces: filterable operational tables, validated status cells, accessible reactive colors, and a passing generic template.

- [ ] **Step 1: Extend the example specification before changing the builder**

Add:

```json
"validation": {
  "requiredAnnexes": ["Protocol", "Estimands", "Measure Semantics", "Analysis Methods", "Sensitivity Analyses", "Reporting Checklist", "Decision Log", "Deviation Log", "Freeze Gates"],
  "statusValues": ["Fixed", "Required", "Open", "Pending", "NOT PASSED", "Not applicable"]
}
```

Build the template with the current builder and inspect it. Expected RED: `Overview` and `Master Variables` have zero Excel tables, and status cells have no list validation.

- [ ] **Step 2: Add tables and filter buttons to non-sectioned operational ranges**

Add to `build_sap.mjs`:

```js
function addOperationalTable(sheet, range, name) {
  const table = sheet.tables.add(range, true, name);
  table.showHeaders = true;
  table.showFilterButton = true;
  return table;
}
```

After styling `Overview` and `Master Variables`, call:

```js
addOperationalTable(s, `A1:H${Math.max(2, (spec.overview ?? []).length + 1)}`, 'SapOverview');
addOperationalTable(
  s,
  `A3:${colLetter(variableColumns.length)}${Math.max(4, (spec.variables ?? []).length + 3)}`,
  'SapMasterVariables',
);
```

Do not table-wrap `Outputs`, because merged section bands intentionally reproduce the reference workbook.
Create each table before the final header/body formatting pass so the explicit reference colors and borders remain authoritative over the table's default style.

- [ ] **Step 3: Add status validation and conditional formatting**

Add and call this helper for every annex column matching `/status/i`:

```js
function addStatusControls(sheet, columnIndex, startRow, endRow, statusValues) {
  if (endRow < startRow) return;
  const letter = colLetter(columnIndex + 1);
  const range = sheet.getRange(`${letter}${startRow}:${letter}${endRow}`);
  range.dataValidation = { rule: { type: 'list', values: statusValues } };
  range.conditionalFormats.add('containsText', {
    text: 'NOT PASSED',
    format: { fill: '#F4CCCC', font: { bold: true, color: '#9C0006' } },
  });
  range.conditionalFormats.add('containsText', {
    text: 'Pending',
    format: { fill: '#FFF2CC', font: { color: '#7F6000' } },
  });
  range.conditionalFormats.add('containsText', {
    text: 'PENDING',
    format: { fill: '#FFF2CC', font: { color: '#7F6000' } },
  });
  range.conditionalFormats.add('containsText', {
    text: 'Fixed',
    format: { fill: '#E2F0D9', font: { color: '#375623' } },
  });
}
```

Default allowed values: `['Fixed', 'Required', 'Open', 'Pending', 'NOT PASSED', 'Not applicable']`.

- [ ] **Step 4: Extend generic validation**

Add to `validate_sap.mjs`:

```js
for (const sheetName of ['Overview', 'Master Variables']) {
  const sheet = wb.worksheets.getItem(sheetName);
  if (!sheet || sheet.tables.items.length < 1) failures.push(`missing filterable table on ${sheetName}`);
}
```

Retain all existing sheet-order, header, required-annex, unique-name, and formula-error checks.

- [ ] **Step 5: Update documentation and rebuild the generic template**

Document `validation.statusValues`, the `Outputs` filter exception, permanent principal-model rules, and the rule that compact workbooks cannot contradict narrative protocols.

```bash
node skills/create-statistical-analysis-plan/scripts/build_sap.mjs \
  --spec skills/create-statistical-analysis-plan/references/example_spec.json \
  --output skills/create-statistical-analysis-plan/assets/SAP_Analysis_Plan_Template.xlsx
node skills/create-statistical-analysis-plan/scripts/validate_sap.mjs \
  --workbook skills/create-statistical-analysis-plan/assets/SAP_Analysis_Plan_Template.xlsx \
  --spec skills/create-statistical-analysis-plan/references/example_spec.json
```

Expected: `SAP validation PASSED`; no `.inspect.ndjson` asset is staged.

- [ ] **Step 6: Commit the reusable skill improvement**

```bash
git add skills/create-statistical-analysis-plan
git diff --cached --check
git commit -m "feat: add SAP workbook handoff controls"
```

---

### Task 3: Regenerate the hardened ChicagoHealthMap workbook

**Files:**
- Modify: `outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx`
- Test: `skills/create-statistical-analysis-plan/scripts/validate_sap.mjs`
- Test: `scripts/qa/validate_sap_hardening.mjs`

**Interfaces:**
- Consumes: corrected narrative, JSON specification, and generic builder.
- Produces: a 19-sheet workbook beginning `Overview`, `Outputs`, `Master Variables`, `Biostat Handoff`.

- [ ] **Step 1: Regenerate from JSON**

```bash
node skills/create-statistical-analysis-plan/scripts/build_sap.mjs \
  --spec docs/analysis/sap_workbook_spec.json \
  --output outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx
```

Expected: `Built ...ChicagoHealthMap_Draft_SAP.xlsx with 19 sheets`.

- [ ] **Step 2: Run both validators**

```bash
node skills/create-statistical-analysis-plan/scripts/validate_sap.mjs \
  --workbook outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx \
  --spec docs/analysis/sap_workbook_spec.json
node scripts/qa/validate_sap_hardening.mjs \
  --spec docs/analysis/sap_workbook_spec.json \
  --narrative docs/analysis/statistical_analysis_plan.md \
  --workbook outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx
```

Expected: both print `PASSED` and exit `0`.

- [ ] **Step 3: Inspect high-risk ranges**

Use artifact-tool `inspect` on:

```text
Biostat Handoff!A1:F30
Estimands!A1:H15
Case Selection!A1:G30
Analysis Methods!A1:F20
Multiplicity!A1:F15
Freeze Gates!A1:F15
```

Verify 97.5% CI language, permanent OLS primacy, fixed anchors, pooled-measure/capture formulas, blockers, section references, and no error tokens.

- [ ] **Step 4: Commit the generated workbook**

```bash
git add outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx
git diff --cached --check
git commit -m "docs: regenerate hardened ChicagoHealthMap SAP workbook"
```

---

### Task 4: Render every sheet and run the final adversarial acceptance audit

**Files:**
- Verify: `outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx`
- Verify: `docs/analysis/statistical_analysis_plan.md`
- Verify: `docs/analysis/sap_workbook_spec.json`
- Verify: `skills/create-statistical-analysis-plan/assets/SAP_Analysis_Plan_Template.xlsx`

**Interfaces:**
- Consumes: finished workbook and sources.
- Produces: evidence that every design acceptance criterion passes and the repository is clean.

- [ ] **Step 1: Render all 19 sheets**

Import the workbook and render each worksheet with:

```js
await wb.render({ sheetName: sheet.name, autoCrop: 'all', scale: 1, format: 'png' });
```

Save previews only under `/tmp/chicagohealthmap_sap_hardening/`.

- [ ] **Step 2: Perform the visual pass**

Inspect every preview for clipped headers, unreadable text, excess used ranges, missing section bands, inaccessible status colors, missing filters, and blank/default sheets. Correct sources or builder, regenerate, and rerun both validators after any correction.

- [ ] **Step 3: Repeat the adversarial review**

Search narrative, JSON, and workbook for:

```text
95% CI
97.5% CI
becomes the principal
OLS remains principal
model-sensitive
PENDING
NOT PASSED
Fixed Scoring Rule
annual observed-adult records
matched annual ACS adult-population denominators
```

Require no high- or medium-severity contradiction or discretionary primary-analysis branch. Remaining `PENDING`/`NOT PASSED` items must correspond only to S4-S7 evidence gates.

- [ ] **Step 4: Run final verification**

```bash
node skills/create-statistical-analysis-plan/scripts/validate_sap.mjs \
  --workbook outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx \
  --spec docs/analysis/sap_workbook_spec.json
node scripts/qa/validate_sap_hardening.mjs \
  --spec docs/analysis/sap_workbook_spec.json \
  --narrative docs/analysis/statistical_analysis_plan.md \
  --workbook outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx
git diff --check
git status --short
```

Expected: both validators pass; `git diff --check` and final `git status --short` print nothing.

- [ ] **Step 5: Record the handoff**

Report final commits, 19-sheet count, validator and visual-review results, remaining scientific gates, and one standalone link to the final `.xlsx`. Do not claim S4-S7 passed.
