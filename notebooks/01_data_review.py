import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo

    from chicagohealthmap.quality.views import (
        findings_view,
        gate_3_decision,
        guard_review_paths,
        load_quality_checkpoint,
        review_sections_view,
        schema_evidence_view,
        write_gate_3_decision,
    )

    return (
        Path,
        findings_view,
        gate_3_decision,
        guard_review_paths,
        load_quality_checkpoint,
        mo,
        review_sections_view,
        schema_evidence_view,
        write_gate_3_decision,
    )


@app.cell
def _(Path, mo):
    project_root = Path(__file__).resolve().parents[1]
    default_report_path = project_root / "outputs" / "quality" / "ehr_quality.json"
    default_decision_path = project_root / "outputs" / "quality" / "gate_3_decision.json"
    script_mode = mo.app_meta().mode == "script"
    command_arguments = mo.cli_args() if script_mode else {}
    report_argument = command_arguments.get(
        "report-path", command_arguments.get("report_path", str(default_report_path))
    )
    decision_argument = command_arguments.get(
        "decision-path", command_arguments.get("decision_path", str(default_decision_path))
    )
    return (
        decision_argument,
        default_decision_path,
        default_report_path,
        project_root,
        report_argument,
    )


@app.cell
def _(default_decision_path, default_report_path, mo):
    report_path_input = mo.ui.text(
        value=str(default_report_path),
        label="Frozen disclosure-safe quality checkpoint",
        full_width=True,
    )
    decision_path_input = mo.ui.text(
        value=str(default_decision_path),
        label="Machine-readable Gate 3 decision",
        full_width=True,
    )
    mo.vstack([report_path_input, decision_path_input])
    return decision_path_input, report_path_input


@app.cell
def _(
    Path,
    decision_argument,
    decision_path_input,
    guard_review_paths,
    mo,
    project_root,
    report_argument,
    report_path_input,
):
    active_report_path = Path(
        report_argument if mo.app_meta().mode == "script" else report_path_input.value
    ).expanduser()
    active_decision_path = Path(
        decision_argument if mo.app_meta().mode == "script" else decision_path_input.value
    ).expanduser()
    guard_review_paths(active_report_path, active_decision_path, project_root)
    return active_decision_path, active_report_path


@app.cell
def _(active_report_path, load_quality_checkpoint):
    checkpoint = load_quality_checkpoint(active_report_path)
    return (checkpoint,)


@app.cell
def _(mo):
    mo.md(r"""
    # Chicago Health Map EHR data review

    This notebook presents a frozen, disclosure-safe schema-evidence checkpoint.
    It does **not** read raw exports, infer field meanings, clean data, publish
    analysis-ready data, or run a model. Measure names, denominators, suppression,
    reliability, representation, and age-adjustment semantics remain unverified.
    """)
    return


@app.cell
def _(checkpoint, schema_evidence_view):
    evidence_table = schema_evidence_view(checkpoint)
    return (evidence_table,)


@app.cell
def _(evidence_table, mo):
    mo.vstack(
        [
            mo.md("## Source inventory and schema/field evidence"),
            mo.ui.table(evidence_table, selection=None, pagination=False),
        ]
    )
    return


@app.cell
def _(checkpoint, review_sections_view):
    review_table = review_sections_view(checkpoint)
    return (review_table,)


@app.cell
def _(mo, review_table):
    mo.vstack(
        [
            mo.md(
                """
                ## Planned quality review domains

                A status of **not evaluated** is not negative evidence. These reviews
                require owner-verified semantic fields, which are not yet available.
                """
            ),
            mo.ui.table(review_table, selection=None, pagination=False),
        ]
    )
    return


@app.cell
def _(checkpoint, findings_view):
    blocker_table = findings_view(checkpoint)
    return (blocker_table,)


@app.cell
def _(blocker_table, mo):
    mo.vstack(
        [
            mo.md("## Unresolved discrepancies and blockers"),
            mo.ui.table(blocker_table, selection=None, pagination=False),
        ]
    )
    return


@app.cell
def _(checkpoint, gate_3_decision):
    decision = gate_3_decision(checkpoint)
    return (decision,)


@app.cell
def _(active_decision_path, decision, write_gate_3_decision):
    write_gate_3_decision(active_decision_path, decision)
    return


@app.cell
def _(active_decision_path, decision, mo):
    mo.vstack(
        [
            mo.md(
                f"""
                ## Gate 3 decision: CLOSED

                Source rows read: **{decision["source_rows_read"]}**. Verified field
                positions: **{decision["schema_evidence"]["verified_positions"]}**.
                Analysis-usable tables: **{decision["schema_evidence"]["analysis_usable_tables"]}**.

                Blocked: disease candidate scoring, analysis-ready EHR publication,
                and confirmatory modeling.

                Decision artifact: `{active_decision_path}`
                """
            ),
            mo.json(decision),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
