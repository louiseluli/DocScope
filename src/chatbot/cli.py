"""
Command-line interface for the docscope-copilot governance chatbot.

This CLI:
- Runs entirely on local / open-source components (no GPT / paid APIs).
- Uses GovernanceCopilot.query() to retrieve:
    - governance_view: structured coverage / risk scores per category
    - evidence: top retrieved documentation snippets
- Builds a human-readable answer that is:
    - Focused on the user's question topic
    - Explicit about best-documented vs weakest areas
    - Grounded in the actual evidence list

All comments and user-facing text are in English for hackathon demo purposes.
"""

from typing import Dict, Any, List, Tuple

from src.chatbot.bot_core import GovernanceCopilot


# Mapping from internal category IDs to nice names for display.
PRETTY_CATEGORY_NAMES = {
    "safety_risk": "Safety & Risk",
    "intended_use_limitations": "Intended Use & Limitations",
    "training_data": "Training Data",
    "performance_capabilities": "Performance & Capabilities",
    "organizational_governance": "Organizational & Governance",
    "access_deployment": "Access & Deployment",
    "equity_bias": "Equity & Bias",
    "other": "Other / Misc.",
}

# Simple heuristic to ignore shell commands in the CLI.
SHELL_LIKE_PREFIXES = (
    "cd ",
    "ls",
    "pwd",
    "python ",
    "pip ",
    "./",
    "bash ",
    "sh ",
)


def pretty_cat(cat_id: str) -> str:
    """Return a human-readable name for a category ID."""
    return PRETTY_CATEGORY_NAMES.get(cat_id, cat_id)


def list_to_english(items: List[str]) -> str:
    """Turn a list into a human-readable phrase."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def detect_topic(query: str) -> str:
    """
    Very lightweight intent detection to tailor the answer.

    Returns one of: "training", "equity", "safety", "performance", "general".
    """
    q = query.lower()
    if any(k in q for k in ["equity", "bias", "fairness", "subgroup", "minority"]):
        return "equity"
    if any(k in q for k in ["train", "training data", "dataset", "corpus", "data "]):
        return "training"
    if any(k in q for k in ["safety", "risk", "red team", "jailbreak"]):
        return "safety"
    if any(k in q for k in ["performance", "benchmark", "capabilit"]):
        return "performance"
    return "general"


def summarize_overall(overall: float) -> str:
    """Map overall coverage score into a qualitative description."""
    if overall >= 0.7:
        return "strong and comparatively comprehensive"
    if overall >= 0.4:
        return "mixed and uneven"
    return "limited and fragmented"


def split_best_and_worst(
    categories: Dict[str, Dict[str, float]],
    top_k: int = 2,
) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """
    Split categories into 'best' and 'worst' based on coverage.

    Returns:
        best: list of (cat_id, coverage) for top_k highest coverage
        worst: list of (cat_id, coverage) for top_k lowest coverage
    """
    items = [
        (cat_id, info.get("avg_coverage_score", 0.0))
        for cat_id, info in categories.items()
    ]
    items.sort(key=lambda x: x[1], reverse=True)
    best = items[:top_k]
    worst = items[-top_k:] if len(items) > top_k else items
    return best, worst


def render_natural_language_answer(result: Dict[str, Any]) -> str:
    """
    Build a human-readable answer from the governance_view + evidence.

    This function is intentionally:
    - Local / deterministic (no external LLM).
    - Topic-aware (training, equity, safety, performance).
    - Focused on best-documented vs weakest areas instead of repeating
      the same phrases for every question.
    """
    query = result.get("query", "")
    topic = detect_topic(query)

    gov = result.get("governance_view", {})
    cats = gov.get("categories", {})
    overall = gov.get("overall_coverage_score", 0.0)
    equity_risk = gov.get("equity_risk_flag", "unknown")

    lines: List[str] = []
    lines.append("=== Answer ===")
    if query:
        lines.append(f"Question: {query}")
        lines.append("")

    # 1) Overall framing
    overall_desc = summarize_overall(overall)
    lines.append(
        f"Across the documentation you ingested, coverage of key governance "
        f"dimensions is {overall_desc} (overall score ≈ {overall:.2f})."
    )

    # 2) Best / worst documented areas (for comparability)
    best, worst = split_best_and_worst(cats)

    if best:
        best_labels = [
            f"{pretty_cat(cid)} (≈{cov:.2f})" for cid, cov in best if cov > 0
        ]
        if best_labels:
            lines.append(
                "The best-documented areas in this corpus are: "
                f"{list_to_english(best_labels)}."
            )

    if worst:
        worst_labels = [
            f"{pretty_cat(cid)} (≈{cov:.2f})" for cid, cov in worst if cov < 0.4
        ]
        if worst_labels:
            lines.append(
                "The weakest areas, where documentation is systematically thin, are: "
                f"{list_to_english(worst_labels)}."
            )

    # 3) Equity / bias always explicitly discussed (core to the challenge)
    if equity_risk == "high":
        lines.append(
            "On **Equity & Bias**, the corpus exposes clear structural gaps: "
            "very few documents report subgroup performance, demographic breakdowns, "
            "or systematic fairness evaluations. This makes cross-model comparison "
            "on equity nearly impossible."
        )
    elif equity_risk == "medium":
        lines.append(
            "On **Equity & Bias**, some documents include fairness or subgroup "
            "analysis, but coverage is inconsistent and not aligned to a common "
            "set of protected groups or metrics."
        )
    else:
        lines.append(
            "On **Equity & Bias**, the current evidence is too sparse to make a "
            "reliable judgment about coverage."
        )

    # 4) Topic-specific commentary
    td_cov = cats.get("training_data", {}).get("avg_coverage_score", 0.0)
    eb_cov = cats.get("equity_bias", {}).get("avg_coverage_score", 0.0)
    s_cov = cats.get("safety_risk", {}).get("avg_coverage_score", 0.0)
    p_cov = cats.get("performance_capabilities", {}).get("avg_coverage_score", 0.0)

    if topic == "training":
        if td_cov >= 0.5:
            lines.append(
                "For **Training Data**, many documents provide high-level descriptions "
                "of data sources and sometimes filtering or de-duplication methods, "
                "but they still rarely break down demographics or sensitive domains."
            )
        elif td_cov >= 0.2:
            lines.append(
                "For **Training Data**, most documentation only mentions 'web-scale' "
                "or 'proprietary' data. Details on collection pipelines, filtering, "
                "and demographic composition are often missing or scattered."
            )
        else:
            lines.append(
                "For **Training Data**, documentation is extremely minimal: it is "
                "often limited to a one-line reference to 'internal' or 'web' data "
                "with no further structure."
            )

    elif topic == "equity":
        if eb_cov >= 0.5:
            lines.append(
                "On **Equity & Bias**, a subset of documents do report subgroup "
                "performance and mitigation strategies, but they use incompatible "
                "definitions and metrics."
            )
        elif eb_cov >= 0.2:
            lines.append(
                "On **Equity & Bias**, there are scattered mentions of 'fairness' or "
                "'demographic performance', but very few concrete, reproducible "
                "evaluations across protected groups."
            )
        else:
            lines.append(
                "On **Equity & Bias**, documentation mostly consists of high-level "
                "statements (e.g., 'we aim to reduce bias') without quantitative "
                "evidence or clearly defined protected groups."
            )

    elif topic == "safety":
        if s_cov >= 0.5:
            lines.append(
                "On **Safety & Risk**, some system cards document red-teaming "
                "campaigns, qualitative failure modes, and mitigation strategies in "
                "moderate detail."
            )
        elif s_cov >= 0.2:
            lines.append(
                "On **Safety & Risk**, many documents refer to alignment and safety "
                "work but rarely provide quantitative metrics (e.g., refusal rates, "
                "jailbreak success rates) that would enable comparison."
            )
        else:
            lines.append(
                "On **Safety & Risk**, documentation tends to be narrative, with "
                "few concrete numbers or structured risk scenarios."
            )

    elif topic == "performance":
        if p_cov >= 0.5:
            lines.append(
                "On **Performance & Capabilities**, many model cards and reports "
                "do include benchmark tables and capability descriptions, but they "
                "often use different suites or metrics, which complicates "
                "cross-model comparison."
            )
        else:
            lines.append(
                "On **Performance & Capabilities**, benchmarks are mentioned, but "
                "not in a way that is consistently comparable across model families."
            )

    # 5) Evidence grounding
    evidence = result.get("evidence", [])
    if evidence:
        lines.append("")
        lines.append(
            "These conclusions are grounded in the top retrieved sources, for example:"
        )
        for ev in evidence[:3]:
            lines.append(f"  • {ev['title']} ({ev['doc_type']})")

    # 6) Policy / hackathon hook
    lines.append("")
    lines.append(
        "From a policy and governance perspective, this analysis allows you to "
        "treat documentation as a measurable object: you can specify minimum "
        "coverage thresholds for categories like Safety & Risk, Training Data, "
        "and Equity & Bias, and then compare model families against those "
        "thresholds in a structured way."
    )

    return "\n".join(lines)


def main() -> None:
    """
    Interactive CLI loop.

    - Uses only local / open-source models and libraries.
    - No external GPT or proprietary API calls are made.
    """
    bot = GovernanceCopilot()

    print("=== docscope-copilot ===")
    print("Governance chatbot for AI documentation")
    print("Runs entirely on local, open-source components (no GPT / paid APIs).")
    print("Type a question about documentation (or 'exit' to quit).")
    print()

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Bye!")
            break

        # Ignore obvious shell commands accidentally pasted into the prompt.
        if user_input.startswith(SHELL_LIKE_PREFIXES):
            print(
                "It looks like you typed a shell command. "
                "Please ask a question about AI documentation instead."
            )
            continue

        # Query the core bot: this returns governance_view + evidence.
        result = bot.query(user_input)

        print()
        print(render_natural_language_answer(result))
        print()

        # Show the structured governance summary for transparency / demo purposes.
        gov = result["governance_view"]
        print("[Governance summary]")
        print(f"  Overall coverage: {gov['overall_coverage_score']:.2f}")
        print(f"  Equity risk flag: {gov['equity_risk_flag']}")
        print("  Categories:")
        for cat_id, info in gov["categories"].items():
            print(
                f"    - {pretty_cat(cat_id)}: "
                f"avg_coverage={info['avg_coverage_score']:.2f}, "
                f"risk={info['risk_flag']}"
            )

        print("\n[Top evidence]")
        for ev in result["evidence"]:
            print(
                f"  - {ev['title']} ({ev['doc_type']}, score={ev['score']:.3f})"
            )
            preview = ev["text_preview"].replace("\n", " ")
            if len(preview) > 240:
                preview = preview[:240] + "..."
            print(f"    {preview}")
        print()


if __name__ == "__main__":
    main()
