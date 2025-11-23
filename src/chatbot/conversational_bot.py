"""
Conversational chatbot interface for DocScope Copilot.
Uses local open-source models for natural language interaction.
"""

from typing import List, Dict, Optional
import json
from src.chatbot.bot_core import DocScopeCopilot


class ConversationalDocBot:
    """
    Conversational interface for documentation analysis.
    
    Designed for stakeholders:
    - Policymakers (understand documentation gaps)
    - Procurement officers (evaluate vendor claims)
    - Civil society (identify equity issues)
    - Researchers (comparative analysis)
    """
    
    def __init__(self):
        self.bot = DocScopeCopilot()
        self.conversation_history = []
        self.context = {
            "last_doc_audited": None,
            "last_category_viewed": None
        }
    
    def get_stakeholder_intro(self, stakeholder_type: str) -> str:
        """Get customized introduction for different stakeholders."""
        intros = {
            "policymaker": """
Welcome, Policymaker! 

I can help you:
- Identify systematic documentation gaps across AI systems
- Understand which governance categories are poorly covered
- Generate evidence for regulatory requirements
- Compare current practice to framework recommendations

Try asking: "What are the biggest documentation gaps?"
            """,
            
            "procurement": """
Welcome, Procurement Officer!

I can help you:
- Audit vendor documentation against standards
- Score documentation coverage across categories
- Identify missing critical information
- Compare vendors side-by-side

Try asking: "How does GPT-4o's documentation score?"
            """,
            
            "civil_society": """
Welcome, Civil Society Advocate!

I can help you:
- Identify equity and bias documentation gaps
- Find missing fairness metrics
- Highlight disparate impact information
- Track accountability mechanisms

Try asking: "Which models lack equity documentation?"
            """,
            
            "researcher": """
Welcome, Researcher!

I can help you:
- Compare documentation frameworks
- Analyze coverage patterns across models
- Extract specific category information
- Generate comparative statistics

Try asking: "Compare framework recommendations to actual artifacts"
            """
        }
        
        return intros.get(stakeholder_type, intros["researcher"])
    
    def interpret_query(self, query: str) -> Dict:
        """
        Interpret natural language query and map to appropriate function.
        
        Simple keyword-based routing (no LLM needed for demo).
        """
        query_lower = query.lower()
        
        # Audit specific document
        if any(word in query_lower for word in ["audit", "analyze", "score", "evaluate"]):
            # Extract document name
            doc_keywords = ["gpt", "llama", "whisper", "qwen", "o1", "stable diffusion"]
            for keyword in doc_keywords:
                if keyword in query_lower:
                    return {
                        "action": "audit_document",
                        "params": {"keyword": keyword}
                    }
        
        # Equity analysis
        if any(word in query_lower for word in ["equity", "bias", "fairness", "discrimination", "disparate"]):
            return {
                "action": "analyze_equity",
                "params": {}
            }
        
        # Gap analysis
        if any(word in query_lower for word in ["gap", "missing", "lack", "absent", "weakness"]):
            return {
                "action": "gap_analysis",
                "params": {}
            }
        
        # Framework comparison
        if any(word in query_lower for word in ["compare", "framework", "versus", "vs", "difference"]):
            return {
                "action": "compare_frameworks",
                "params": {}
            }
        
        # List documents
        if any(word in query_lower for word in ["list", "show", "available", "which models"]):
            return {
                "action": "list_documents",
                "params": {}
            }
        
        # Category information
        if any(word in query_lower for word in ["category", "safety", "training data", "governance"]):
            for cat_id in self.bot.schema.keys():
                if cat_id.replace("_", " ") in query_lower:
                    return {
                        "action": "category_info",
                        "params": {"category_id": cat_id}
                    }
        
        # Default: provide help
        return {
            "action": "help",
            "params": {}
        }
    
    def execute_action(self, action_info: Dict) -> str:
        """Execute the interpreted action and return response."""
        action = action_info["action"]
        params = action_info["params"]
        
        if action == "audit_document":
            return self._handle_audit(params)
        elif action == "analyze_equity":
            return self._handle_equity()
        elif action == "gap_analysis":
            return self._handle_gaps()
        elif action == "compare_frameworks":
            return self._handle_comparison()
        elif action == "list_documents":
            return self._handle_list()
        elif action == "category_info":
            return self._handle_category(params)
        else:
            return self._handle_help()
    
    def _handle_audit(self, params: Dict) -> str:
        """Handle document audit request."""
        keyword = params.get("keyword", "")
        
        # Find matching document
        docs = self.bot.list_documents()
        matching_doc = None
        
        for doc in docs:
            if keyword in doc["doc_id"].lower() or keyword in doc["title"].lower():
                matching_doc = doc
                break
        
        if not matching_doc:
            return f"❌ Could not find a document matching '{keyword}'. Try: {', '.join([d['doc_id'] for d in docs[:3]])}"
        
        doc_id = matching_doc["doc_id"]
        self.context["last_doc_audited"] = doc_id
        
        # Audit the document
        result = self.bot.audit_document(doc_id)
        
        # Format response
        response = f"""
📊 **Audit Report: {result['document']['title']}**

**Overall Coverage**: {result['coverage']['overall_score']:.3f}

**Top Categories**:
"""
        
        # Get top 3 categories by score
        categories = sorted(
            result['category_details'].items(),
            key=lambda x: x[1]['coverage_score'],
            reverse=True
        )[:3]
        
        for cat_id, info in categories:
            response += f"\n  • {info['name_en']}: {info['coverage_score']:.3f} ({info['hit_count']} chunks)"
        
        # Add critical gaps
        gaps = result.get("gap_analysis", {})
        critical_gaps = [g for g in gaps.values() if g.get("severity") in ["critical", "high"]]
        
        if critical_gaps:
            response += f"\n\n⚠️ **Critical Gaps**: {len(critical_gaps)}"
            for gap in critical_gaps[:2]:
                response += f"\n  • {gap['name']}: {gap['recommendation'][:100]}..."
        
        return response
    
    def _handle_equity(self) -> str:
        """Handle equity analysis request."""
        result = self.bot.analyze_equity_coverage()
        
        total = result['total_docs_analyzed']
        with_coverage = result['docs_with_equity_coverage']
        with_quant = result['docs_with_quantitative_equity']
        critical = len(result['critical_gaps'])
        
        response = f"""
🔍 **Equity & Bias Analysis**

**Coverage Statistics**:
  • Documents analyzed: {total}
  • With ANY equity coverage: {with_coverage}/{total} ({with_coverage/total*100:.1f}%)
  • With QUANTITATIVE metrics: {with_quant}/{total} ({with_quant/total*100:.1f}%)
  
⚠️ **Critical Finding**: {critical} documents have severe equity gaps

**Worst Offenders**:
"""
        
        for gap in result['critical_gaps'][:5]:
            response += f"\n  • {gap['title']}: score={gap['score']:.3f}"
        
        response += "\n\n💡 **Recommendation**: Mandate disaggregated performance reporting across demographic groups"
        
        return response
    
    def _handle_gaps(self) -> str:
        """Handle gap analysis request."""
        # Audit all documents quickly
        artifacts = self.bot.list_documents(doc_type="artifact")
        
        gap_counts = {"critical": 0, "high": 0, "medium": 0}
        problem_categories = {}
        
        for doc in artifacts[:5]:
            result = self.bot.audit_document(doc["doc_id"])
            gaps = result.get("gap_analysis", {})
            
            for cat_id, gap in gaps.items():
                severity = gap.get("severity", "low")
                if severity in gap_counts:
                    gap_counts[severity] += 1
                
                cat_name = gap.get("name", cat_id)
                if cat_name not in problem_categories:
                    problem_categories[cat_name] = 0
                problem_categories[cat_name] += 1
        
        response = f"""
📉 **Documentation Gap Analysis**

**Gap Severity**:
  • Critical: {gap_counts['critical']}
  • High: {gap_counts['high']}
  • Medium: {gap_counts['medium']}

**Most Problematic Categories**:
"""
        
        top_problems = sorted(problem_categories.items(), key=lambda x: x[1], reverse=True)[:3]
        for cat_name, count in top_problems:
            response += f"\n  • {cat_name}: {count} gaps"
        
        response += "\n\n💡 **Policy Implication**: Standardized documentation requirements needed"
        
        return response
    
    def _handle_comparison(self) -> str:
        """Handle framework vs artifact comparison."""
        result = self.bot.compare_documents(by_type=True)
        
        frameworks_count = result['frameworks']['doc_count']
        artifacts_count = result['artifacts']['doc_count']
        
        response = f"""
🔬 **Framework vs. Artifact Comparison**

  • Frameworks analyzed: {frameworks_count}
  • Artifacts analyzed: {artifacts_count}

**Biggest Gaps** (What frameworks recommend but artifacts lack):
"""
        
        comparisons = result.get("category_comparison", {})
        gaps = []
        
        for cat_id, comp in comparisons.items():
            gap = comp.get("gap", 0)
            if gap > 0.01:
                gaps.append((gap, comp))
        
        gaps.sort(reverse=True, key=lambda x: x[0])
        
        for gap, comp in gaps[:3]:
            response += f"\n  • {comp['category_name']}: {gap:.3f} gap"
            response += f"\n    (Frameworks: {comp.get('framework_mean', 0):.3f}, Artifacts: {comp.get('artifact_mean', 0):.3f})"
        
        response += "\n\n💡 **Finding**: Significant gap between recommendations and practice"
        
        return response
    
    def _handle_list(self) -> str:
        """Handle list documents request."""
        artifacts = self.bot.list_documents(doc_type="artifact")
        
        response = "📚 **Available AI Artifacts**:\n"
        for doc in artifacts[:8]:
            response += f"\n  • {doc['title']} ({doc['year']})"
            response += f"\n    ID: {doc['doc_id']}"
        
        response += "\n\n💬 Ask me to audit any of these documents!"
        
        return response
    
    def _handle_category(self, params: Dict) -> str:
        """Handle category information request."""
        cat_id = params.get("category_id")
        result = self.bot.get_category_overview(cat_id)
        
        response = f"""
📋 **{result['name']}**

**Importance**: {result['importance']}
**Governance Axis**: {result['governance_axis']}

**Description**: {result['description'][:200]}...

**Coverage Statistics**:
  • Mean: {result['overall_coverage']['mean']:.3f}
  • Range: {result['overall_coverage']['min']:.3f} - {result['overall_coverage']['max']:.3f}

**Key Questions**:
"""
        
        for q in result['question_templates'][:2]:
            response += f"\n  • {q}"
        
        return response
    
    def _handle_help(self) -> str:
        """Provide help information."""
        return """
💬 **How can I help you?**

**Try asking**:
  • "Audit GPT-4o's documentation"
  • "What are the equity gaps?"
  • "Compare frameworks to artifacts"
  • "Which models lack safety information?"
  • "Show me available documents"
  • "Tell me about the safety category"

**Your stakeholder role**: I can customize my responses for:
  • Policymakers
  • Procurement officers
  • Civil society advocates
  • Researchers
"""
    
    def chat(self, user_message: str) -> str:
        """Main chat interface."""
        # Interpret and execute
        action_info = self.interpret_query(user_message)
        response = self.execute_action(action_info)
        
        # Store in history
        self.conversation_history.append({
            "user": user_message,
            "bot": response
        })
        
        return response


def main():
    """Run conversational bot."""
    print("="*70)
    print("DOCSCOPE COPILOT - Conversational Interface")
    print("="*70)
    
    bot = ConversationalDocBot()
    
    # Stakeholder selection
    print("\nWho are you?")
    print("1. Policymaker")
    print("2. Procurement Officer")
    print("3. Civil Society Advocate")
    print("4. Researcher")
    
    choice = input("\nSelect (1-4): ").strip()
    stakeholder_map = {
        "1": "policymaker",
        "2": "procurement",
        "3": "civil_society",
        "4": "researcher"
    }
    
    stakeholder = stakeholder_map.get(choice, "researcher")
    print(bot.get_stakeholder_intro(stakeholder))
    
    print("\n" + "="*70)
    print("Start chatting! (type 'quit' to exit)")
    print("="*70 + "\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("\n👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        response = bot.chat(user_input)
        print(f"\nBot: {response}\n")


if __name__ == "__main__":
    main()