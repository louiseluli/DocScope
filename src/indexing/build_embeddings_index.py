from pathlib import Path
import json
from typing import List, Dict

import faiss
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

from src.config.settings import (
    PROCESSED_DIR,
    MODELS_DIR,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DIM,
)


def load_chunks(chunks_path: Path) -> List[Dict]:
    chunks: List[Dict] = []
    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return chunks


def build_embeddings_index(batch_size: int = 64) -> None:
    chunks_path = PROCESSED_DIR / "chunks.jsonl"
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file not found at {chunks_path}")

    chunks = load_chunks(chunks_path)
    print(f"[INFO] Loaded {len(chunks)} chunks")

    # Carregar modelo de embeddings
    print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # FAISS index (inner product, com vetores normalizados → cosine similarity)
    index = faiss.IndexFlatIP(EMBEDDING_DIM)

    # Metadados paralelos (mesmo índice do vetor no FAISS)
    metadata: List[Dict] = []

    all_embeddings: List[np.ndarray] = []

    texts = [ch["text"] for ch in chunks]

    for start in tqdm(range(0, len(texts), batch_size), desc="Encoding chunks"):
        end = min(start + batch_size, len(texts))
        batch_texts = texts[start:end]
        emb = model.encode(batch_texts, batch_size=batch_size, show_progress_bar=False)
        # Normalizar para cosine similarity
        emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)
        all_embeddings.append(emb)

    # Empilhar tudo
    embeddings = np.vstack(all_embeddings).astype("float32")
    print(f"[INFO] Embeddings shape: {embeddings.shape}")

    # Construir índice
    index.add(embeddings)
    print(f"[INFO] FAISS index size: {index.ntotal}")

    # Salvar índice e metadados
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    index_path = MODELS_DIR / "chunks_faiss.index"
    faiss.write_index(index, str(index_path))
    print(f"[INFO] Saved FAISS index to {index_path}")

    meta_path = MODELS_DIR / "chunks_metadata.jsonl"
    with meta_path.open("w", encoding="utf-8") as f:
        for ch in chunks:
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")
    print(f"[INFO] Saved metadata for {len(chunks)} chunks to {meta_path}")


if __name__ == "__main__":
    build_embeddings_index()
