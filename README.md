# Stock Mates RAG + LangGraph Demo

**Once-off public demonstration** for interview purposes.

This is a simplified, self-contained illustration of the core RAG pipeline and bounded LangGraph orchestration used in [Stock Mates](https://github.com/junchenw/stock-mates) — a local-first, evidence-backed stock-research application.

**It is informational research software only. It is not financial advice, and it does not execute trades or provide buy/sell/hold recommendations.**

## What this demo shows

- How grounded company research is produced from deterministic evidence (SEC filings, etc.).
- A bounded LangGraph that orchestrates the stages: prepare → plan topics → retrieve → build evidence pool → plan sections → write (with at most one repair) → compose → publish.
- Fail-closed evidence integrity: claims must be supported by retained source evidence; missing facts are disclosed rather than invented.
- Local-first principles: retrieval, storage, and replay are local; only the LLM stages call a cloud model.
- Checkpointing and recovery concepts (simplified).

This is **not** the full product. The full Stock Mates system includes SEC corpus admission, lexical + dense indexes (FTS5 + LanceDB), company identity, receipt persistence, Library Q&A, evaluation harnesses, and a FastAPI/React workbench. Those live in the private development repository.

## Architecture overview (simplified)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Request    │────▶│  LangGraph   │────▶│  Grounded       │
│  (ticker +  │     │  (bounded)   │     │  Report +       │
│  cutoff)    │     │              │     │  Citations      │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
           ┌──────────────┬───────────────┐
           ▼               ▼               ▼
    Prepare evidence   Retrieve        Write & validate
    (identity,         (lexical +      (planner → writer,
     filings)          dense hybrid)   numeric/citation
                                        checks, one repair)
```

**LangGraph nodes** (mirroring the production graph in `report_langgraph.py`):

1. `prepare` — load company identity and available filings
2. `plan_topics` — LLM planner proposes research topics
3. `retrieve` — hybrid retrieval over lexical + dense indexes
4. `build_pool` — construct the evidence pool with provenance
5. `prepare_writer` / `plan_sections` — section plan
6. `write` — generate sections; conditional edge allows one repair on validation failure
7. `compose` — assemble receipt with citations and limitations
8. `publish` — persist the immutable receipt

The graph owns stage progression and the single repair decision. Domain logic stays in shared stages; the graph does not invent a second research runtime.

## Quick start (demo script)

Requires Python 3.11+ and the packages in `requirements.txt`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python demo_rag_langgraph.py
```

The script uses synthetic evidence (no real SEC downloads, no API keys required for the mocked path). It prints the graph execution, retrieved evidence, and a grounded report with citations.

To exercise the real OpenAI path (optional), set `OPENAI_API_KEY` and change the mock flag.

## Key design decisions visible in the demo

- **Evidence first**: retrieval and pool construction happen before any generation. The writer only sees admitted evidence.
- **Fail-closed**: if validation fails (unsupported numbers, missing citations, etc.), the graph repairs once or refuses. No silent fallback to ungrounded prose.
- **Immutable receipts**: outputs carry source digests and can be reopened without re-generation or re-retrieval.
- **Local vs cloud boundary**: indexes, SQLite, and receipts are local. Only planner/writer/embeddings call the model.
- **Bounded orchestration**: LangGraph is a thin adapter over existing stages, not an open-ended agent.

## Mapping to the full Stock Mates system

| Demo concept                  | Full system location                          |
|-------------------------------|-----------------------------------------------|
| LangGraph report driver       | `src/stock_mates/research/report_langgraph.py` |
| Shared stages / pool-direct   | `report_planner_led_runtime.py`, `report_preparation.py` |
| Lexical retrieval             | FTS5 + BM25 / RRF in `retrieval/` and `research/` |
| Dense retrieval               | LanceDB + embeddings in `retrieval/lancedb_*` |
| Evidence pool & citations     | `report_library_evidence.py`, receipt contracts |
| Admission & checkpointing     | `report_admission.py`, run checkpoints        |

See the private repository's `docs/architecture/current-module-map.md` and `docs/architecture/target-architecture.md` for the authoritative map.

## Licence

MIT. This demo is provided for educational and interview purposes only.

---

*Derived from the Stock Mates architecture. Full product remains private and under active development.*
