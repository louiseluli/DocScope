# DocScope Copilot

**Short description**

DocScope Copilot is an AI documentation assistant that:

- Aggregates key AI documentation frameworks and empirical studies,
- Lets users ask questions about documentation best practices,
- Audits model/system/dataset documentation snippets against governance-relevant categories (Safety, Data, Governance, Equity, etc.).

It is meant as a **governance tool**, not a new framework. It shows:

- Where existing documentation is strong or weak,
- How frameworks complement or contradict each other,
- How policymakers could require machine-readable docs and use tools like this to support audits and procurement.

## High-level components

- `data/` – corpus of frameworks, studies, and real-world documentation artifacts.
- `src/ingest/` – pipelines to extract and normalise text from PDFs / HTML.
- `src/indexing/` – embeddings + vector index for retrieval.
- `src/models/` – category classifier (Safety, Data, Governance, etc.).
- `src/audit/` – document auditing logic.
- `src/chatbot/` – chatbot core (CLI/web) using retrieval + auditing.
- `notebooks/` – analysis & evaluation (metrics, figures for memo/slides).
- `docs/` – policy memo draft, slides outline, design notes.

## Quickstart (dev)

```bash
git clone <your-repo-url>
cd docscope-copilot
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
