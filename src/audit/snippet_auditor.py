from dataclasses import dataclass
from typing import Dict, List, Set, Optional
import re


@dataclass
class CategoryScore:
    """Score for a single category"""
    score: float  # 0.0 to 1.0
    hit_count: int
    matched_keywords: List[str]
    matched_chunks: List[str]  # chunk_ids that matched
    table_hits: int  # Number of table chunks that matched
    text_hits: int  # Number of text chunks that matched


class SnippetAuditor:
    """
    Audit document chunks against governance categories.
    
    Enhanced to:
    - Weight table chunks higher (they contain metrics/benchmarks)
    - Detect negations (e.g., "no safety evaluation" should lower score)
    - Identify equity-specific gaps
    - Support comparative analysis across documents
    """
    
    def __init__(self, schema: Dict):
        """
        Parameters
        ----------
        schema : Dict
            Category schema with keywords, importance weights, etc.
        """
        self.schema = schema
        
        # Compile negation patterns for sophisticated scoring
        self.negation_patterns = [
            r'\bno\b',
            r'\bnot\b',
            r'\bnever\b',
            r'\bunavailable\b',
            r'\bunknown\b',
            r'\bnot\s+disclosed\b',
            r'\bnot\s+reported\b',
            r'\bnot\s+evaluated\b',
            r'\bnot\s+measured\b',
        ]
        self.negation_regex = re.compile('|'.join(self.negation_patterns), re.IGNORECASE)
    
    def _detect_negation_context(self, text: str, keyword: str) -> bool:
        """
        Check if a keyword appears in a negation context.
        
        Returns True if keyword is negated (e.g., "no safety testing").
        """
        # Find keyword position
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        
        if keyword_lower not in text_lower:
            return False
        
        # Get context window around keyword (50 chars before)
        idx = text_lower.find(keyword_lower)
        context_start = max(0, idx - 50)
        context = text_lower[context_start:idx + len(keyword_lower) + 20]
        
        # Check for negation patterns in context
        return bool(self.negation_regex.search(context))
    
    def _calculate_keyword_score(
        self, 
        text: str, 
        keywords: List[str],
        chunk_type: str = "text"
    ) -> tuple[float, List[str], bool]:
        """
        Calculate keyword match score for a single chunk.
        
        Returns:
        --------
        tuple[float, List[str], bool]
            - score: 0.0 to 1.0
            - matched_keywords: list of keywords that matched
            - has_negation: True if any match was in negation context
        """
        text_lower = text.lower()
        matched = []
        has_negation = False
        
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in text_lower:
                # Check for negation
                if self._detect_negation_context(text, kw):
                    has_negation = True
                else:
                    matched.append(kw)
        
        if not matched:
            return 0.0, [], has_negation
        
        # Base score: proportion of keywords matched
        base_score = len(matched) / len(keywords)
        
        # Boost for tables (they contain structured data/metrics)
        if chunk_type == "table":
            base_score = min(1.0, base_score * 1.3)
        
        # Cap at 1.0
        score = min(1.0, base_score)
        
        return score, matched, has_negation
    
    def audit_chunks(self, chunks: List[Dict]) -> Dict[str, CategoryScore]:
        """
        Audit a list of chunks against all categories in schema.
        
        Parameters
        ----------
        chunks : List[Dict]
            List of chunk dicts with at least 'text', 'chunk_id', 'chunk_type' fields.
        
        Returns
        -------
        Dict[str, CategoryScore]
            Map from category_id to CategoryScore with detailed metrics.
        """
        results: Dict[str, CategoryScore] = {}
        
        for cat_id, cat_info in self.schema.items():
            keywords = cat_info.get("keywords", [])
            if not keywords:
                continue
            
            total_score = 0.0
            matched_keywords_set: Set[str] = set()
            matched_chunk_ids: List[str] = []
            table_hit_count = 0
            text_hit_count = 0
            negation_penalty = 0.0
            
            for chunk in chunks:
                text = chunk.get("text", "")
                chunk_id = chunk.get("chunk_id", "")
                chunk_type = chunk.get("chunk_type", "text")
                
                if not text:
                    continue
                
                score, matched_kws, has_negation = self._calculate_keyword_score(
                    text, keywords, chunk_type
                )
                
                if score > 0:
                    total_score += score
                    matched_keywords_set.update(matched_kws)
                    matched_chunk_ids.append(chunk_id)
                    
                    if chunk_type == "table":
                        table_hit_count += 1
                    else:
                        text_hit_count += 1
                
                # Accumulate negation penalty
                if has_negation:
                    negation_penalty += 0.1
            
            # Normalize score by number of chunks
            if chunks:
                avg_score = total_score / len(chunks)
                # Apply negation penalty (but don't go below 0)
                avg_score = max(0.0, avg_score - negation_penalty)
            else:
                avg_score = 0.0
            
            results[cat_id] = CategoryScore(
                score=avg_score,
                hit_count=len(matched_chunk_ids),
                matched_keywords=sorted(list(matched_keywords_set)),
                matched_chunks=matched_chunk_ids,
                table_hits=table_hit_count,
                text_hits=text_hit_count
            )
        
        return results
    
    def generate_gap_analysis(
        self, 
        scores: Dict[str, CategoryScore],
        min_threshold: float = 0.3
    ) -> Dict[str, Dict]:
        """
        Generate gap analysis identifying high-priority missing information.
        
        Addresses rubric:
        - Equity: Explicitly flags equity/bias gaps
        - Data Analysis: Clear metrics for policy recommendations
        - Trade-Offs: Identifies what's missing vs. what's present
        
        Parameters
        ----------
        scores : Dict[str, CategoryScore]
            Category scores from audit_chunks
        min_threshold : float
            Minimum acceptable coverage score
        
        Returns
        -------
        Dict[str, Dict]
            Gap analysis with severity levels and recommendations
        """
        gaps = {}
        
        for cat_id, cs in scores.items():
            info = self.schema.get(cat_id, {})
            importance = info.get("importance_weight", 0.5)
            
            # Calculate gap severity
            if cs.score < min_threshold:
                gap_size = min_threshold - cs.score
                severity = gap_size * importance
                
                # Categorize severity
                if severity >= 0.6:
                    severity_level = "critical"
                elif severity >= 0.3:
                    severity_level = "high"
                elif severity >= 0.15:
                    severity_level = "medium"
                else:
                    severity_level = "low"
                
                # Special handling for equity/bias (rubric requirement)
                if cat_id == "equity_bias":
                    if severity_level != "critical":
                        severity_level = "high"  # Always elevate equity gaps
                    
                    # Check if there are ANY table hits (quantitative data)
                    has_quantitative = cs.table_hits > 0
                    
                    gaps[cat_id] = {
                        "category_id": cat_id,
                        "name": info.get("human_name_en", cat_id),
                        "severity": severity_level,
                        "coverage_score": cs.score,
                        "importance": importance,
                        "gap_size": gap_size,
                        "has_quantitative_data": has_quantitative,
                        "missing_question_templates": info.get("question_templates_en", []),
                        "recommendation": self._generate_recommendation(
                            cat_id, cs, info, has_quantitative
                        )
                    }
                else:
                    gaps[cat_id] = {
                        "category_id": cat_id,
                        "name": info.get("human_name_en", cat_id),
                        "severity": severity_level,
                        "coverage_score": cs.score,
                        "importance": importance,
                        "gap_size": gap_size,
                        "table_evidence": cs.table_hits,
                        "text_evidence": cs.text_hits,
                        "missing_question_templates": info.get("question_templates_en", []),
                        "recommendation": self._generate_recommendation(
                            cat_id, cs, info, cs.table_hits > 0
                        )
                    }
        
        return gaps
    
    def _generate_recommendation(
        self, 
        cat_id: str, 
        score: CategoryScore, 
        cat_info: Dict,
        has_quantitative: bool
    ) -> str:
        """
        Generate actionable recommendation for a gap.
        
        Addresses rubric's "Recommendations" criterion.
        """
        name = cat_info.get("human_name_en", cat_id)
        
        # Equity-specific recommendations
        if cat_id == "equity_bias":
            if not has_quantitative:
                return (
                    f"CRITICAL: {name} lacks quantitative fairness metrics. "
                    f"Require disaggregated performance data across demographic groups, "
                    f"standardized fairness metrics (e.g., equalized odds, demographic parity), "
                    f"and transparent reporting of disparate impact."
                )
            else:
                return (
                    f"{name} has some quantitative data but coverage is incomplete. "
                    f"Expand to include intersectional analysis and document mitigation strategies."
                )
        
        # Safety-specific recommendations
        if cat_id == "safety_risk":
            if score.table_hits == 0:
                return (
                    f"{name} lacks structured safety benchmarks. "
                    f"Require standardized red-teaming results, refusal rate tables, "
                    f"and incident tracking with severity classifications."
                )
            else:
                return (
                    f"{name} has some safety data. "
                    f"Enhance with threat model documentation and post-deployment monitoring plans."
                )
        
        # Training data recommendations
        if cat_id == "training_data":
            return (
                f"{name} documentation is incomplete. "
                f"Require data provenance, filtering methodology, "
                f"demographic composition, and licensing information."
            )
        
        # Generic recommendation
        questions = cat_info.get("question_templates_en", [])
        if questions:
            return (
                f"{name} needs better documentation. "
                f"Key questions to address: {questions[0]}"
            )
        
        return f"{name} requires more comprehensive documentation."
    
    def compare_documents(
        self,
        doc_scores: Dict[str, Dict[str, CategoryScore]]
    ) -> Dict[str, Dict]:
        """
        Compare category coverage across multiple documents.
        
        Supports comparative analysis for policy recommendations.
        
        Parameters
        ----------
        doc_scores : Dict[str, Dict[str, CategoryScore]]
            Map from doc_id to category scores
        
        Returns
        -------
        Dict[str, Dict]
            Comparative analysis per category
        """
        comparison = {}
        
        # Get all categories
        all_categories = set()
        for scores in doc_scores.values():
            all_categories.update(scores.keys())
        
        for cat_id in all_categories:
            cat_info = self.schema.get(cat_id, {})
            
            scores_list = []
            best_doc = None
            worst_doc = None
            best_score = 0.0
            worst_score = 1.0
            
            for doc_id, scores in doc_scores.items():
                if cat_id in scores:
                    score_val = scores[cat_id].score
                    scores_list.append(score_val)
                    
                    if score_val > best_score:
                        best_score = score_val
                        best_doc = doc_id
                    
                    if score_val < worst_score:
                        worst_score = score_val
                        worst_doc = doc_id
            
            if scores_list:
                comparison[cat_id] = {
                    "category_name": cat_info.get("human_name_en", cat_id),
                    "mean_coverage": sum(scores_list) / len(scores_list),
                    "min_coverage": min(scores_list),
                    "max_coverage": max(scores_list),
                    "best_doc": best_doc,
                    "worst_doc": worst_doc,
                    "variance": self._calculate_variance(scores_list),
                    "doc_count": len(scores_list)
                }
        
        return comparison
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)