from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"

# Specific files
FRAMEWORKS_METADATA_PATH = RAW_DIR / "frameworks_metadata.csv"
CHUNKS_PATH = PROCESSED_DIR / "chunks.jsonl"
LABELLED_CHUNKS_PATH = PROCESSED_DIR / "labelled_chunks.csv"
DOC_METADATA_PATH = PROCESSED_DIR / "doc_metadata.json"
CATEGORY_SCHEMA_PATH = PROCESSED_DIR / "category_schema.json"

# Embeddings settings
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # for all-MiniLM-L6-v2

# Retrieval settings
TOP_K_RETRIEVAL = 5

# Classifier settings
CLASSIFIER_NAME = "tfidf_logreg_v1"

# Language defaults for explanations
DEFAULT_LANG = "en"
