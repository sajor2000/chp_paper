---
name: write-jama-health-forum-manuscript
description: Use when a user requests JAMA paper writing, a JAMA manuscript, JAMA Health Forum Original Investigation support, or journal-style audit, draft, revise, statistical reporting, display, or submission-readiness work. It applies JAMA Health Forum rules only after the target journal and article type are established.
---

# Write JAMA Health Forum Manuscript

Produce evidence-bound, policy-relevant manuscripts whose claims, numbers, and journal conventions remain traceable. Treat style as the final layer over scientific validity.

## Establish scope

Confirm the target journal, article type, study design, requested task, and source artifacts before applying rules. When the user says only "JAMA," inspect the files and conversation for the intended journal; if it remains unknown, ask one focused question.

Do not apply JAMA Health Forum-specific requirements to another JAMA Network journal. For another journal or article type, verify its live instructions and state that this skill's detailed requirements are not controlling.

For JAMA Health Forum compliance or submission-readiness work, verify the [official instructions](https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors) during the current task. Record the access date and resolve differences in favor of the live instructions.

## Load references

1. Read [jama-requirements.md](references/jama-requirements.md) for every JAMA Health Forum task.
2. Read [writing-style.md](references/writing-style.md) when drafting or revising prose.
3. Read [audit-rubric.md](references/audit-rubric.md) when reviewing a manuscript, abstract, table, figure, or supplement.
4. Read [chicagohealthmap-profile.md](references/chicagohealthmap-profile.md) only for ChicagoHealthMap/CAPriCORN work. Treat it as a project profile, never as universal JAMA policy.

Use the host's PDF or document tools when supplied files require them. The bundled auditor accepts UTF-8 Markdown or plain text; its warnings are screening prompts, not editorial verdicts.

## Establish the evidence contract

Collect the protocol or SAP, frozen results, display shells, claim ledger, reporting guideline, and journal instructions. For each empirical claim, identify its source, denominator, unit, period, estimate, uncertainty, and analysis status.

Rank authority in this order: verified data and approved protocol; live journal requirements; project-specific contracts; exemplar patterns; stylistic preference. Exemplar prose demonstrates craft, not policy or scientific truth.

Do not invent a result, denominator, CI, citation, ethics determination, data-sharing position, or unresolved scientific choice. Use a labeled shell or blocker when evidence is unavailable.

## Choose the route

### Audit

Run:

```bash
python <skill>/scripts/audit_manuscript.py <manuscript.md-or.txt>
```

Then apply the full audit rubric. Report findings first, ordered by evidence failure, inference risk, cross-artifact inconsistency, journal noncompliance, and prose quality. Distinguish deterministic warnings from human judgments and cite exact locations.

### Draft

Draft in this order: displays and result ledger, Results, Methods, Discussion/Limitations/Conclusions, Introduction, structured abstract, Key Points, then title. Preserve the order of aims, methods, results, and displays. Keep unresolved fields visibly bracketed with an owner or evidence need; remove them before submission-ready delivery.

### Revise

Preserve scientific meaning while improving syntax, compression, cadence, and claim boundaries. Compare every changed number and interpretation with its source artifact. Do not use stylistic revision to strengthen causal or policy claims.

### Finalize

Recheck live limits, reporting guidelines, ethics language, disclosures, data sharing, AI-use disclosure, references, display citations, and supplement numbering. Verify title, abstract, Key Points, text, tables, figures, and supplement against the same frozen values. Never label a draft submission-ready while blockers remain.

## Nonnegotiable writing rules

- Use causal language only when the design supports it and current JAMA policy permits it.
- Report every primary outcome with an exact estimate and uncertainty in the abstract and text or table, not only in a figure.
- State the observational unit and number of observations.
- Keep Design, Setting, and Participants separate in the submitted abstract.
- Keep human authors accountable for every sentence, number, citation, and disclosure; document qualifying AI assistance under the current journal policy.
- Never generate or format references from memory; resolve them through verified source records.
- Treat automated readability, passive-voice, hedge, and stock-phrase flags as review prompts, not acceptance targets.

## Delivery contract

For an audit, lead with actionable findings and cite exact locations. For drafting or revision, provide the edited artifact, a concise change summary, unresolved evidence gaps, and verification performed. Separate `verified`, `author decision needed`, and `not checked`. Do not claim JAMA compliance without a same-task official-instructions check.
