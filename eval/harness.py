"""Evaluation harness for Task 1 (triage) and Task 2 (account brief).

Each test case is scored by rule-based checks (schema validity, enum
membership, expected-value matching, quote grounding) and — when GROQ_API_KEY
is set — an LLM-as-judge pass for qualitative quality. A case's quality_score
is the rule pass rate; if the judge ran, it's averaged in. Run:

    python -m eval.harness
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.account_brief import AccountNotFoundError, account_health_brief
from app.config import GROQ_API_KEY
from app.schemas import TicketInput
from app.triage import triage_ticket
from eval import judge

ROOT = Path(__file__).resolve().parent.parent
JUDGE_ENABLED = bool(GROQ_API_KEY)

# Quality gate — main() exits 1 below these, so CI actually fails on a real
# regression instead of just "the script didn't crash." Real baseline is
# 8/10 passed, 0.916 avg quality; thresholds sit below that with margin so
# the gate isn't brittle to the 2 known judgment-call non-passes.
EVAL_MIN_PASSED = int(os.environ.get("EVAL_MIN_PASSED", "6"))
EVAL_MIN_AVG_QUALITY = float(os.environ.get("EVAL_MIN_AVG_QUALITY", "0.6"))


def _score(checks: dict[str, bool]) -> float:
    if not checks:
        return 1.0
    return sum(1 for v in checks.values() if v) / len(checks)


def run_triage_case(case: dict) -> dict:
    acc = case["acceptance"]
    checks: dict[str, bool] = {}
    notes = []
    try:
        ticket = TicketInput(**case["input"])
        result = triage_ticket(ticket)
        rd = result.model_dump()

        if acc.get("expect_valid_schema_only"):
            checks["valid_schema"] = True  # pydantic already validated on construction
        if "expected_urgency" in acc:
            checks["urgency_match"] = rd["urgency"] == acc["expected_urgency"]
        if "expected_urgency_any" in acc:
            checks["urgency_in_range"] = rd["urgency"] in acc["expected_urgency_any"]
        if "expected_category_any" in acc:
            checks["category_plausible"] = rd["issue_category"] in acc["expected_category_any"]
        if acc.get("requires_kb_match"):
            checks["kb_match_present"] = rd["kb_match"] is not None
        if "expected_kb_doc_contains" in acc:
            doc = (rd["kb_match"] or {}).get("doc_path", "") if rd["kb_match"] else ""
            checks["kb_doc_correct"] = acc["expected_kb_doc_contains"] in doc
        if acc.get("expect_low_confidence"):
            checks["low_confidence_as_expected"] = rd["confidence"] <= acc.get("max_confidence", 0.6)
        checks["response_nonempty"] = bool(rd["draft_first_response"].strip())

        rule_score = _score(checks)
        judge_result = None
        if JUDGE_ENABLED:
            judge_result = judge.judge_triage(case["input"], rd)
            quality_score = (rule_score + judge_result["score"]) / 2
        else:
            quality_score = rule_score
            notes.append("LLM-as-judge skipped: GROQ_API_KEY not set")

        return {
            "case_id": case["case_id"],
            "passed": rule_score == 1.0 and (judge_result is None or judge_result["pass"]),
            "quality_score": round(quality_score, 3),
            "rule_checks": checks,
            "judge": judge_result,
            "notes": notes,
            "output": rd,
        }
    except Exception as e:
        return {
            "case_id": case["case_id"],
            "passed": False,
            "quality_score": 0.0,
            "rule_checks": checks,
            "judge": None,
            "notes": [f"EXCEPTION: {type(e).__name__}: {e}"],
            "output": None,
        }


def run_account_case(case: dict) -> dict:
    acc = case["acceptance"]
    checks: dict[str, bool] = {}
    notes = []
    try:
        if acc.get("expect_not_found_error"):
            try:
                account_health_brief(case["account_id"])
                checks["raised_not_found"] = False
            except AccountNotFoundError:
                checks["raised_not_found"] = True
            return {
                "case_id": case["case_id"],
                "passed": checks["raised_not_found"],
                "quality_score": _score(checks),
                "rule_checks": checks,
                "judge": None,
                "notes": notes,
                "output": None,
            }

        result = account_health_brief(case["account_id"])
        rd = result.model_dump()

        if "min_open_risks" in acc:
            checks["min_open_risks_met"] = len(rd["open_risks"]) >= acc["min_open_risks"]
        if acc.get("require_grounded_quotes"):
            # grounding already enforced in app/account_brief.py; verify nothing slipped through empty
            checks["risks_have_quotes"] = all(r["evidence_quote"].strip() for r in rd["open_risks"])
        if acc.get("expect_sparse_data_acknowledged") and rd["tickets_analyzed"] == 0:
            summary_lower = rd["executive_summary"].lower()
            checks["sparse_data_acknowledged"] = any(
                kw in summary_lower for kw in ["no recent", "no ticket", "sparse", "limited data", "no data", "zero ticket"]
            )
        checks["summary_nonempty"] = bool(rd["executive_summary"].strip())

        rule_score = _score(checks)
        judge_result = None
        if JUDGE_ENABLED:
            judge_result = judge.judge_account_brief(case["account_id"], rd)
            quality_score = (rule_score + judge_result["score"]) / 2
        else:
            quality_score = rule_score
            notes.append("LLM-as-judge skipped: GROQ_API_KEY not set")

        return {
            "case_id": case["case_id"],
            "passed": rule_score == 1.0 and (judge_result is None or judge_result["pass"]),
            "quality_score": round(quality_score, 3),
            "rule_checks": checks,
            "judge": judge_result,
            "notes": notes,
            "output": rd,
        }
    except Exception as e:
        return {
            "case_id": case["case_id"],
            "passed": False,
            "quality_score": 0.0,
            "rule_checks": checks,
            "judge": None,
            "notes": [f"EXCEPTION: {type(e).__name__}: {e}"],
            "output": None,
        }


def run_determinism_check() -> dict:
    """Task 2 explicitly requires deterministic output for the same input."""
    if not JUDGE_ENABLED:
        return {"skipped": True, "reason": "GROQ_API_KEY not set"}
    r1 = account_health_brief("ACC-1785").model_dump()
    r2 = account_health_brief("ACC-1785").model_dump()
    r1.pop("model", None)
    r2.pop("model", None)
    return {"skipped": False, "identical": r1 == r2}


def main():
    triage_cases = json.loads((ROOT / "eval" / "cases_triage.json").read_text(encoding="utf-8"))
    account_cases = json.loads((ROOT / "eval" / "cases_account_brief.json").read_text(encoding="utf-8"))

    triage_results = [run_triage_case(c) for c in triage_cases]
    account_results = [run_account_case(c) for c in account_cases]
    determinism = run_determinism_check()

    all_results = triage_results + account_results
    n_passed = sum(1 for r in all_results if r["passed"])
    avg_quality = round(sum(r["quality_score"] for r in all_results) / len(all_results), 3)
    gate_passed = n_passed >= EVAL_MIN_PASSED and avg_quality >= EVAL_MIN_AVG_QUALITY

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "judge_enabled": JUDGE_ENABLED,
        "summary": {
            "total_cases": len(all_results),
            "passed": n_passed,
            "failed": len(all_results) - n_passed,
            "avg_quality_score": avg_quality,
            "gate_passed": gate_passed,
            "gate_thresholds": {"min_passed": EVAL_MIN_PASSED, "min_avg_quality": EVAL_MIN_AVG_QUALITY},
        },
        "determinism_check_task2": determinism,
        "task1_triage_results": triage_results,
        "task2_account_brief_results": account_results,
    }

    (ROOT / "eval_report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    _write_markdown(report)
    print(f"Passed {n_passed}/{len(all_results)} cases. Avg quality {avg_quality}. "
          f"Report written to eval_report.json / eval_report.md")

    if not gate_passed:
        print(
            f"QUALITY GATE FAILED: need >= {EVAL_MIN_PASSED} passed and "
            f">= {EVAL_MIN_AVG_QUALITY} avg quality (got {n_passed} passed, {avg_quality} avg)."
        )
        if not JUDGE_ENABLED:
            print("GROQ_API_KEY is not set for this run — that's almost certainly why every "
                  "LLM-backed case failed. Set it as a repo secret for CI to run for real.")
        sys.exit(1)


def _write_markdown(report: dict):
    lines = [
        "# Eval Report",
        "",
        f"Generated: {report['generated_at']}",
        f"LLM-as-judge enabled: {report['judge_enabled']}",
        "",
        f"**{report['summary']['passed']}/{report['summary']['total_cases']} cases passed** "
        f"(avg quality score: {report['summary']['avg_quality_score']})",
        "",
        f"Quality gate: {'PASSED' if report['summary']['gate_passed'] else 'FAILED'} "
        f"(requires >= {report['summary']['gate_thresholds']['min_passed']} passed and "
        f">= {report['summary']['gate_thresholds']['min_avg_quality']} avg quality)",
        "",
        f"Determinism check (Task 2, same input twice): "
        f"{'SKIPPED (no API key)' if report['determinism_check_task2'].get('skipped') else report['determinism_check_task2'].get('identical')}",
        "",
        "| Case | Task | Passed | Quality | Notes |",
        "|---|---|---|---|---|",
    ]
    for r in report["task1_triage_results"]:
        lines.append(f"| {r['case_id']} | triage | {r['passed']} | {r['quality_score']} | {'; '.join(r['notes'])} |")
    for r in report["task2_account_brief_results"]:
        lines.append(f"| {r['case_id']} | account_brief | {r['passed']} | {r['quality_score']} | {'; '.join(r['notes'])} |")
    (ROOT / "eval_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
