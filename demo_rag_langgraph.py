#!/usr/bin/env python3
"""
Simplified Stock Mates RAG + LangGraph demo.

Illustrates the bounded orchestration of evidence preparation, hybrid retrieval,
pool building, section planning, writing with one repair, and receipt composition.

Uses synthetic evidence and a mocked LLM so the demo runs with zero network
and zero API keys. The structure mirrors production report_langgraph.py.
"""

from __future__ import annotations

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ---------------------------------------------------------------------------
# Synthetic evidence (stand-in for admitted SEC filings + dense/lexical indexes)
# ---------------------------------------------------------------------------

SYNTHETIC_FILINGS = {
    "AAPL": [
        {
            "id": "10-K-2024",
            "type": "10-K",
            "period": "FY2024",
            "excerpt": (
                "Net sales for fiscal 2024 were $391.0 billion, an increase of 2% "
                "compared to $383.3 billion in 2023. Net income was $93.7 billion. "
                "Services net sales were $96.2 billion."
            ),
        },
        {
            "id": "10-Q-Q1-2025",
            "type": "10-Q",
            "period": "Q1 FY2025",
            "excerpt": (
                "Net sales for the first quarter of 2025 were $124.3 billion. "
                "iPhone net sales were $69.1 billion. Services grew 14% year-over-year."
            ),
        },
    ]
}


# ---------------------------------------------------------------------------
# LangGraph state (compact, primitive — mirrors production checkpoint contract)
# ---------------------------------------------------------------------------

class ReportState(TypedDict):
    ticker: str
    topics: list[str]
    evidence: list[dict]
    pool: str
    sections: list[str]
    draft: str
    writer_attempts: int
    writer_error: str | None
    receipt: dict


# ---------------------------------------------------------------------------
# Stage functions (shared domain logic; graph only sequences them)
# ---------------------------------------------------------------------------

def prepare(state: ReportState) -> dict:
    print("→ prepare: loading identity and available filings")
    filings = SYNTHETIC_FILINGS.get(state["ticker"], [])
    return {"evidence": filings}


def plan_topics(state: ReportState) -> dict:
    print("→ plan_topics: proposing research topics from request")
    topics = ["Revenue and growth", "Services segment", "Quarterly performance"]
    return {"topics": topics}


def retrieve(state: ReportState) -> dict:
    print("→ retrieve: hybrid lexical + dense retrieval over admitted filings")
    return {"evidence": state["evidence"]}


def build_pool(state: ReportState) -> dict:
    print("→ build_pool: constructing evidence pool with provenance")
    lines = []
    for item in state["evidence"]:
        lines.append(
            f"[{item['id']} | {item['type']} | {item['period']}]\n{item['excerpt']}"
        )
    pool = "\n\n".join(lines)
    return {"pool": pool}


def plan_sections(state: ReportState) -> dict:
    print("→ plan_sections: producing section plan")
    sections = ["Overview", "Revenue", "Services", "Limitations"]
    return {"sections": sections}


def write(state: ReportState) -> dict:
    attempts = state.get("writer_attempts", 0) + 1
    print(f"→ write: attempt {attempts}")

    if attempts == 1:
        draft = (
            "Overview: Apple reported strong results.\n"
            "Revenue: Net sales reached $400 billion in FY2024. "
            f"(source: {state['evidence'][0]['id']})\n"
            "Services: Services grew substantially.\n"
            "Limitations: Some figures are approximate."
        )
        error = "unsupported_numeric_claim"
    else:
        draft = (
            "Overview: Apple reported results for FY2024 and Q1 FY2025.\n"
            "Revenue: Net sales for fiscal 2024 were $391.0 billion "
            f"(source: {state['evidence'][0]['id']}). "
            f"Q1 FY2025 net sales were $124.3 billion "
            f"(source: {state['evidence'][1]['id']}).\n"
            "Services: Services net sales were $96.2 billion in FY2024 "
            f"(source: {state['evidence'][0]['id']}).\n"
            "Limitations: This is a demonstration using synthetic excerpts only. "
            "No claim is made about investment merit."
        )
        error = None

    return {
        "draft": draft,
        "writer_attempts": attempts,
        "writer_error": error,
    }


def after_write(state: ReportState) -> str:
    """Single bounded repair decision — mirrors production _after_write."""
    if state["writer_error"] is None:
        return "compose"
    if state["writer_attempts"] < 2:
        print("  ↳ validation failed; repairing once")
        return "write"
    print("  ↳ repair exhausted; refusing")
    return "refuse"


def compose(state: ReportState) -> dict:
    print("→ compose: sealing receipt with citations and limitations")
    receipt = {
        "ticker": state["ticker"],
        "sections": state["sections"],
        "text": state["draft"],
        "evidence_ids": [e["id"] for e in state["evidence"]],
        "writer_attempts": state["writer_attempts"],
        "limitations": ["Synthetic demo data only", "Not financial advice"],
    }
    return {"receipt": receipt}


def publish(state: ReportState) -> dict:
    print("→ publish: receipt ready")
    print("\n" + "=" * 60)
    print("GROUNDED REPORT (demo)")
    print("=" * 60)
    print(state["receipt"]["text"])
    print("\nEvidence used:", ", ".join(state["receipt"]["evidence_ids"]))
    print("Writer attempts:", state["receipt"]["writer_attempts"])
    print("Limitations:", "; ".join(state["receipt"]["limitations"]))
    return {}


def refuse(state: ReportState) -> dict:
    print("→ refuse: report not produced (fail-closed)")
    return {"receipt": {"error": "validation_failed_after_repair"}}


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_demo_graph():
    graph = StateGraph(ReportState)

    graph.add_node("prepare", prepare)
    graph.add_node("plan_topics", plan_topics)
    graph.add_node("retrieve", retrieve)
    graph.add_node("build_pool", build_pool)
    graph.add_node("plan_sections", plan_sections)
    graph.add_node("write", write)
    graph.add_node("compose", compose)
    graph.add_node("publish", publish)
    graph.add_node("refuse", refuse)

    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "plan_topics")
    graph.add_edge("plan_topics", "retrieve")
    graph.add_edge("retrieve", "build_pool")
    graph.add_edge("build_pool", "plan_sections")
    graph.add_edge("plan_sections", "write")
    graph.add_conditional_edges(
        "write",
        after_write,
        {"write": "write", "compose": "compose", "refuse": "refuse"},
    )
    graph.add_edge("compose", "publish")
    graph.add_edge("publish", END)
    graph.add_edge("refuse", END)

    return graph.compile()


def main():
    print("Stock Mates RAG + LangGraph Demo")
    print("Informational research demonstration only — not financial advice.\n")

    app = build_demo_graph()
    initial = {
        "ticker": "AAPL",
        "writer_attempts": 0,
        "writer_error": None,
    }
    app.invoke(initial)


if __name__ == "__main__":
    main()
