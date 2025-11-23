from pathlib import Path
from typing import List
import pandas as pd

from src.config.settings import FRAMEWORKS_METADATA_PATH


def load_metadata(priority_max: int = 3) -> pd.DataFrame:
    """
    Load and filter the frameworks & artifacts metadata.

    Parameters
    ----------
    priority_max : int
        Keep only rows with priority <= priority_max.

    Returns
    -------
    pd.DataFrame
        DataFrame with at least:
        - doc_id
        - title
        - year
        - doc_type
        - eval_type
        - rel_path
        - priority
    """
    if not FRAMEWORKS_METADATA_PATH.exists():
        raise FileNotFoundError(f"Metadata file not found at {FRAMEWORKS_METADATA_PATH}")

    df = pd.read_csv(FRAMEWORKS_METADATA_PATH)

    required_cols: List[str] = [
        "doc_id", "title", "year", "doc_type",
        "eval_type", "rel_path", "priority"
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Metadata file is missing required columns: {missing}")

    # Filter by priority
    df = df[df["priority"] <= priority_max].copy()

    # Normalise paths to strings
    df["rel_path"] = df["rel_path"].astype(str)

    return df
