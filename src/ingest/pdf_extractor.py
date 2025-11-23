from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pdfplumber
import re


def detect_section_header(text: str) -> Optional[str]:
    """
    Detect if a text line is likely a section header.
    
    Heuristics:
    - All caps and short (< 100 chars)
    - Starts with number followed by period/colon
    - Common header patterns in AI documentation
    
    Returns the cleaned header text or None.
    """
    text = text.strip()
    
    # Common documentation section patterns
    header_patterns = [
        r'^(\d+\.?\s+)?([A-Z][A-Z\s&-]+)$',  # "1. SAFETY" or "SAFETY & RISK"
        r'^#{1,6}\s+(.+)$',  # Markdown headers
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):?\s*$',  # "Training Data:" or "Model Architecture"
    ]
    
    for pattern in header_patterns:
        match = re.match(pattern, text)
        if match:
            # Extract the actual header text
            header = match.group(0).strip('#').strip(':').strip()
            if len(header) < 100 and header:
                return header
    
    # Check for all-caps short lines
    if text.isupper() and 3 < len(text) < 80:
        return text
    
    return None


def extract_tables_from_pdf(pdf_path: Path) -> List[Dict]:
    """
    Extract tables from PDF with page numbers and basic formatting.
    
    Returns list of dicts with:
    - page_num: int
    - table_data: list of lists (rows)
    - text_representation: string representation of table
    """
    tables = []
    
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()
                if page_tables:
                    for table_idx, table in enumerate(page_tables):
                        if table and len(table) > 1:  # At least header + 1 row
                            # Convert table to text representation
                            text_lines = []
                            for row in table:
                                if row:
                                    # Filter out None and empty strings
                                    cleaned_row = [str(cell).strip() for cell in row if cell]
                                    if cleaned_row:
                                        text_lines.append(" | ".join(cleaned_row))
                            
                            if text_lines:
                                tables.append({
                                    "page_num": page_num,
                                    "table_idx": table_idx,
                                    "table_data": table,
                                    "text_representation": "\n".join(text_lines)
                                })
    except Exception as e:
        print(f"[WARN] Table extraction failed for {pdf_path}: {e}")
    
    return tables


def extract_structured_content_from_pdf(pdf_path: Path) -> Tuple[List[Dict], List[Dict]]:
    """
    Extract both paragraphs and tables with structural metadata.
    
    Returns:
    --------
    Tuple[List[Dict], List[Dict]]
        - List of paragraph dicts with section context
        - List of table dicts
    """
    paragraphs = []
    current_section = "Introduction"  # Default section
    
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return paragraphs, []
    
    try:
        full_text_parts = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if text:
                    # Store with page metadata
                    full_text_parts.append({
                        "page_num": page_num,
                        "text": text
                    })
    except Exception as e:
        print(f"[WARN] Failed to parse PDF {pdf_path}: {type(e).__name__}: {e}")
        return paragraphs, []
    
    # Extract tables separately
    tables = extract_tables_from_pdf(pdf_path)
    
    # Process text with section awareness
    for page_info in full_text_parts:
        page_num = page_info["page_num"]
        text = page_info["text"]
        
        # Split into lines first to detect headers
        lines = text.split("\n")
        current_paragraph_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # Empty line - potential paragraph boundary
                if current_paragraph_lines:
                    para_text = " ".join(current_paragraph_lines)
                    if len(para_text) > 30:  # Minimum meaningful length
                        paragraphs.append({
                            "text": para_text,
                            "section": current_section,
                            "page_num": page_num
                        })
                    current_paragraph_lines = []
                continue
            
            # Check if this line is a section header
            header = detect_section_header(line)
            if header:
                # Save any accumulated paragraph first
                if current_paragraph_lines:
                    para_text = " ".join(current_paragraph_lines)
                    if len(para_text) > 30:
                        paragraphs.append({
                            "text": para_text,
                            "section": current_section,
                            "page_num": page_num
                        })
                    current_paragraph_lines = []
                
                # Update current section
                current_section = header
            else:
                # Regular text line
                current_paragraph_lines.append(line)
        
        # Don't forget last paragraph of the page
        if current_paragraph_lines:
            para_text = " ".join(current_paragraph_lines)
            if len(para_text) > 30:
                paragraphs.append({
                    "text": para_text,
                    "section": current_section,
                    "page_num": page_num
                })
    
    return paragraphs, tables


def build_pdf_chunks(doc_row: Dict, base_data_dir: Path) -> List[Dict]:
    """
    Build enhanced chunk dictionaries for a single PDF with:
    - Section-aware text chunks
    - Table chunks as structured data
    - Page number tracking
    
    Parameters
    ----------
    doc_row : Dict
        Row from metadata DataFrame (converted to dict).
        Must contain: doc_id, title, year, doc_type, eval_type, rel_path.
    base_data_dir : Path
        Base 'data' directory (e.g., DATA_DIR).
    
    Returns
    -------
    List[Dict]
        List of chunks with fields:
        - chunk_id
        - doc_id
        - title
        - year
        - doc_type
        - eval_type
        - text
        - section_heading
        - chunk_type (text|table)
        - page_num
        - source_path
        - table_data (optional, for table chunks)
    """
    rel_path = doc_row["rel_path"]
    pdf_path = base_data_dir / "raw" / rel_path
    
    paragraphs, tables = extract_structured_content_from_pdf(pdf_path)
    
    chunks = []
    
    # Add text chunks
    for i, para in enumerate(paragraphs):
        chunk_id = f"{doc_row['doc_id']}::text_{i:04d}"
        chunks.append({
            "chunk_id": chunk_id,
            "doc_id": doc_row["doc_id"],
            "title": doc_row["title"],
            "year": int(doc_row["year"]),
            "doc_type": doc_row["doc_type"],
            "eval_type": doc_row["eval_type"],
            "text": para["text"],
            "section_heading": para["section"],
            "chunk_type": "text",
            "page_num": para["page_num"],
            "source_path": str(pdf_path),
        })
    
    # Add table chunks
    for i, table in enumerate(tables):
        chunk_id = f"{doc_row['doc_id']}::table_{i:04d}"
        chunks.append({
            "chunk_id": chunk_id,
            "doc_id": doc_row["doc_id"],
            "title": doc_row["title"],
            "year": int(doc_row["year"]),
            "doc_type": doc_row["doc_type"],
            "eval_type": doc_row["eval_type"],
            "text": table["text_representation"],
            "section_heading": "",  # Tables don't have sections in this version
            "chunk_type": "table",
            "page_num": table["page_num"],
            "source_path": str(pdf_path),
            "table_data": table["table_data"],  # Preserve raw table structure
        })
    
    return chunks