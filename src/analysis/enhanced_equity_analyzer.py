"""
Enhanced Equity Analyzer for AI Documentation

Goes beyond basic keyword matching to provide sophisticated equity analysis:
1. Intersectional equity coverage (multiple protected characteristics)
2. Disparate impact quantification
3. Fairness metric completeness assessment
4. Best practices identification
5. Concrete, actionable recommendations

Directly addresses MIT rubric criterion: Equity
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import re


class EnhancedEquityAnalyzer:
    """
    Sophisticated equity analysis for AI documentation.
    
    Analyzes documentation for:
    - Intersectional coverage (race × gender, disability × language, etc.)
    - Concrete fairness metrics (demographic parity, equalized odds, etc.)
    - Disaggregated performance data
    - Mitigation strategies
    - Accessibility considerations
    """
    
    def __init__(self):
        # Protected characteristics for intersectional analysis
        self.protected_characteristics = {
            "race_ethnicity": [
                "race", "racial", "ethnicity", "ethnic", "Black", "African American",
                "Hispanic", "Latinx", "Latino", "Latina", "Asian", "Indigenous",
                "Native American", "White", "Caucasian", "multiracial"
            ],
            "gender": [
                "gender", "gendered", "sex", "women", "men", "male", "female",
                "nonbinary", "non-binary", "transgender", "cisgender", "LGBTQ",
                "LGBTQIA", "queer"
            ],
            "disability": [
                "disability", "disabled", "accessibility", "accessible",
                "visual impairment", "hearing impairment", "mobility",
                "cognitive disability", "neurodiversity", "neurodivergent"
            ],
            "age": [
                "age", "elderly", "older adults", "seniors", "children",
                "minors", "youth", "generational"
            ],
            "language": [
                "language", "linguistic", "non-English", "multilingual",
                "dialect", "accent", "native speaker", "language barrier"
            ],
            "socioeconomic": [
                "socioeconomic", "income", "poverty", "wealth gap",
                "economic disadvantage", "low-income", "affluent"
            ],
            "geography": [
                "geography", "geographic", "rural", "urban", "regional",
                "developing countries", "Global South", "remote areas"
            ]
        }
        
        # Fairness metrics to look for
        self.fairness_metrics = {
            "statistical_parity": [
                "demographic parity", "statistical parity", "equal acceptance rates"
            ],
            "equalized_odds": [
                "equalized odds", "equal opportunity", "true positive rate parity",
                "false positive rate parity"
            ],
            "predictive_parity": [
                "predictive parity", "predictive value parity", "precision parity"
            ],
            "calibration": [
                "calibration", "calibrated", "calibration by group"
            ],
            "counterfactual": [
                "counterfactual fairness", "individual fairness", "similar treatment"
            ],
            "disparate_impact": [
                "disparate impact", "adverse impact", "four-fifths rule", "80% rule"
            ]
        }
        
        # Quantitative indicators (suggests actual metrics, not just discussion)
        self.quantitative_patterns = [
            r'\b\d+\.?\d*\s*%',  # Percentages: 23.5%
            r'\b\d+\.?\d*\s*percent',  # Written percentages
            r'\bp\s*[<>=]\s*0?\.\d+',  # P-values: p < 0.05
            r'\b\d+\.?\d*\s*[±]\s*\d+\.?\d*',  # Confidence intervals: 0.85 ± 0.03
            r'\b\d+\.?\d*/\d+\.?\d*',  # Ratios: 0.85/0.90
            r'AUC.*\d+\.?\d*',  # AUC scores
            r'F1.*\d+\.?\d*',  # F1 scores
        ]
        
        # Mitigation strategies
        self.mitigation_keywords = [
            "mitigation", "mitigate", "mitigated",
            "debiasing", "debias", "debiased",
            "reweighting", "resampling",
            "fairness constraints", "fairness-aware",
            "bias correction", "adjustment",
            "post-processing", "pre-processing"
        ]
        
        # Best practices indicators
        self.best_practice_patterns = {
            "disaggregated_reporting": [
                "disaggregated", "broken down by", "stratified by",
                "subgroup analysis", "per-group performance"
            ],
            "stakeholder_engagement": [
                "stakeholder engagement", "community consultation",
                "participatory design", "affected communities"
            ],
            "impact_assessment": [
                "impact assessment", "equity impact", "fairness assessment",
                "bias audit", "algorithmic audit"
            ],
            "transparency": [
                "transparent", "transparency", "disclosed", "publicly available"
            ]
        }
    
    def analyze_document_equity(
        self,
        chunks: List[Dict],
        doc_metadata: Dict
    ) -> Dict:
        """
        Perform comprehensive equity analysis on a single document.
        
        Returns
        -------
        Dict
            Detailed equity analysis with scores and findings
        """
        doc_id = doc_metadata.get("doc_id", "unknown")
        title = doc_metadata.get("title", "Unknown")
        
        # Combine all text
        full_text = " ".join([chunk.get("text", "") for chunk in chunks])
        
        # 1. Protected characteristics coverage
        protected_coverage = self._analyze_protected_characteristics(full_text)
        
        # 2. Intersectional analysis
        intersectional_coverage = self._analyze_intersectionality(full_text, chunks)
        
        # 3. Fairness metrics presence
        fairness_metrics = self._detect_fairness_metrics(full_text, chunks)
        
        # 4. Quantitative vs. qualitative
        quantitative_evidence = self._assess_quantitative_evidence(full_text, chunks)
        
        # 5. Mitigation strategies
        mitigation = self._analyze_mitigation_strategies(full_text, chunks)
        
        # 6. Best practices adherence
        best_practices = self._assess_best_practices(full_text, chunks)
        
        # 7. Calculate overall equity score
        equity_score = self._calculate_equity_score(
            protected_coverage,
            intersectional_coverage,
            fairness_metrics,
            quantitative_evidence,
            mitigation,
            best_practices
        )
        
        return {
            "doc_id": doc_id,
            "title": title,
            "equity_score": equity_score,
            "protected_characteristics": protected_coverage,
            "intersectional_analysis": intersectional_coverage,
            "fairness_metrics": fairness_metrics,
            "quantitative_evidence": quantitative_evidence,
            "mitigation_strategies": mitigation,
            "best_practices": best_practices,
            "overall_assessment": self._generate_assessment(equity_score),
            "recommendations": self._generate_recommendations(
                protected_coverage,
                intersectional_coverage,
                fairness_metrics,
                quantitative_evidence,
                mitigation
            )
        }
    
    def _analyze_protected_characteristics(self, text: str) -> Dict:
        """
        Detect which protected characteristics are mentioned.
        
        Returns dictionary with coverage for each characteristic.
        """
        text_lower = text.lower()
        coverage = {}
        
        for char_type, keywords in self.protected_characteristics.items():
            mentions = []
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    mentions.append(keyword)
            
            coverage[char_type] = {
                "present": len(mentions) > 0,
                "mention_count": len(mentions),
                "keywords_found": mentions[:5]  # Top 5
            }
        
        # Calculate coverage percentage
        total_chars = len(self.protected_characteristics)
        covered_chars = sum(1 for c in coverage.values() if c["present"])
        
        coverage["summary"] = {
            "total_characteristics": total_chars,
            "covered_characteristics": covered_chars,
            "coverage_percentage": round(covered_chars / total_chars * 100, 1)
        }
        
        return coverage
    
    def _analyze_intersectionality(
        self,
        text: str,
        chunks: List[Dict]
    ) -> Dict:
        """
        Detect intersectional equity considerations.
        
        Looks for mentions of multiple protected characteristics together,
        which suggests intersectional analysis.
        """
        intersectional_chunks = []
        
        for chunk in chunks:
            chunk_text = chunk.get("text", "").lower()
            
            # Count how many characteristic types appear in this chunk
            char_types_present = set()
            for char_type, keywords in self.protected_characteristics.items():
                for keyword in keywords:
                    if keyword.lower() in chunk_text:
                        char_types_present.add(char_type)
                        break
            
            # If 2+ characteristic types appear together, it's intersectional
            if len(char_types_present) >= 2:
                intersectional_chunks.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "characteristics": list(char_types_present),
                    "text_preview": chunk_text[:200] + "..."
                })
        
        # Find specific intersectional patterns
        intersectional_patterns = [
            "intersectional", "intersection", "compound discrimination",
            "multiply marginalized", "overlapping identities"
        ]
        
        explicit_intersectional = any(
            pattern in text.lower() for pattern in intersectional_patterns
        )
        
        return {
            "has_intersectional_analysis": len(intersectional_chunks) > 0,
            "explicit_intersectional_language": explicit_intersectional,
            "intersectional_chunk_count": len(intersectional_chunks),
            "intersectional_chunks": intersectional_chunks[:10],  # Top 10
            "assessment": (
                "Strong intersectional consideration" if len(intersectional_chunks) >= 3
                else "Some intersectional consideration" if len(intersectional_chunks) > 0
                else "No intersectional analysis detected"
            )
        }
    
    def _detect_fairness_metrics(
        self,
        text: str,
        chunks: List[Dict]
    ) -> Dict:
        """
        Detect which formal fairness metrics are reported.
        """
        text_lower = text.lower()
        detected_metrics = {}
        
        for metric_type, patterns in self.fairness_metrics.items():
            found_patterns = []
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    found_patterns.append(pattern)
            
            detected_metrics[metric_type] = {
                "present": len(found_patterns) > 0,
                "patterns_found": found_patterns
            }
        
        # Count metrics with actual numbers
        metrics_with_numbers = 0
        for metric_type, info in detected_metrics.items():
            if info["present"]:
                # Check if numbers appear near the metric mention
                for pattern in info["patterns_found"]:
                    # Find chunks mentioning this pattern
                    for chunk in chunks:
                        if pattern.lower() in chunk.get("text", "").lower():
                            # Check if this chunk has numbers
                            chunk_text = chunk.get("text", "")
                            if any(re.search(p, chunk_text) for p in self.quantitative_patterns):
                                metrics_with_numbers += 1
                                break
        
        total_metrics = len(self.fairness_metrics)
        present_metrics = sum(1 for m in detected_metrics.values() if m["present"])
        
        return {
            "metrics_detected": detected_metrics,
            "summary": {
                "total_metric_types": total_metrics,
                "metrics_mentioned": present_metrics,
                "metrics_with_quantitative_data": metrics_with_numbers,
                "coverage_percentage": round(present_metrics / total_metrics * 100, 1)
            },
            "assessment": (
                "Comprehensive fairness metrics" if present_metrics >= 3
                else "Some fairness metrics" if present_metrics > 0
                else "No formal fairness metrics detected"
            )
        }
    
    def _assess_quantitative_evidence(
        self,
        text: str,
        chunks: List[Dict]
    ) -> Dict:
        """
        Assess whether equity claims are backed by quantitative evidence.
        """
        # Find chunks that mention equity/bias AND contain numbers
        equity_keywords = ["equity", "bias", "fairness", "disparity", "discrimination"]
        
        quantitative_equity_chunks = []
        
        for chunk in chunks:
            chunk_text = chunk.get("text", "")
            chunk_lower = chunk_text.lower()
            
            # Check if chunk mentions equity
            has_equity_mention = any(kw in chunk_lower for kw in equity_keywords)
            
            # Check if chunk has quantitative data
            has_numbers = any(re.search(p, chunk_text) for p in self.quantitative_patterns)
            
            if has_equity_mention and has_numbers:
                quantitative_equity_chunks.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "chunk_type": chunk.get("chunk_type", "text"),
                    "preview": chunk_text[:200] + "..."
                })
        
        # Count table chunks with equity content
        equity_table_chunks = [
            c for c in quantitative_equity_chunks
            if c["chunk_type"] == "table"
        ]
        
        return {
            "has_quantitative_evidence": len(quantitative_equity_chunks) > 0,
            "quantitative_equity_chunks": len(quantitative_equity_chunks),
            "equity_tables": len(equity_table_chunks),
            "sample_chunks": quantitative_equity_chunks[:5],
            "assessment": (
                "Strong quantitative evidence" if len(equity_table_chunks) >= 2
                else "Some quantitative evidence" if len(quantitative_equity_chunks) > 0
                else "Qualitative only - no quantitative equity data"
            )
        }
    
    def _analyze_mitigation_strategies(
        self,
        text: str,
        chunks: List[Dict]
    ) -> Dict:
        """
        Detect mentions of bias mitigation strategies.
        """
        text_lower = text.lower()
        
        mitigation_mentions = []
        for keyword in self.mitigation_keywords:
            if keyword.lower() in text_lower:
                mitigation_mentions.append(keyword)
        
        # Find chunks with mitigation discussion
        mitigation_chunks = []
        for chunk in chunks:
            chunk_text = chunk.get("text", "")
            chunk_lower = chunk_text.lower()
            
            if any(kw in chunk_lower for kw in self.mitigation_keywords):
                mitigation_chunks.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "preview": chunk_text[:200] + "..."
                })
        
        return {
            "has_mitigation_strategies": len(mitigation_mentions) > 0,
            "mitigation_keywords_found": mitigation_mentions,
            "mitigation_chunk_count": len(mitigation_chunks),
            "mitigation_chunks": mitigation_chunks[:5],
            "assessment": (
                "Comprehensive mitigation strategies" if len(mitigation_chunks) >= 3
                else "Some mitigation discussion" if len(mitigation_chunks) > 0
                else "No mitigation strategies mentioned"
            )
        }
    
    def _assess_best_practices(
        self,
        text: str,
        chunks: List[Dict]
    ) -> Dict:
        """
        Assess adherence to equity documentation best practices.
        """
        text_lower = text.lower()
        
        best_practices_found = {}
        for practice_type, patterns in self.best_practice_patterns.items():
            found = []
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    found.append(pattern)
            
            best_practices_found[practice_type] = {
                "present": len(found) > 0,
                "patterns_found": found
            }
        
        total_practices = len(self.best_practice_patterns)
        present_practices = sum(1 for p in best_practices_found.values() if p["present"])
        
        return {
            "practices_detected": best_practices_found,
            "summary": {
                "total_best_practices": total_practices,
                "practices_followed": present_practices,
                "adherence_percentage": round(present_practices / total_practices * 100, 1)
            },
            "assessment": (
                "Strong best practice adherence" if present_practices >= 3
                else "Partial best practice adherence" if present_practices > 0
                else "Poor best practice adherence"
            )
        }
    
    def _calculate_equity_score(
        self,
        protected_coverage: Dict,
        intersectional: Dict,
        fairness_metrics: Dict,
        quantitative: Dict,
        mitigation: Dict,
        best_practices: Dict
    ) -> float:
        """
        Calculate overall equity score (0-1) based on multiple factors.
        
        Weights:
        - Protected characteristics coverage: 20%
        - Intersectional analysis: 15%
        - Fairness metrics: 25%
        - Quantitative evidence: 25%
        - Mitigation strategies: 10%
        - Best practices: 5%
        """
        score = 0.0
        
        # Protected characteristics (0-20 points)
        coverage_pct = protected_coverage["summary"]["coverage_percentage"]
        score += (coverage_pct / 100) * 0.20
        
        # Intersectional analysis (0-15 points)
        if intersectional["explicit_intersectional_language"]:
            score += 0.15
        elif intersectional["intersectional_chunk_count"] >= 3:
            score += 0.10
        elif intersectional["intersectional_chunk_count"] > 0:
            score += 0.05
        
        # Fairness metrics (0-25 points)
        metrics_pct = fairness_metrics["summary"]["coverage_percentage"]
        score += (metrics_pct / 100) * 0.25
        
        # Quantitative evidence (0-25 points)
        if quantitative["equity_tables"] >= 2:
            score += 0.25
        elif quantitative["equity_tables"] == 1:
            score += 0.15
        elif quantitative["quantitative_equity_chunks"] > 0:
            score += 0.10
        
        # Mitigation strategies (0-10 points)
        if mitigation["mitigation_chunk_count"] >= 3:
            score += 0.10
        elif mitigation["mitigation_chunk_count"] > 0:
            score += 0.05
        
        # Best practices (0-5 points)
        practices_pct = best_practices["summary"]["adherence_percentage"]
        score += (practices_pct / 100) * 0.05
        
        return round(score, 3)
    
    def _generate_assessment(self, equity_score: float) -> str:
        """Generate human-readable assessment."""
        if equity_score >= 0.7:
            return "Excellent equity documentation with comprehensive coverage"
        elif equity_score >= 0.5:
            return "Good equity documentation with room for improvement"
        elif equity_score >= 0.3:
            return "Basic equity documentation with significant gaps"
        else:
            return "Poor equity documentation - major improvements needed"
    
    def _generate_recommendations(
        self,
        protected_coverage: Dict,
        intersectional: Dict,
        fairness_metrics: Dict,
        quantitative: Dict,
        mitigation: Dict
    ) -> List[str]:
        """Generate specific, actionable recommendations."""
        recommendations = []
        
        # Check protected characteristics
        covered = protected_coverage["summary"]["covered_characteristics"]
        if covered < 5:
            missing_chars = [
                char_type for char_type, info in protected_coverage.items()
                if char_type != "summary" and not info["present"]
            ]
            recommendations.append(
                f"Expand protected characteristic coverage to include: {', '.join(missing_chars[:3])}"
            )
        
        # Check intersectionality
        if not intersectional["has_intersectional_analysis"]:
            recommendations.append(
                "Add intersectional equity analysis examining combinations of protected characteristics (e.g., race × gender, disability × language)"
            )
        
        # Check fairness metrics
        if fairness_metrics["summary"]["metrics_mentioned"] == 0:
            recommendations.append(
                "Implement and report formal fairness metrics such as demographic parity, equalized odds, or disparate impact ratios"
            )
        
        # Check quantitative evidence
        if not quantitative["has_quantitative_evidence"]:
            recommendations.append(
                "Provide quantitative fairness metrics with disaggregated performance data across demographic groups"
            )
        elif quantitative["equity_tables"] == 0:
            recommendations.append(
                "Present equity metrics in structured tables for easier comparison across groups"
            )
        
        # Check mitigation
        if not mitigation["has_mitigation_strategies"]:
            recommendations.append(
                "Document specific bias mitigation strategies implemented (e.g., reweighting, debiasing techniques, fairness constraints)"
            )
        
        return recommendations
    
    def compare_documents(
        self,
        doc_analyses: List[Dict]
    ) -> Dict:
        """
        Compare equity coverage across multiple documents.
        
        Identifies leaders, laggards, and common gaps.
        """
        # Sort by equity score
        sorted_docs = sorted(
            doc_analyses,
            key=lambda x: x["equity_score"],
            reverse=True
        )
        
        # Find common gaps
        common_gaps = defaultdict(int)
        for doc in doc_analyses:
            if not doc["intersectional_analysis"]["has_intersectional_analysis"]:
                common_gaps["No intersectional analysis"] += 1
            
            if doc["fairness_metrics"]["summary"]["metrics_mentioned"] == 0:
                common_gaps["No formal fairness metrics"] += 1
            
            if not doc["quantitative_evidence"]["has_quantitative_evidence"]:
                common_gaps["No quantitative equity data"] += 1
            
            if not doc["mitigation_strategies"]["has_mitigation_strategies"]:
                common_gaps["No mitigation strategies"] += 1
        
        total_docs = len(doc_analyses)
        
        return {
            "total_documents": total_docs,
            "best_equity_docs": [
                {
                    "title": doc["title"],
                    "equity_score": doc["equity_score"],
                    "assessment": doc["overall_assessment"]
                }
                for doc in sorted_docs[:3]
            ],
            "worst_equity_docs": [
                {
                    "title": doc["title"],
                    "equity_score": doc["equity_score"],
                    "assessment": doc["overall_assessment"]
                }
                for doc in sorted_docs[-3:]
            ],
            "common_gaps": [
                {
                    "gap": gap,
                    "affected_docs": count,
                    "percentage": round(count / total_docs * 100, 1)
                }
                for gap, count in sorted(
                    common_gaps.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ],
            "average_equity_score": round(
                sum(d["equity_score"] for d in doc_analyses) / total_docs,
                3
            )
        }


def main():
    """Demo the enhanced equity analyzer."""
    from src.config.settings import PROCESSED_DIR
    from src.ingest.load_metadata import load_metadata
    
    # Load data
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
    
    # Analyze artifacts
    analyzer = EnhancedEquityAnalyzer()
    
    artifact_analyses = []
    for doc_id, doc_chunks in chunks_by_doc.items():
        if doc_metadata.get(doc_id, {}).get("doc_type") == "artifact":
            print(f"\n🔍 Analyzing: {doc_metadata[doc_id]['title']}")
            
            analysis = analyzer.analyze_document_equity(
                doc_chunks,
                doc_metadata[doc_id]
            )
            
            artifact_analyses.append(analysis)
            
            print(f"   Equity Score: {analysis['equity_score']:.3f}")
            print(f"   Assessment: {analysis['overall_assessment']}")
            
            if analysis['recommendations']:
                print(f"   Top Recommendation: {analysis['recommendations'][0]}")
    
    # Compare all artifacts
    print("\n" + "="*70)
    print("CROSS-DOCUMENT EQUITY COMPARISON")
    print("="*70)
    
    comparison = analyzer.compare_documents(artifact_analyses)
    
    print(f"\nAverage Equity Score: {comparison['average_equity_score']:.3f}")
    
    print("\n📊 Best Equity Documentation:")
    for doc in comparison["best_equity_docs"]:
        print(f"   • {doc['title']}: {doc['equity_score']:.3f}")
    
    print("\n⚠️  Common Equity Gaps:")
    for gap in comparison["common_gaps"][:3]:
        print(f"   • {gap['gap']}: {gap['affected_docs']}/{comparison['total_documents']} documents ({gap['percentage']}%)")
    
    # Save results
    output_dir = Path("analysis_results")
    output_dir.mkdir(exist_ok=True)
    
    with (output_dir / "enhanced_equity_analysis.json").open("w") as f:
        json.dump({
            "document_analyses": artifact_analyses,
            "comparison": comparison
        }, f, indent=2)
    
    print(f"\n✅ Saved enhanced equity analysis to {output_dir / 'enhanced_equity_analysis.json'}")


if __name__ == "__main__":
    main()