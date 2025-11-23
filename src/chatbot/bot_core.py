from typing import List, Dict, Optional
import json
from pathlib import Path

from src.audit.snippet_auditor import SnippetAuditor
from src.audit.category_utils import CategoryAnalyzer
from src.audit.category_schema import load_category_schema
from src.config.settings import PROCESSED_DIR

# Optional import for semantic search
try:
    from src.indexing.search import ChunkSearcher
    SEARCH_AVAILABLE = True
except (ImportError, FileNotFoundError) as e:
    SEARCH_AVAILABLE = False
    print(f"[INFO] Semantic search not available: {e}")


class DocScopeCopilot:
    """
    Main chatbot interface for AI documentation analysis.
    
    Capabilities:
    1. Answer questions about documentation frameworks
    2. Audit specific documents against governance categories
    3. Compare documentation across artifacts
    4. Generate evidence-based gap analysis
    """
    
    def __init__(self):
        """Initialize the copilot with schema, chunks, and metadata."""
        self.schema = load_category_schema()
        self.auditor = SnippetAuditor(self.schema)
        self.analyzer = CategoryAnalyzer(self.schema)
        
        # Load all chunks and metadata
        self.chunks = self._load_chunks()
        self.doc_metadata = self._load_doc_metadata()
        
        # Organize chunks by document
        self.chunks_by_doc = self._organize_chunks_by_doc()
        
        # Initialize searcher if available
        self.searcher = None
        if SEARCH_AVAILABLE:
            try:
                self.searcher = ChunkSearcher()
                print(f"[INFO] Semantic search initialized")
            except Exception as e:
                print(f"[INFO] Semantic search not initialized: {e}")
        
        print(f"[INFO] Loaded {len(self.chunks)} chunks from {len(self.doc_metadata)} documents")
        print(f"[INFO] Schema has {len(self.schema)} governance categories")
    
    def _load_chunks(self) -> List[Dict]:
        """Load all chunks from JSONL file."""
        chunks_path = PROCESSED_DIR / "chunks.jsonl"
        chunks = []
        
        if not chunks_path.exists():
            print(f"[WARN] No chunks file found at {chunks_path}")
            return chunks
        
        with chunks_path.open("r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))
        
        return chunks
    
    def _load_doc_metadata(self) -> Dict[str, Dict]:
        """Load document metadata."""
        metadata_path = PROCESSED_DIR / "doc_metadata.json"
        
        if not metadata_path.exists():
            print(f"[WARN] No metadata file found at {metadata_path}")
            return {}
        
        with metadata_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    
    def _organize_chunks_by_doc(self) -> Dict[str, List[Dict]]:
        """Organize chunks by document ID."""
        chunks_by_doc = {}
        
        for chunk in self.chunks:
            doc_id = chunk.get("doc_id")
            if doc_id not in chunks_by_doc:
                chunks_by_doc[doc_id] = []
            chunks_by_doc[doc_id].append(chunk)
        
        return chunks_by_doc
    
    def audit_document(self, doc_id: str) -> Dict:
        """
        Audit a specific document against all governance categories.
        
        Parameters
        ----------
        doc_id : str
            Document identifier (e.g., "openai_gpt4o_system_card")
        
        Returns
        -------
        Dict
            Complete audit report with evidence
        """
        if doc_id not in self.chunks_by_doc:
            return {
                "error": f"Document '{doc_id}' not found",
                "available_docs": list(self.chunks_by_doc.keys())[:10]
            }
        
        doc_chunks = self.chunks_by_doc[doc_id]
        metadata = self.doc_metadata.get(doc_id, {})
        
        # Run audit
        scores = self.auditor.audit_chunks(doc_chunks)
        
        # Generate comprehensive report
        report = self.analyzer.generate_evidence_based_report(
            doc_id=doc_id,
            scores=scores,
            chunks=doc_chunks,
            doc_metadata=metadata
        )
        
        # Add gap analysis
        gaps = self.auditor.generate_gap_analysis(scores)
        report["gap_analysis"] = gaps
        
        return report
    
    def compare_documents(
        self, 
        doc_ids: Optional[List[str]] = None,
        by_type: bool = False
    ) -> Dict:
        """
        Compare documentation coverage across multiple documents.
        
        Parameters
        ----------
        doc_ids : Optional[List[str]]
            Specific documents to compare. If None, compares all.
        by_type : bool
            If True, groups comparison by doc_type (framework vs artifact)
        
        Returns
        -------
        Dict
            Comparative analysis with statistics
        """
        if doc_ids is None:
            doc_ids = list(self.chunks_by_doc.keys())
        
        # Filter to valid doc_ids
        valid_doc_ids = [d for d in doc_ids if d in self.chunks_by_doc]
        
        if not valid_doc_ids:
            return {"error": "No valid documents found"}
        
        # Audit all documents
        all_scores = {}
        for doc_id in valid_doc_ids:
            doc_chunks = self.chunks_by_doc[doc_id]
            all_scores[doc_id] = self.auditor.audit_chunks(doc_chunks)
        
        if by_type:
            # Separate frameworks from artifacts
            framework_scores = {}
            artifact_scores = {}
            
            for doc_id, scores in all_scores.items():
                doc_type = self.doc_metadata.get(doc_id, {}).get("doc_type", "")
                
                if "framework" in doc_type or "study" in doc_type or "synthesis" in doc_type:
                    framework_scores[doc_id] = scores
                else:
                    artifact_scores[doc_id] = scores
            
            comparison = self.analyzer.compare_framework_vs_artifact_coverage(
                framework_scores=framework_scores,
                artifact_scores=artifact_scores,
                doc_metadata=self.doc_metadata
            )
        else:
            # Generic comparison
            comparison = self.auditor.compare_documents(all_scores)
            comparison["doc_metadata"] = {
                doc_id: self.doc_metadata.get(doc_id, {})
                for doc_id in valid_doc_ids
            }
        
        return comparison
    
    def analyze_equity_coverage(self) -> Dict:
        """
        Generate equity-focused analysis across all documents.
        
        Critical for addressing the Equity rubric criterion.
        
        Returns
        -------
        Dict
            Evidence-based equity analysis
        """
        # Audit all documents
        all_scores = {}
        for doc_id, doc_chunks in self.chunks_by_doc.items():
            all_scores[doc_id] = self.auditor.audit_chunks(doc_chunks)
        
        equity_analysis = self.analyzer.generate_equity_focused_analysis(
            all_scores=all_scores,
            doc_metadata=self.doc_metadata
        )
        
        return equity_analysis
    
    def answer_question(self, question: str, top_k: int = 5) -> Dict:
        """
        Answer a question using semantic search over chunks (if available).
        
        Parameters
        ----------
        question : str
            User's question about documentation
        top_k : int
            Number of relevant chunks to retrieve
        
        Returns
        -------
        Dict
            Answer with supporting evidence
        """
        if not self.searcher:
            return {
                "error": "Semantic search not available. Run build_embeddings_index.py first.",
                "fallback": "Use audit_document() or compare_documents() for analysis."
            }
        
        # Perform semantic search
        try:
            results = self.searcher.search(question, top_k=top_k)
        except Exception as e:
            return {
                "error": f"Search failed: {e}",
                "question": question
            }
        
        if not results:
            return {
                "answer": "No relevant information found in the corpus.",
                "sources": []
            }
        
        # Extract unique sources
        sources = []
        for result in results:
            doc_id = result.get("doc_id")
            
            if doc_id:
                metadata = self.doc_metadata.get(doc_id, {})
                sources.append({
                    "doc_id": doc_id,
                    "title": result.get("title", metadata.get("title", doc_id)),
                    "chunk_id": result.get("chunk_id", ""),
                    "relevance_score": round(result.get("score", 0.0), 3),
                    "text_preview": result.get("text", "")[:200] + "..."
                })
        
        return {
            "question": question,
            "top_chunks": len(results),
            "sources": sources,
            "note": "Use these sources to form evidence-based answers"
        }
    
    def get_category_overview(self, category_id: Optional[str] = None) -> Dict:
        """
        Get overview of a governance category or all categories.
        
        Parameters
        ----------
        category_id : Optional[str]
            Specific category to describe. If None, returns all.
        
        Returns
        -------
        Dict
            Category information and coverage statistics
        """
        if category_id:
            if category_id not in self.schema:
                return {
                    "error": f"Category '{category_id}' not found",
                    "available": list(self.schema.keys())
                }
            
            cat_info = self.schema[category_id]
            
            # Calculate overall coverage for this category
            coverage_scores = []
            for doc_chunks in self.chunks_by_doc.values():
                scores = self.auditor.audit_chunks(doc_chunks)
                if category_id in scores:
                    coverage_scores.append(scores[category_id].score)
            
            return {
                "category_id": category_id,
                "name": cat_info.get("human_name_en"),
                "governance_axis": cat_info.get("governance_axis"),
                "importance": cat_info.get("importance_weight"),
                "description": cat_info.get("description_en"),
                "examples": cat_info.get("examples", []),
                "question_templates": cat_info.get("question_templates_en", []),
                "overall_coverage": {
                    "mean": round(sum(coverage_scores) / len(coverage_scores), 3) if coverage_scores else 0.0,
                    "min": round(min(coverage_scores), 3) if coverage_scores else 0.0,
                    "max": round(max(coverage_scores), 3) if coverage_scores else 0.0,
                    "docs_evaluated": len(coverage_scores)
                }
            }
        else:
            # Return all categories with summary stats
            categories = {}
            for cat_id in self.schema:
                categories[cat_id] = {
                    "name": self.schema[cat_id].get("human_name_en"),
                    "importance": self.schema[cat_id].get("importance_weight"),
                    "governance_axis": self.schema[cat_id].get("governance_axis")
                }
            
            return {
                "total_categories": len(categories),
                "categories": categories,
                "governance_axes": list(set(c["governance_axis"] for c in categories.values()))
            }
    
    def list_documents(self, doc_type: Optional[str] = None) -> List[Dict]:
        """
        List available documents, optionally filtered by type.
        
        Parameters
        ----------
        doc_type : Optional[str]
            Filter by document type (e.g., "artifact", "framework")
        
        Returns
        -------
        List[Dict]
            Document metadata
        """
        docs = []
        
        for doc_id, metadata in self.doc_metadata.items():
            if doc_type is None or doc_type.lower() in metadata.get("doc_type", "").lower():
                docs.append({
                    "doc_id": doc_id,
                    "title": metadata.get("title"),
                    "year": metadata.get("year"),
                    "doc_type": metadata.get("doc_type"),
                    "chunk_count": len(self.chunks_by_doc.get(doc_id, []))
                })
        
        # Sort by year (descending) and title
        docs.sort(key=lambda x: (-x.get("year", 0), x.get("title", "")))
        
        return docs