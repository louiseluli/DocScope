import json
from pathlib import Path
from typing import Dict, Any


BASE_DIR = Path(__file__).resolve().parents[2]
SCHEMA_PATH = BASE_DIR / "data" / "processed" / "category_schema.json"


def load_category_schema() -> Dict[str, Any]:
    """
    Load the category schema from the JSON file.

    Returns
    -------
    Dict[str, Any]
        A dictionary where keys are category IDs (e.g. "safety_risk")
        and values are dictionaries with fields:
        - human_name_en / human_name_pt
        - description_en / description_pt
        - examples
        - keywords
    """
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return schema


def get_category_ids() -> list:
    """
    Return a list of category IDs defined in the schema.
    """
    schema = load_category_schema()
    return list(schema.keys())


def get_keywords_for_category(category_id: str) -> list:
    """
    Return the list of keywords associated with a category.

    Parameters
    ----------
    category_id : str
        ID of the category (e.g. "training_data").

    Returns
    -------
    list
        List of keyword strings. Returns an empty list if not found.
    """
    schema = load_category_schema()
    category = schema.get(category_id, {})
    return category.get("keywords", [])


def get_human_name(category_id: str, lang: str = "en") -> str:
    """
    Get the human-readable name for a category in the given language.

    Parameters
    ----------
    category_id : str
        ID of the category.
    lang : str
        "en" for English, "pt" for Portuguese.

    Returns
    -------
    str
        Human-readable name, or the category_id if not found.
    """
    schema = load_category_schema()
    category = schema.get(category_id)
    if not category:
        return category_id

    if lang == "pt":
        return category.get("human_name_pt", category.get("human_name_en", category_id))
    return category.get("human_name_en", category_id)


def get_description(category_id: str, lang: str = "en") -> str:
    """
    Get the description for a category in the given language.

    Parameters
    ----------
    category_id : str
        ID of the category.
    lang : str
        "en" for English, "pt" for Portuguese.

    Returns
    -------
    str
        Description text, or empty string if not found.
    """
    schema = load_category_schema()
    category = schema.get(category_id)
    if not category:
        return ""

    if lang == "pt":
        return category.get("description_pt", category.get("description_en", ""))
    return category.get("description_en", "")
