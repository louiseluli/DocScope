"""
Interactive CLI for DocScope Copilot.
Designed for live demo during presentation.
"""

import json
from typing import Optional
from src.chatbot.bot_core import DocScopeCopilot


class InteractiveCLI:
    """Interactive command-line interface for demonstrations."""
    
    def __init__(self):
        print("\n" + "="*70)
        print("DOCSCOPE COPILOT - AI Documentation Governance Tool")
        print("="*70)
        self.bot = DocScopeCopilot()
        self.running = True
    
    def display_menu(self):
        """Display main menu."""
        print("\n" + "-"*70)
        print("MAIN MENU")
        print("-"*70)
        print("1. List available documents")
        print("2. Audit a specific document")
        print("3. Compare frameworks vs. artifacts")
        print("4. Analyze equity coverage")
        print("5. View category information")
        print("6. Quick demo (pre-configured analysis)")
        print("7. Exit")
        print("-"*70)
    
    def list_documents(self):
        """List all documents."""
        print("\n=== AVAILABLE DOCUMENTS ===\n")
        
        print("FRAMEWORKS & PAPERS:")
        frameworks = self.bot.list_documents(doc_type="framework")
        for doc in frameworks[:8]:
            print(f"  [{doc['doc_id']}]")
            print(f"    {doc['title']} ({doc['year']})")
            print(f"    Chunks: {doc['chunk_count']}\n")
        
        print("\nARTIFACTS (Real Documentation):")
        artifacts = self.bot.list_documents(doc_type="artifact")
        for doc in artifacts[:8]:
            print(f"  [{doc['doc_id']}]")
            print(f"    {doc['title']} ({doc['year']})")
            print(f"    Chunks: {doc['chunk_count']}\n")
    
    def audit_document(self):
        """Audit a specific document."""
        doc_id = input("\nEnter document ID (e.g., openai_gpt4o_system_card): ").strip()
        
        if not doc_id:
            print("❌ No document ID provided")
            return
        
        print(f"\n🔍 Auditing: {doc_id}...")
        result = self.bot.audit_document(doc_id)
        
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        
        # Display results
        doc_info = result["document"]
        coverage = result["coverage"]
        
        print(f"\n{'='*70}")
        print(f"AUDIT REPORT: {doc_info['title']}")
        print(f"{'='*70}")
        print(f"Type: {doc_info['doc_type']}")
        print(f"Year: {doc_info['year']}")
        print(f"Total chunks: {doc_info['total_chunks']}")
        print(f"Overall coverage: {coverage['overall_score']:.3f}")
        print(f"\n{'='*70}")
        print("CATEGORY COVERAGE:")
        print(f"{'='*70}")
        
        # Display category scores
        categories = result["category_details"]
        for cat_id, cat_info in sorted(categories.items(), 
                                       key=lambda x: x[1]['coverage_score'], 
                                       reverse=True):
            score = cat_info['coverage_score']
            name = cat_info['name_en']
            hits = cat_info['hit_count']
            
            # Visual bar
            bar_length = int(score * 50)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            print(f"\n{name}")
            print(f"  [{bar}] {score:.3f}")
            print(f"  Evidence: {hits} chunks, {cat_info['table_hits']} tables")
            
            if cat_info['matched_keywords'][:3]:
                print(f"  Keywords: {', '.join(cat_info['matched_keywords'][:3])}")
        
        # Display gaps
        gaps = result.get("gap_analysis", {})
        if gaps:
            print(f"\n{'='*70}")
            print("CRITICAL GAPS:")
            print(f"{'='*70}")
            
            for cat_id, gap in gaps.items():
                if gap.get("severity") in ["critical", "high"]:
                    print(f"\n⚠️  {gap['name']}")
                    print(f"   Severity: {gap['severity'].upper()}")
                    print(f"   Recommendation: {gap['recommendation'][:150]}...")
    
    def compare_frameworks_artifacts(self):
        """Compare framework recommendations vs. actual practice.

        Prints a short summary and the top category gaps (frameworks - artifacts).
        This implementation is defensive: it handles missing keys and empty
        responses from `compare_documents`.
        """
        print("\n🔍 Comparing frameworks vs. artifacts...")
        result = self.bot.compare_documents(by_type=True)

        if not isinstance(result, dict) or result.get("error"):
            err = result.get("error") if isinstance(result, dict) else "Unexpected result"
            print(f"❌ Comparison failed: {err}")
            return

        frameworks_meta = result.get("frameworks", {})
        artifacts_meta = result.get("artifacts", {})

        fw_count = frameworks_meta.get("doc_count", 0)
        art_count = artifacts_meta.get("doc_count", 0)

        print(f"\n{'='*70}")
        print("FRAMEWORK VS. ARTIFACT COMPARISON")
        print(f"{'='*70}")
        print(f"Frameworks analyzed: {fw_count}")
        print(f"Artifacts analyzed: {art_count}")

        print(f"\n{'='*70}")
        print("CATEGORY GAPS:")
        print(f"{'='*70}")

        comparisons = result.get("category_comparison", {}) or {}
        gap_list = []

        for cat_id, comp in comparisons.items():
            try:
                gap = float(comp.get("gap", 0))
            except Exception:
                gap = 0.0

            # Store tuple (gap, cat_id, comp) so sorting is explicit
            gap_list.append((gap, cat_id, comp))

        # Sort by gap size (descending)
        gap_list.sort(key=lambda x: x[0], reverse=True)

        printed = 0
        for gap, cat_id, comp in gap_list:
            if printed >= 5:
                break

            if gap <= 0.01:
                # small or no gap — stop showing further items
                continue

            name = comp.get("category_name") or self.bot.schema.get(cat_id, {}).get("human_name_en", cat_id)
            fw_mean = comp.get("framework_mean", 0.0)
            art_mean = comp.get("artifact_mean", 0.0)

            print(f"\n{name}")
            print(f"  Framework mean: {fw_mean:.3f}")
            print(f"  Artifact mean: {art_mean:.3f}")
            print(f"  GAP: {gap:.3f} ⚠️")

            printed += 1

        if printed == 0:
            print("No meaningful gaps found between frameworks and artifacts.")
    
    def analyze_equity(self):
        """Analyze equity coverage."""
        print("\n🔍 Analyzing equity & bias coverage...")
        result = self.bot.analyze_equity_coverage()
        
        total = result['total_docs_analyzed']
        with_coverage = result['docs_with_equity_coverage']
        with_quant = result['docs_with_quantitative_equity']
        
        print(f"\n{'='*70}")
        print("EQUITY & BIAS ANALYSIS")
        print(f"{'='*70}")
        print(f"Documents analyzed: {total}")
        print(f"Documents with ANY equity coverage: {with_coverage}/{total} ({with_coverage/total*100:.1f}%)")
        print(f"Documents with QUANTITATIVE equity data: {with_quant}/{total} ({with_quant/total*100:.1f}%)")
        
        critical_gaps = result.get('critical_gaps', [])
        print(f"\n⚠️  CRITICAL EQUITY GAPS: {len(critical_gaps)}")
        
        for gap in critical_gaps[:5]:
            print(f"  - {gap['title']}: score={gap['score']:.3f}")
    
    def view_category(self):
        """View category information."""
        print("\nAvailable categories:")
        for i, cat_id in enumerate(self.bot.schema.keys(), 1):
            name = self.bot.schema[cat_id].get('human_name_en')
            print(f"  {i}. {cat_id}: {name}")
        
        choice = input("\nEnter category ID: ").strip()
        
        if choice not in self.bot.schema:
            print("❌ Invalid category")
            return
        
        result = self.bot.get_category_overview(choice)
        
        print(f"\n{'='*70}")
        print(f"{result['name'].upper()}")
        print(f"{'='*70}")
        print(f"Importance: {result['importance']}")
        print(f"Governance Axis: {result['governance_axis']}")
        print(f"\nDescription:")
        print(f"  {result['description']}")
        
        print(f"\n{'='*70}")
        print("OVERALL COVERAGE STATISTICS:")
        print(f"{'='*70}")
        cov = result['overall_coverage']
        print(f"Mean: {cov['mean']:.3f}")
        print(f"Range: {cov['min']:.3f} - {cov['max']:.3f}")
        print(f"Documents: {cov['docs_evaluated']}")
        
        print(f"\n{'='*70}")
        print("KEY QUESTIONS THIS CATEGORY ADDRESSES:")
        print(f"{'='*70}")
        for q in result['question_templates'][:3]:
            print(f"  • {q}")
    
    def quick_demo(self):
        """Run pre-configured demo."""
        print("\n🎯 RUNNING QUICK DEMO...")
        
        print("\n[1/3] Auditing GPT-4o System Card...")
        self.bot.audit_document("openai_gpt4o_system_card")
        
        print("\n[2/3] Comparing frameworks vs artifacts...")
        self.bot.compare_documents(by_type=True)
        
        print("\n[3/3] Analyzing equity coverage...")
        self.bot.analyze_equity_coverage()
        
        print("\n✅ Demo complete!")
    
    def run(self):
        """Main event loop."""
        while self.running:
            self.display_menu()
            choice = input("\nSelect option (1-7): ").strip()
            
            if choice == "1":
                self.list_documents()
            elif choice == "2":
                self.audit_document()
            elif choice == "3":
                self.compare_frameworks_artifacts()
            elif choice == "4":
                self.analyze_equity()
            elif choice == "5":
                self.view_category()
            elif choice == "6":
                self.quick_demo()
            elif choice == "7":
                print("\n👋 Goodbye!")
                self.running = False
            else:
                print("\n❌ Invalid option")
            
            if self.running and choice != "7":
                input("\nPress Enter to continue...")


def main():
    """Entry point."""
    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()