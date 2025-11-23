"""
Enhanced metrics to complement coverage scores.
Shows information density, completeness, and specific gaps.
"""

import json
from pathlib import Path
from typing import Dict, List


def calculate_information_density(audit_results: Dict) -> Dict:
    """
    Calculate what % of document contains governance-relevant information.
    
    This helps explain low coverage scores.
    """
    metrics = {}
    
    for doc_id, audit in audit_results.items():
        total_chunks = audit['document']['total_chunks']
        
        # Count unique chunks with ANY governance information
        relevant_chunks = set()
        
        for cat_id, cat_info in audit['category_details'].items():
            if cat_id != 'other':  # Exclude "other" category
                relevant_chunks.update(cat_info['evidence_chunks'])
        
        density = len(relevant_chunks) / total_chunks if total_chunks > 0 else 0
        
        metrics[doc_id] = {
            'title': audit['document']['title'],
            'total_chunks': total_chunks,
            'governance_chunks': len(relevant_chunks),
            'information_density': round(density, 3),
            'interpretation': get_density_interpretation(density)
        }
    
    return metrics


def get_density_interpretation(density: float) -> str:
    """Interpret information density score."""
    if density < 0.2:
        return "Very sparse - most document is irrelevant to governance"
    elif density < 0.4:
        return "Sparse - significant portions lack governance info"
    elif density < 0.6:
        return "Moderate - half the document addresses governance"
    elif density < 0.8:
        return "Good - most content is governance-relevant"
    else:
        return "Excellent - comprehensive governance focus"


def identify_specific_missing_elements(audit_results: Dict) -> Dict:
    """
    Identify EXACTLY what information is missing.
    
    More actionable than just a score.
    """
    missing_analysis = {}
    
    for doc_id, audit in audit_results.items():
        doc_title = audit['document']['title']
        missing_elements = []
        
        # Check each category for zero-score items
        for cat_id, cat_info in audit['category_details'].items():
            if cat_info['coverage_score'] < 0.01:  # Essentially zero
                missing_elements.append({
                    'category': cat_info['name_en'],
                    'missing_questions': cat_info.get('missing_questions_en', [])[:3],
                    'importance': cat_info['importance_weight']
                })
        
        # Sort by importance
        missing_elements.sort(key=lambda x: x['importance'], reverse=True)
        
        missing_analysis[doc_id] = {
            'title': doc_title,
            'critical_missing_count': len([m for m in missing_elements if m['importance'] >= 0.9]),
            'missing_elements': missing_elements[:5]  # Top 5
        }
    
    return missing_analysis


def calculate_best_in_class_comparison(equity_data: Dict) -> Dict:
    """
    Show how current docs compare to best possible.
    """
    scores = [(doc_id, info['score']) for doc_id, info in equity_data['coverage_by_doc'].items()]
    scores.sort(key=lambda x: x[1], reverse=True)
    
    best_score = scores[0][1] if scores else 0
    worst_score = scores[-1][1] if scores else 0
    mean_score = sum(s[1] for s in scores) / len(scores) if scores else 0
    
    # What would "good" documentation look like?
    theoretical_best = 0.8  # 80% coverage if comprehensive
    
    return {
        'current_best': {
            'doc_id': scores[0][0],
            'score': best_score,
            'vs_theoretical': f"{(best_score/theoretical_best)*100:.1f}% of ideal"
        },
        'current_mean': {
            'score': mean_score,
            'vs_theoretical': f"{(mean_score/theoretical_best)*100:.1f}% of ideal"
        },
        'gap_to_excellence': theoretical_best - mean_score,
        'interpretation': f"Even best-in-class ({best_score:.3f}) achieves only {(best_score/theoretical_best)*100:.1f}% of comprehensive documentation"
    }


def generate_enhanced_summary():
    """Generate enhanced analysis with all new metrics."""
    
    # Load existing analysis
    with open('analysis_results/document_audits.json') as f:
        audits = json.load(f)
    
    with open('analysis_results/equity_focused_analysis.json') as f:
        equity = json.load(f)
    
    # Calculate enhanced metrics
    density = calculate_information_density(audits)
    missing = identify_specific_missing_elements(audits)
    best_comparison = calculate_best_in_class_comparison(equity)
    
    # Generate enhanced report
    report = {
        'information_density': density,
        'missing_elements': missing,
        'best_in_class_analysis': best_comparison
    }
    
    # Save
    with open('analysis_results/enhanced_metrics.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate readable summary
    with open('analysis_results/ENHANCED_FINDINGS.md', 'w') as f:
        f.write("# ENHANCED DOCUMENTATION ANALYSIS\n\n")
        
        f.write("## Why Are Scores So Low?\n\n")
        f.write("**The low scores reveal systematic documentation failure, not measurement error.**\n\n")
        
        f.write("### Information Density Analysis\n\n")
        f.write("What % of each document contains governance-relevant information:\n\n")
        f.write("| Document | Governance Chunks | Total Chunks | Density | Interpretation |\n")
        f.write("|----------|-------------------|--------------|---------|----------------|\n")
        
        for doc_id, metrics in list(density.items())[:8]:
            f.write(f"| {metrics['title'][:30]} | {metrics['governance_chunks']} | {metrics['total_chunks']} | {metrics['information_density']:.1%} | {metrics['interpretation']} |\n")
        
        f.write("\n### Comparison to Excellence\n\n")
        f.write(f"**Current Best**: {best_comparison['current_best']['score']:.3f} ")
        f.write(f"({best_comparison['current_best']['vs_theoretical']})\n\n")
        f.write(f"**Industry Mean**: {best_comparison['current_mean']['score']:.3f} ")
        f.write(f"({best_comparison['current_mean']['vs_theoretical']})\n\n")
        f.write(f"**Gap to Excellence**: {best_comparison['gap_to_excellence']:.3f}\n\n")
        f.write(f"*{best_comparison['interpretation']}*\n\n")
        
        f.write("\n### What's Actually Missing?\n\n")
        f.write("Specific elements absent from leading AI systems:\n\n")
        
        for doc_id, analysis in list(missing.items())[:3]:
            f.write(f"**{analysis['title']}**:\n")
            f.write(f"- {analysis['critical_missing_count']} critical elements missing\n")
            for elem in analysis['missing_elements'][:2]:
                f.write(f"  - {elem['category']}: {elem['missing_questions'][0] if elem['missing_questions'] else 'No disclosure'}\n")
            f.write("\n")
    
    print("✓ Generated enhanced metrics and findings")
    return report


if __name__ == "__main__":
    generate_enhanced_summary()