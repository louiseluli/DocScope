"""
Content Quality Detection for AI Documentation.

Multi-method analyzer to distinguish promotional language from substantive
technical content. Addresses the challenge question: "How do you disincentivize
promotional language (PR speak) in technical documentation?"

Methods:
1. Linguistic Pattern Analysis - Detects marketing language patterns
2. Information Density Measurement - Facts per sentence ratio
3. Specificity Scoring - Vague claims vs. concrete metrics
4. Evidence-Based Assessment - Presence of quantitative data
5. Comparative Quality Ranking - Cross-document benchmarking
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re
from collections import Counter
import statistics


@dataclass
class QualityScore:
    """Comprehensive quality score for a document or chunk."""
    overall_score: float  # 0.0 to 1.0
    substantive_score: float  # Higher = more technical content
    promotional_score: float  # Higher = more PR speak
    specificity_score: float  # Higher = more concrete metrics
    information_density: float  # Facts per 100 words
    evidence_based_score: float  # Quantitative data presence
    
    quality_tier: str  # "excellent", "good", "fair", "poor"
    flags: List[str]  # Specific quality issues
    recommendations: List[str]  # How to improve
    

class ContentQualityDetector:
    """
    Sophisticated content quality analyzer for AI documentation.
    
    Uses multiple complementary methods to assess documentation quality
    and distinguish promotional language from substantive technical content.
    """
    
    # Promotional language patterns (marketing speak)
    PROMOTIONAL_PATTERNS = [
        # Superlatives without evidence
        r'\b(best|leading|premier|top|revolutionary|breakthrough|cutting-edge|state-of-the-art|world-class|industry-leading)\b',
        r'\b(unprecedented|unparalleled|unmatched|superior|advanced|innovative|transformative|groundbreaking)\b',
        
        # Marketing buzzwords
        r'\b(game-changer|disruptive|next-generation|future-proof|enterprise-grade|mission-critical)\b',
        r'\b(seamless|robust|powerful|flexible|scalable|reliable|efficient)\b(?! benchmark| test| evaluation)',
        
        # Vague claims
        r'\b(significantly|substantially|dramatically|greatly|highly|extremely|exceptionally)\b(?! \d)',
        r'\b(various|numerous|many|several|multiple)\b(?! \d)',
        
        # Marketing phrases
        r'\b(we are proud|we are excited|we are pleased|delighted to announce)\b',
        r'\b(designed to|built to|tailored to|optimized for)\b(?! meet .* benchmark| achieve .* performance)',
        
        # Empty promises
        r'\b(unlimited|endless|infinite|effortless|instant|automatic)\b(?! in theory| in principle)',
    ]
    
    # Substantive technical patterns (real content)
    SUBSTANTIVE_PATTERNS = [
        # Quantitative metrics
        r'\b\d+\.?\d*\s*(GB|TB|MB|KB|parameters?|tokens?|layers?|heads?|dimensions?)\b',
        r'\b\d+\.?\d*\s*(%|percent|percentage|accuracy|precision|recall|F1)\b',
        r'\bscored?\s+\d+\.?\d*\b',
        r'\b(MMLU|HumanEval|GSM8K|HellaSwag|ARC|BLEU|ROUGE|METEOR)\b',
        
        # Specific methodologies
        r'\b(evaluated on|tested on|measured using|calculated via|assessed through)\b',
        r'\b(benchmark|dataset|corpus|evaluation suite)\b.*\b\d',
        r'\b(red team|adversarial testing|ablation study|A/B test)\b',
        
        # Concrete limitations
        r'\b(does not support|cannot handle|limited to|restricted to|fails when)\b',
        r'\b(known limitation|edge case|failure mode|out-of-scope)\b',
        
        # Evidence-based statements
        r'\b(as shown in|according to|results indicate|data shows|experiments demonstrate)\b',
        r'\b(Table \d+|Figure \d+|Section \d+|Appendix [A-Z])\b',
        
        # Specific technical details
        r'\b(architecture|algorithm|model|training|fine-tuning|inference)\b.*\b(described|implemented|configured|optimized)\b',
        r'\b(hyperparameter|learning rate|batch size|epoch|iteration)\b',
    ]
    
    # Vagueness indicators
    VAGUENESS_PATTERNS = [
        r'\b(thing|stuff|various things|and so on|etc\.)\b',
        r'\b(kind of|sort of|type of|relatively|fairly|quite|rather)\b',
        r'\b(generally|typically|usually|often|sometimes|may|might|could)\b(?! be (measured|quantified|evaluated))',
        r'\b(approximately|roughly|around|about)\b(?! \d)',
    ]
    
    # Specific metrics/evidence indicators
    SPECIFICITY_PATTERNS = [
        # Numbers with context
        r'\b\d+\.?\d*\s*[A-Za-z]+',  # "95.3 accuracy", "100M parameters"
        r'\b\d{1,3}(,\d{3})*(\.\d+)?\b',  # Numbers with commas
        
        # Exact dates/versions
        r'\b(20\d{2}|v\d+\.\d+|version \d+)\b',
        
        # Specific comparisons
        r'\b(compared to|versus|vs\.|relative to|against)\b.*\b\d',
        r'\b(\d+%\s*(better|worse|higher|lower|more|less|faster|slower))\b',
        
        # Concrete examples
        r'\b(for example|for instance|specifically|namely|such as)\b.*\b[A-Z]',
    ]
    
    def __init__(self):
        """Initialize the quality detector with compiled patterns."""
        self.promotional_regex = [re.compile(p, re.IGNORECASE) for p in self.PROMOTIONAL_PATTERNS]
        self.substantive_regex = [re.compile(p, re.IGNORECASE) for p in self.SUBSTANTIVE_PATTERNS]
        self.vagueness_regex = [re.compile(p, re.IGNORECASE) for p in self.VAGUENESS_PATTERNS]
        self.specificity_regex = [re.compile(p, re.IGNORECASE) for p in self.SPECIFICITY_PATTERNS]
    
    def analyze_text(self, text: str) -> QualityScore:
        """
        Comprehensive quality analysis of a text chunk.
        
        Parameters
        ----------
        text : str
            Text to analyze (chunk, paragraph, or full document)
        
        Returns
        -------
        QualityScore
            Multi-dimensional quality assessment
        """
        if not text or len(text.strip()) < 20:
            return self._empty_score()
        
        # Method 1: Pattern-based scoring
        promotional_score = self._calculate_promotional_score(text)
        substantive_score = self._calculate_substantive_score(text)
        
        # Method 2: Information density
        info_density = self._calculate_information_density(text)
        
        # Method 3: Specificity vs. vagueness
        specificity_score = self._calculate_specificity_score(text)
        
        # Method 4: Evidence-based content
        evidence_score = self._calculate_evidence_score(text)
        
        # Overall score (weighted combination)
        overall_score = self._calculate_overall_score(
            substantive_score, promotional_score, specificity_score, 
            info_density, evidence_score
        )
        
        # Quality tier
        quality_tier = self._assign_quality_tier(overall_score)
        
        # Identify specific issues
        flags = self._identify_quality_flags(
            text, promotional_score, substantive_score, specificity_score
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(flags)
        
        return QualityScore(
            overall_score=round(overall_score, 3),
            substantive_score=round(substantive_score, 3),
            promotional_score=round(promotional_score, 3),
            specificity_score=round(specificity_score, 3),
            information_density=round(info_density, 2),
            evidence_based_score=round(evidence_score, 3),
            quality_tier=quality_tier,
            flags=flags,
            recommendations=recommendations
        )
    
    def _calculate_promotional_score(self, text: str) -> float:
        """
        Calculate promotional language score (0.0 = none, 1.0 = heavy marketing).
        """
        text_lower = text.lower()
        word_count = len(text.split())
        
        promotional_matches = 0
        for regex in self.promotional_regex:
            matches = regex.findall(text_lower)
            promotional_matches += len(matches)
        
        # Normalize by text length
        if word_count == 0:
            return 0.0
        
        # Score increases with promotional density
        score = min(1.0, (promotional_matches / word_count) * 10)
        return score
    
    def _calculate_substantive_score(self, text: str) -> float:
        """
        Calculate substantive technical content score (0.0 = none, 1.0 = highly technical).
        """
        text_lower = text.lower()
        word_count = len(text.split())
        
        substantive_matches = 0
        for regex in self.substantive_regex:
            matches = regex.findall(text_lower)
            substantive_matches += len(matches)
        
        # Normalize by text length
        if word_count == 0:
            return 0.0
        
        # Score increases with technical density
        score = min(1.0, (substantive_matches / word_count) * 5)
        return score
    
    def _calculate_information_density(self, text: str) -> float:
        """
        Calculate information density (facts per 100 words).
        
        Facts include: numbers, specific terms, citations, technical jargon.
        """
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        # Count factual elements
        numbers = len(re.findall(r'\b\d+\.?\d*', text))
        technical_terms = len(re.findall(r'\b[A-Z]{2,}|[a-z]+\d+', text))  # Acronyms, versions
        citations = len(re.findall(r'\b(Table|Figure|Section|Appendix|et al\.)\b', text, re.IGNORECASE))
        
        total_facts = numbers + technical_terms + citations
        
        # Facts per 100 words
        density = (total_facts / word_count) * 100
        return density
    
    def _calculate_specificity_score(self, text: str) -> float:
        """
        Calculate specificity score (concrete metrics vs. vague claims).
        """
        word_count = len(text.split())
        if word_count == 0:
            return 0.0
        
        # Count specific elements
        specific_matches = 0
        for regex in self.specificity_regex:
            matches = regex.findall(text)
            specific_matches += len(matches)
        
        # Count vague elements
        vague_matches = 0
        for regex in self.vagueness_regex:
            matches = regex.findall(text.lower())
            vague_matches += len(matches)
        
        # Specificity score balances specific vs. vague
        if specific_matches + vague_matches == 0:
            return 0.5  # Neutral
        
        specificity = specific_matches / (specific_matches + vague_matches)
        return specificity
    
    def _calculate_evidence_score(self, text: str) -> float:
        """
        Calculate evidence-based content score (presence of quantitative data, citations).
        """
        indicators = 0
        
        # Has numbers
        if re.search(r'\b\d+\.?\d*', text):
            indicators += 1
        
        # Has tables/figures references
        if re.search(r'\b(Table|Figure|Section|Appendix)\s*\d+', text, re.IGNORECASE):
            indicators += 1
        
        # Has benchmark names
        if re.search(r'\b(MMLU|HumanEval|GSM8K|HellaSwag|ARC|benchmark)\b', text, re.IGNORECASE):
            indicators += 1
        
        # Has evaluation language
        if re.search(r'\b(evaluated|tested|measured|assessed|scored)\b', text, re.IGNORECASE):
            indicators += 1
        
        # Has comparative data
        if re.search(r'\b(compared to|vs\.|versus|against|relative to)\b', text, re.IGNORECASE):
            indicators += 1
        
        # Score is proportion of indicators present
        evidence_score = indicators / 5.0
        return evidence_score
    
    def _calculate_overall_score(
        self, 
        substantive: float, 
        promotional: float, 
        specificity: float, 
        info_density: float, 
        evidence: float
    ) -> float:
        """
        Calculate weighted overall quality score.
        
        Higher substantive, specificity, density, evidence = higher quality
        Higher promotional = lower quality
        """
        # Normalize information density to 0-1 range (assume 20 facts/100 words is excellent)
        normalized_density = min(1.0, info_density / 20.0)
        
        # Weighted combination
        quality = (
            0.30 * substantive +           # Technical content weight
            0.20 * (1.0 - promotional) +   # Penalize marketing speak
            0.20 * specificity +           # Reward concrete metrics
            0.15 * normalized_density +    # Reward information density
            0.15 * evidence                # Reward evidence-based claims
        )
        
        return quality
    
    def _assign_quality_tier(self, overall_score: float) -> str:
        """Assign human-readable quality tier."""
        if overall_score >= 0.7:
            return "excellent"
        elif overall_score >= 0.5:
            return "good"
        elif overall_score >= 0.3:
            return "fair"
        else:
            return "poor"
    
    def _identify_quality_flags(
        self, 
        text: str, 
        promotional: float, 
        substantive: float, 
        specificity: float
    ) -> List[str]:
        """Identify specific quality issues."""
        flags = []
        
        if promotional > 0.3:
            flags.append("high_promotional_language")
        
        if substantive < 0.2:
            flags.append("low_technical_content")
        
        if specificity < 0.3:
            flags.append("vague_claims_without_metrics")
        
        # Check for specific problematic patterns
        if re.search(r'\b(best|leading|revolutionary|unprecedented)\b', text, re.IGNORECASE):
            if not re.search(r'\b\d+\.?\d*', text):
                flags.append("superlatives_without_data")
        
        if re.search(r'\b(significantly|substantially|dramatically)\b', text, re.IGNORECASE):
            if not re.search(r'\b\d+\.?\d*\s*%', text):
                flags.append("qualitative_claims_without_quantification")
        
        if len(re.findall(r'\b(various|numerous|many|several)\b', text, re.IGNORECASE)) > 2:
            flags.append("excessive_vagueness")
        
        return flags
    
    def _generate_recommendations(self, flags: List[str]) -> List[str]:
        """Generate actionable recommendations to improve quality."""
        recommendations = []
        
        flag_to_recommendation = {
            "high_promotional_language": "Replace marketing language with specific technical details and metrics",
            "low_technical_content": "Include concrete methodologies, benchmarks, and performance data",
            "vague_claims_without_metrics": "Quantify claims with specific numbers, percentages, or benchmark scores",
            "superlatives_without_data": "Support superlative claims with comparative data or third-party evaluations",
            "qualitative_claims_without_quantification": "Provide specific percentage improvements or numerical comparisons",
            "excessive_vagueness": "Replace vague terms (various, numerous) with exact counts or ranges"
        }
        
        for flag in flags:
            if flag in flag_to_recommendation:
                recommendations.append(flag_to_recommendation[flag])
        
        if not recommendations:
            recommendations.append("Documentation quality is good - maintain current level of specificity and evidence")
        
        return recommendations
    
    def _empty_score(self) -> QualityScore:
        """Return empty score for invalid input."""
        return QualityScore(
            overall_score=0.0,
            substantive_score=0.0,
            promotional_score=0.0,
            specificity_score=0.0,
            information_density=0.0,
            evidence_based_score=0.0,
            quality_tier="insufficient_data",
            flags=["text_too_short"],
            recommendations=["Provide more content for quality analysis"]
        )
    
    def analyze_document(self, chunks: List[Dict]) -> Dict:
        """
        Analyze quality across all chunks of a document.
        
        Parameters
        ----------
        chunks : List[Dict]
            Document chunks with 'text' field
        
        Returns
        -------
        Dict
            Aggregated quality analysis with per-chunk and document-level scores
        """
        if not chunks:
            return {"error": "No chunks provided"}
        
        chunk_scores = []
        for chunk in chunks:
            text = chunk.get("text", "")
            score = self.analyze_text(text)
            chunk_scores.append(score)
        
        # Aggregate statistics
        overall_scores = [s.overall_score for s in chunk_scores]
        substantive_scores = [s.substantive_score for s in chunk_scores]
        promotional_scores = [s.promotional_score for s in chunk_scores]
        
        # Identify problematic chunks
        poor_quality_chunks = [
            {"chunk_id": chunks[i].get("chunk_id"), "score": s.overall_score, "flags": s.flags}
            for i, s in enumerate(chunk_scores)
            if s.quality_tier in ["poor", "fair"]
        ]
        
        # Count flag frequency
        all_flags = []
        for s in chunk_scores:
            all_flags.extend(s.flags)
        flag_counts = Counter(all_flags)
        
        return {
            "document_level": {
                "mean_quality_score": round(statistics.mean(overall_scores), 3),
                "median_quality_score": round(statistics.median(overall_scores), 3),
                "quality_std_dev": round(statistics.stdev(overall_scores), 3) if len(overall_scores) > 1 else 0.0,
                "mean_substantive_score": round(statistics.mean(substantive_scores), 3),
                "mean_promotional_score": round(statistics.mean(promotional_scores), 3),
                "chunks_analyzed": len(chunks),
            },
            "quality_distribution": {
                "excellent": sum(1 for s in chunk_scores if s.quality_tier == "excellent"),
                "good": sum(1 for s in chunk_scores if s.quality_tier == "good"),
                "fair": sum(1 for s in chunk_scores if s.quality_tier == "fair"),
                "poor": sum(1 for s in chunk_scores if s.quality_tier == "poor"),
            },
            "common_issues": [
                {"flag": flag, "frequency": count, "affected_chunks": count}
                for flag, count in flag_counts.most_common(5)
            ],
            "poor_quality_chunks": poor_quality_chunks[:5],  # Top 5 worst
            "recommendations": self._generate_document_recommendations(chunk_scores, flag_counts)
        }
    
    def _generate_document_recommendations(
        self, 
        chunk_scores: List[QualityScore], 
        flag_counts: Counter
    ) -> List[str]:
        """Generate document-level quality recommendations."""
        recommendations = []
        
        # Check overall quality
        mean_quality = statistics.mean([s.overall_score for s in chunk_scores])
        
        if mean_quality < 0.4:
            recommendations.append(
                "CRITICAL: Document has low overall quality. Increase technical depth and reduce promotional language."
            )
        
        # Check promotional language prevalence
        mean_promo = statistics.mean([s.promotional_score for s in chunk_scores])
        if mean_promo > 0.3:
            recommendations.append(
                "HIGH PROMOTIONAL LANGUAGE: Replace marketing claims with verifiable technical specifications."
            )
        
        # Check most common issues
        if flag_counts:
            top_flag = flag_counts.most_common(1)[0]
            if top_flag[1] > len(chunk_scores) * 0.3:  # Affects >30% of chunks
                recommendations.append(
                    f"SYSTEMATIC ISSUE: '{top_flag[0]}' affects {top_flag[1]} chunks. Address this consistently."
                )
        
        # Check for missing quantitative data
        quant_scores = [s.evidence_based_score for s in chunk_scores]
        if statistics.mean(quant_scores) < 0.3:
            recommendations.append(
                "INSUFFICIENT EVIDENCE: Add quantitative benchmarks, performance metrics, and evaluation results."
            )
        
        return recommendations
    
    def compare_documents(self, doc_analyses: Dict[str, Dict]) -> Dict:
        """
        Compare quality across multiple documents.
        
        Parameters
        ----------
        doc_analyses : Dict[str, Dict]
            Map from doc_id to document analysis results
        
        Returns
        -------
        Dict
            Comparative quality analysis
        """
        rankings = []
        
        for doc_id, analysis in doc_analyses.items():
            doc_level = analysis.get("document_level", {})
            rankings.append({
                "doc_id": doc_id,
                "mean_quality": doc_level.get("mean_quality_score", 0),
                "mean_substantive": doc_level.get("mean_substantive_score", 0),
                "mean_promotional": doc_level.get("mean_promotional_score", 0),
            })
        
        # Sort by quality
        rankings.sort(key=lambda x: x["mean_quality"], reverse=True)
        
        # Calculate percentiles
        qualities = [r["mean_quality"] for r in rankings]
        
        return {
            "rankings": rankings,
            "quality_statistics": {
                "best": max(qualities) if qualities else 0,
                "worst": min(qualities) if qualities else 0,
                "mean": round(statistics.mean(qualities), 3) if qualities else 0,
                "median": round(statistics.median(qualities), 3) if qualities else 0,
            },
            "insights": self._generate_comparative_insights(rankings)
        }
    
    def _generate_comparative_insights(self, rankings: List[Dict]) -> List[str]:
        """Generate insights from cross-document comparison."""
        insights = []
        
        if not rankings:
            return insights
        
        best = rankings[0]
        worst = rankings[-1]
        
        quality_gap = best["mean_quality"] - worst["mean_quality"]
        
        insights.append(
            f"Quality gap between best and worst documentation: {quality_gap:.3f}"
        )
        
        # Identify leaders in substantive content
        substantive_leader = max(rankings, key=lambda x: x["mean_substantive"])
        insights.append(
            f"Highest technical content: {substantive_leader['doc_id']} (score: {substantive_leader['mean_substantive']:.3f})"
        )
        
        # Identify most promotional
        promo_leader = max(rankings, key=lambda x: x["mean_promotional"])
        if promo_leader["mean_promotional"] > 0.3:
            insights.append(
                f"Most promotional language: {promo_leader['doc_id']} (score: {promo_leader['mean_promotional']:.3f})"
            )
        
        return insights


def main():
    """Demonstration of content quality detection."""
    detector = ContentQualityDetector()
    
    # Example 1: Promotional text
    promo_text = """
    Our revolutionary AI model is the best-in-class solution for enterprise needs.
    Leveraging cutting-edge technology, we deliver unprecedented performance that
    significantly outperforms competitors. Built with innovative architecture,
    our world-class system provides seamless integration and powerful capabilities.
    """
    
    print("="*70)
    print("EXAMPLE 1: PROMOTIONAL TEXT")
    print("="*70)
    score1 = detector.analyze_text(promo_text)
    print(f"Overall Quality: {score1.overall_score} ({score1.quality_tier})")
    print(f"Promotional Score: {score1.promotional_score}")
    print(f"Substantive Score: {score1.substantive_score}")
    print(f"Flags: {', '.join(score1.flags)}")
    print(f"\nRecommendations:")
    for rec in score1.recommendations:
        print(f"  • {rec}")
    
    # Example 2: Technical text
    tech_text = """
    The model was evaluated on MMLU achieving 87.3% accuracy. Trained on 15T tokens
    with a context window of 128K tokens using 96 attention heads across 80 layers.
    Performance on HumanEval reached 92.4% pass@1, compared to 85.2% for the baseline.
    Red teaming identified 3.2% jailbreak success rate, down from 8.7% in the previous version.
    """
    
    print("\n" + "="*70)
    print("EXAMPLE 2: TECHNICAL TEXT")
    print("="*70)
    score2 = detector.analyze_text(tech_text)
    print(f"Overall Quality: {score2.overall_score} ({score2.quality_tier})")
    print(f"Promotional Score: {score2.promotional_score}")
    print(f"Substantive Score: {score2.substantive_score}")
    print(f"Information Density: {score2.information_density} facts/100 words")
    print(f"Flags: {', '.join(score2.flags) if score2.flags else 'None - high quality'}")


if __name__ == "__main__":
    main()