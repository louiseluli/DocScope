from pathlib import Path
import json
from typing import List, Dict, Tuple
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
import joblib

from src.config.settings import PROCESSED_DIR, MODELS_DIR
from src.audit.category_schema import load_category_schema


def load_chunks(chunks_path: Path) -> List[Dict]:
    chunks: List[Dict] = []
    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return chunks


def build_keyword_matcher(schema: Dict[str, Dict]) -> Dict[str, List[re.Pattern]]:
    """
    Build regex patterns for each category's keywords.
    """
    patterns: Dict[str, List[re.Pattern]] = {}
    for cat_id, info in schema.items():
        kws = info.get("keywords", [])
        pats = []
        for kw in kws:
            # simple word boundary match; lowercasing handled later
            # escape special chars in keyword
            pattern = re.compile(r"\b" + re.escape(kw.lower()) + r"\b")
            pats.append(pattern)
        patterns[cat_id] = pats
    return patterns


def weak_label_chunk(text: str, patterns: Dict[str, List[re.Pattern]]) -> str:
    """
    Assign a category to a chunk based on keyword hits.
    Returns category_id with highest hit count, or "other" if no hits.
    """
    text_l = text.lower()
    scores: Dict[str, int] = {}
    for cat_id, pats in patterns.items():
        count = 0
        for pat in pats:
            hits = len(pat.findall(text_l))
            count += hits
        scores[cat_id] = count

    # Get best category
    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        return "other"
    return best_cat


def prepare_training_data(
    min_length: int = 80, max_samples_per_cat: int = 200
) -> Tuple[List[str], List[str]]:
    """
    Create a weakly-labelled dataset from chunks.jsonl using keyword matching.

    Parameters
    ----------
    min_length : int
        Minimum length of text to be considered.
    max_samples_per_cat : int
        Cap number of training samples per category to avoid imbalance.

    Returns
    -------
    texts : List[str]
    labels : List[str]
    """
    chunks_path = PROCESSED_DIR / "chunks.jsonl"
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file not found at {chunks_path}")

    schema = load_category_schema()
    patterns = build_keyword_matcher(schema)

    chunks = load_chunks(chunks_path)
    texts: List[str] = []
    labels: List[str] = []

    per_cat_count: Dict[str, int] = {}

    for ch in chunks:
        text = ch["text"]
        if len(text) < min_length:
            continue

        cat = weak_label_chunk(text, patterns)

        # Limitar amostras por categoria
        current = per_cat_count.get(cat, 0)
        if current >= max_samples_per_cat:
            continue

        texts.append(text)
        labels.append(cat)
        per_cat_count[cat] = current + 1

    print("[INFO] Weak labelling summary:")
    for cat, cnt in sorted(per_cat_count.items(), key=lambda x: x[0]):
        print(f"  {cat}: {cnt} samples")

    return texts, labels


def train_category_classifier() -> None:
    texts, labels = prepare_training_data()

    if not texts:
        raise RuntimeError("No training data collected. Check chunks or keyword schema.")

    # handle small classes for stratification 
    class_counts = Counter(labels)
    min_count = min(class_counts.values())
    print("[INFO] Class distribution:", dict(class_counts))
    if min_count < 2:
        print(
            "[WARN] Some classes have fewer than 2 samples "
            f"(min={min_count}). Disabling stratified split."
        )
        stratify = None
    else:
        stratify = labels
    # ---------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.9,
    )

    print("[INFO] Fitting TF-IDF vectorizer...")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    clf = LogisticRegression(
        max_iter=1000,
        n_jobs=-1,
        multi_class="auto",
    )

    print("[INFO] Training Logistic Regression classifier...")
    clf.fit(X_train_vec, y_train)

    print("[INFO] Evaluation on held-out set:")
    y_pred = clf.predict(X_test_vec)
    print(classification_report(y_test, y_pred, zero_division=0))


    # Save models
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    vec_path = MODELS_DIR / "category_tfidf_vectorizer.pkl"
    clf_path = MODELS_DIR / "category_classifier.pkl"

    joblib.dump(vectorizer, vec_path)
    joblib.dump(clf, clf_path)

    print(f"[INFO] Saved TF-IDF vectorizer to {vec_path}")
    print(f"[INFO] Saved classifier to {clf_path}")


if __name__ == "__main__":
    train_category_classifier()
