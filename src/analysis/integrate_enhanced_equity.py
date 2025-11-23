"""
Integration script for Enhanced Equity Analysis

Adds sophisticated equity analysis to the comprehensive analysis pipeline.

Usage:
    python integrate_enhanced_equity.py

This will:
1. Run enhanced equity analysis on all artifacts
2. Generate comparison report
3. Add results to comprehensive_analysis.json
4. Update ANALYSIS_SUMMARY.txt with equity findings
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analysis.enhanced_equity_analyzer import EnhancedEquityAnalyzer
from src.config.settings import PROCESSED_DIR
from collections import defaultdict


def integrate_enhanced_equity():
    """Run enhanced equity analysis and integrate with existing results."""
    
    print("\n" + "="*70)
    print("ENHANCED EQUITY ANALYSIS")
    print("="*70)
    
    # Load data
    print("\n[1/3] Loading data...")
    chunks_path = PROCESSED_DIR / "chunks.jsonl"
    chunks = []
    with chunks_path.open("r") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    
    metadata_path = PROCESSED_DIR / "doc_metadata.json"
    with metadata_path.open("r") as f:
        doc_metadata = json.load(f)
    
    # Organize chunks by doc
    chunks_by_doc = defaultdict(list)
    for chunk in chunks:
        doc_id = chunk.get("doc_id")
        if doc_id:
            chunks_by_doc[doc_id].append(chunk)
    
    # Run enhanced equity analysis
    print("[2/3] Running enhanced equity analysis...")
    analyzer = EnhancedEquityAnalyzer()
    
    all_analyses = []
    artifact_analyses = []
    
    for doc_id, doc_chunks in chunks_by_doc.items():
        doc_meta = doc_metadata.get(doc_id, {})
        print(f"   • {doc_meta.get('title', doc_id)}...")
        
        analysis = analyzer.analyze_document_equity(doc_chunks, doc_meta)
        all_analyses.append(analysis)
        
        if doc_meta.get("doc_type") == "artifact":
            artifact_analyses.append(analysis)
    
    # Compare artifacts
    print("[3/3] Generating comparison report...")
    comparison = analyzer.compare_documents(artifact_analyses)
    
    # Save results
    output_dir = Path("analysis_results")
    output_dir.mkdir(exist_ok=True)
    
    enhanced_results = {
        "all_documents": all_analyses,
        "artifact_comparison": comparison,
        "key_findings": {
            "avg_equity_score": comparison["average_equity_score"],
            "best_performing": comparison["best_equity_docs"][0] if comparison["best_equity_docs"] else None,
            "most_common_gap": comparison["common_gaps"][0] if comparison["common_gaps"] else None,
            "total_docs_analyzed": comparison["total_documents"]
        }
    }
    
    with (output_dir / "enhanced_equity_analysis.json").open("w") as f:
        json.dump(enhanced_results, f, indent=2)
    
    print(f"\n✅ Saved enhanced equity analysis")
    
    # Update comprehensive analysis
    comprehensive_path = output_dir / "complete_analysis.json"
    if comprehensive_path.exists():
        with comprehensive_path.open("r") as f:
            comprehensive = json.load(f)
        
        comprehensive["analyses"]["enhanced_equity"] = enhanced_results
        
        with comprehensive_path.open("w") as f:
            json.dump(comprehensive, f, indent=2)
        
        print("✅ Updated complete_analysis.json")
    
    # Generate equity-focused summary
    _generate_equity_summary(enhanced_results, output_dir)
    
    print("\n" + "="*70)
    print("ENHANCED EQUITY ANALYSIS COMPLETE")
    print("="*70)
    
    # Print key findings
    print(f"\n📊 Key Findings:")
    print(f"   • Average Equity Score: {comparison['average_equity_score']:.3f}/1.0")
    print(f"   • Documents Analyzed: {comparison['total_documents']}")
    print(f"   • Best: {comparison['best_equity_docs'][0]['title']} ({comparison['best_equity_docs'][0]['equity_score']:.3f})")
    
    if comparison['common_gaps']:
        print(f"\n⚠️  Most Common Gap:")
        top_gap = comparison['common_gaps'][0]
        print(f"   • {top_gap['gap']}")
        print(f"   • Affects {top_gap['affected_docs']}/{comparison['total_documents']} documents ({top_gap['percentage']}%)")
    
    print(f"\n📄 Outputs saved to: {output_dir}/")
    print(f"   • enhanced_equity_analysis.json")
    print(f"   • ENHANCED_EQUITY_SUMMARY.txt")


def _generate_equity_summary(results: dict, output_dir: Path):
    """Generate human-readable equity summary."""
    
    summary_path = output_dir / "ENHANCED_EQUITY_SUMMARY.txt"
    
    with summary_path.open("w") as f:
        f.write("="*70 + "\n")
        f.write("ENHANCED EQUITY ANALYSIS - SUMMARY\n")
        f.write("="*70 + "\n\n")
        
        f.write("METHODOLOGY\n")
        f.write("-" * 70 + "\n")
        f.write("This analysis goes beyond keyword matching to provide:\n")
        f.write("• Intersectional equity coverage (multiple protected characteristics)\n")
        f.write("• Fairness metric completeness assessment\n")
        f.write("• Quantitative vs. qualitative evidence distinction\n")
        f.write("• Bias mitigation strategy evaluation\n")
        f.write("• Best practices adherence scoring\n\n")
        
        comparison = results["artifact_comparison"]
        
        f.write("KEY FINDINGS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Average Equity Score: {comparison['average_equity_score']:.3f}/1.0\n")
        f.write(f"Documents Analyzed: {comparison['total_documents']}\n\n")
        
        f.write("BEST PERFORMING DOCUMENTS:\n")
        for i, doc in enumerate(comparison["best_equity_docs"][:3], 1):
            f.write(f"{i}. {doc['title']}\n")
            f.write(f"   Score: {doc['equity_score']:.3f}\n")
            f.write(f"   {doc['assessment']}\n\n")
        
        f.write("POOREST PERFORMING DOCUMENTS:\n")
        for i, doc in enumerate(comparison["worst_equity_docs"][:3], 1):
            f.write(f"{i}. {doc['title']}\n")
            f.write(f"   Score: {doc['equity_score']:.3f}\n")
            f.write(f"   {doc['assessment']}\n\n")
        
        f.write("SYSTEMATIC EQUITY GAPS\n")
        f.write("-" * 70 + "\n")
        for gap in comparison["common_gaps"]:
            f.write(f"• {gap['gap']}\n")
            f.write(f"  Affects: {gap['affected_docs']}/{comparison['total_documents']} documents ({gap['percentage']}%)\n\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("POLICY IMPLICATIONS\n")
        f.write("="*70 + "\n")
        f.write("""
1. MANDATE DISAGGREGATED REPORTING
   Current documentation largely lacks performance breakdowns by protected
   characteristics. Regulation should require quantitative fairness metrics
   across demographic groups.

2. REQUIRE INTERSECTIONAL ANALYSIS
   Most documents fail to consider compound discrimination. Standards should
   mandate analysis of intersecting identities (race × gender, disability × age, etc.)

3. STANDARDIZE FAIRNESS METRICS
   Without formal metrics (demographic parity, equalized odds, etc.), fairness
   claims are unverifiable. Procurement standards should specify required metrics.

4. ENFORCE MITIGATION DOCUMENTATION
   Merely identifying bias is insufficient. Documentation must describe specific
   technical mitigations implemented and their effectiveness.

5. ENABLE AUTOMATED AUDITING
   Machine-readable equity metrics would allow regulatory bodies and procurement
   officers to systematically evaluate documentation quality at scale.
        """)
    
    print(f"✅ Generated ENHANCED_EQUITY_SUMMARY.txt")


if __name__ == "__main__":
    integrate_enhanced_equity()