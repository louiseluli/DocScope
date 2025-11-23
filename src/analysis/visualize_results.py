"""
Generate visualizations for presentation.
Creates tables and summary statistics.
"""

import json
from pathlib import Path
from typing import Dict


def generate_coverage_table(analysis_dir: Path = Path("analysis_results")):
    """Generate markdown table of coverage by category."""
    
    deep_dives_path = analysis_dir / "category_deep_dives.json"
    with open(deep_dives_path) as f:
        data = json.load(f)
    
    print("\n## Category Coverage Summary\n")
    print("| Category | Importance | Mean Coverage | Range |")
    print("|----------|------------|---------------|-------|")
    
    for cat_id, info in data.items():
        name = info['name']
        importance = info['importance']
        cov = info['overall_coverage']
        
        print(f"| {name} | {importance} | {cov['mean']:.3f} | {cov['min']:.3f} - {cov['max']:.3f} |")


def generate_equity_summary(analysis_dir: Path = Path("analysis_results")):
    """Generate equity analysis summary."""
    
    equity_path = analysis_dir / "equity_focused_analysis.json"
    with open(equity_path) as f:
        data = json.load(f)
    
    print("\n## Equity Coverage Analysis\n")
    print(f"- **Total documents**: {data['total_docs_analyzed']}")
    print(f"- **With equity coverage**: {data['docs_with_equity_coverage']} ({data['docs_with_equity_coverage']/data['total_docs_analyzed']*100:.1f}%)")
    print(f"- **With quantitative metrics**: {data['docs_with_quantitative_equity']} ({data['docs_with_quantitative_equity']/data['total_docs_analyzed']*100:.1f}%)")
    print(f"- **Critical gaps**: {len(data['critical_gaps'])}")
    
    print("\n### Documents with Critical Equity Gaps:\n")
    for gap in data['critical_gaps'][:5]:
        print(f"- {gap['title']} (score: {gap['score']:.3f})")


def generate_presentation_stats(analysis_dir: Path = Path("analysis_results")):
    """Generate key statistics for presentation."""
    
    complete_path = analysis_dir / "complete_analysis.json"
    with open(complete_path) as f:
        data = json.load(f)
    
    print("\n## KEY STATISTICS FOR PRESENTATION\n")
    
    metadata = data['metadata']
    print(f"### Dataset")
    print(f"- Documents analyzed: **{metadata['total_documents']}**")
    print(f"- Text chunks processed: **{metadata['total_chunks']}**")
    print(f"- Governance categories: **{metadata['categories']}**")
    
    equity = data['analyses']['equity_analysis']
    print(f"\n### Equity Findings")
    print(f"- Only **{equity['docs_with_quantitative_equity']}/{equity['total_docs_analyzed']}** documents have quantitative fairness metrics")
    print(f"- **{len(equity['critical_gaps'])}** documents have critical equity gaps")
    
    gaps = data['analyses']['gap_summary']['summary']
    print(f"\n### Documentation Gaps")
    print(f"- Critical gaps: **{gaps['total_critical_gaps']}**")
    print(f"- High-priority gaps: **{gaps['total_high_gaps']}**")
    print(f"- Medium-priority gaps: **{gaps['total_medium_gaps']}**")


if __name__ == "__main__":
    print("="*70)
    print("DOCSCOPE COPILOT - VISUALIZATION GENERATOR")
    print("="*70)
    
    generate_presentation_stats()
    generate_coverage_table()
    generate_equity_summary()
    
    print("\n" + "="*70)
    print("Copy these tables into your presentation/memo")
    print("="*70)