import json
from pathlib import Path
from typing import List, Dict

from tqdm import tqdm

from src.config.settings import DATA_DIR, PROCESSED_DIR
from src.ingest.load_metadata import load_metadata
from src.ingest.pdf_extractor import build_pdf_chunks
from src.ingest.html_extractor import build_text_chunks


def build_corpus(priority_max: int = 3) -> None:
    """
    Build the corpus of text chunks from all documents listed in
    frameworks_metadata.csv with priority <= priority_max.

    Outputs:
    - data/processed/chunks.jsonl
    - data/processed/doc_metadata.json
    """
    metadata_df = load_metadata(priority_max=priority_max)

    all_chunks: List[Dict] = []
    doc_metadata: Dict[str, Dict] = {}

    base_data_dir: Path = DATA_DIR  # points to data/

    for _, row in tqdm(
        metadata_df.iterrows(),
        total=len(metadata_df),
        desc="Building corpus"
    ):
        row_dict = row.to_dict()
        doc_id = row_dict["doc_id"]
        rel_path: str = row_dict["rel_path"]
        ext = Path(rel_path).suffix.lower()

        # Save doc-level metadata
        doc_metadata[doc_id] = {
            "doc_id": doc_id,
            "title": row_dict["title"],
            "year": int(row_dict["year"]),
            "doc_type": row_dict["doc_type"],
            "eval_type": row_dict["eval_type"],
            "rel_path": rel_path,
            "priority": int(row_dict["priority"]),
        }

        try:
            # Choose extractor based on extension
            if ext == ".pdf":
                chunks = build_pdf_chunks(row_dict, base_data_dir)
            elif ext in [".md", ".txt", ".html"]:
                chunks = build_text_chunks(row_dict, base_data_dir)
            else:
                print(f"[WARN] Unsupported extension {ext} for {rel_path}. Skipping.")
                continue
        except Exception as e:
            print(f"[ERROR] Failed to process {doc_id} ({rel_path}): {e}")
            continue

        if not chunks:
            print(f"[INFO] No text extracted for {doc_id} ({rel_path}).")
        all_chunks.extend(chunks)

    # Ensure processed dir exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    chunks_path = PROCESSED_DIR / "chunks.jsonl"
    with chunks_path.open("w", encoding="utf-8") as f:
        for ch in all_chunks:
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")

    doc_meta_path = PROCESSED_DIR / "doc_metadata.json"
    with doc_meta_path.open("w", encoding="utf-8") as f:
        json.dump(doc_metadata, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_chunks)} chunks to {chunks_path}")
    print(f"Saved metadata for {len(doc_metadata)} docs to {doc_meta_path}")


if __name__ == "__main__":
    build_corpus(priority_max=3)
