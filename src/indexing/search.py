from pathlib import Path
from typing import List, Dict, Tuple
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src.config.settings import (
    MODELS_DIR,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DIM,
    TOP_K_RETRIEVAL,
)


class ChunkSearcher:
    def __init__(self):
        index_path = MODELS_DIR / "chunks_faiss.index"
        meta_path = MODELS_DIR / "chunks_metadata.jsonl"

        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found at {index_path}")
        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found at {meta_path}")

        self.index = faiss.read_index(str(index_path))
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)

        # Carregar metadados em lista
        self.metadata: List[Dict] = []
        with meta_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                self.metadata.append(json.loads(line))

        if len(self.metadata) != self.index.ntotal:
            print(
                f"[WARN] Metadata size ({len(self.metadata)}) "
                f"differs from index size ({self.index.ntotal})"
            )

    def _encode_query(self, query: str) -> np.ndarray:
        emb = self.model.encode([query], show_progress_bar=False)
        emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)
        return emb.astype("float32")

    def search(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> List[Dict]:
        """
        Search the corpus for the most relevant chunks.

        Returns a list of dicts with:
        - score
        - text
        - chunk_id, doc_id, title, year, doc_type, eval_type, source_path
        """
        if self.index.ntotal == 0:
            return []

        q_emb = self._encode_query(query)
        scores, indices = self.index.search(q_emb, top_k)
        scores = scores[0]
        indices = indices[0]

        results: List[Dict] = []
        for score, idx in zip(scores, indices):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            results.append(
                {
                    "score": float(score),
                    "text": meta["text"],
                    "chunk_id": meta["chunk_id"],
                    "doc_id": meta["doc_id"],
                    "title": meta["title"],
                    "year": meta["year"],
                    "doc_type": meta["doc_type"],
                    "eval_type": meta["eval_type"],
                    "source_path": meta["source_path"],
                }
            )
        return results


if __name__ == "__main__":
    # Pequeno teste manual
    searcher = ChunkSearcher()
    q = "What are datasheets for datasets?"
    hits = searcher.search(q, top_k=3)
    for h in hits:
        print(f"[{h['score']:.3f}] {h['title']} ({h['doc_id']})")
        print(h["text"][:200], "...\n")
