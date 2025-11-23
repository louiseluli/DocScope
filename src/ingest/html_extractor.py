from pathlib import Path
from typing import List, Dict, Optional
import re


def detect_markdown_header(line: str) -> Optional[str]:
    """
    Detect markdown headers (# Header, ## Subheader, etc.).
    Returns the header text without the # symbols.
    """
    line = line.strip()
    match = re.match(r'^(#{1,6})\s+(.+)$', line)
    if match:
        return match.group(2).strip()
    return None


def detect_section_patterns(line: str) -> Optional[str]:
    """
    Detect common section patterns in model card documentation:
    - ALL CAPS headers
    - Title Case followed by colon
    - Numbered sections (1. Section Name)
    """
    line = line.strip()
    
    # Numbered sections: "1. Model Overview" or "1.1 Architecture"
    if re.match(r'^\d+\.?\d*\s+[A-Z]', line):
        return re.sub(r'^\d+\.?\d*\s+', '', line).strip()
    
    # All caps (but not too long, likely not a sentence)
    if line.isupper() and 3 < len(line) < 80 and not line.endswith('.'):
        return line
    
    # Title case with colon: "Model Details:"
    if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:?\s*$', line) and len(line) < 60:
        return line.rstrip(':')
    
    return None


def extract_code_blocks(text: str) -> List[Dict]:
    """
    Extract code blocks from markdown (```...```).
    Returns list of code blocks with their content.
    """
    code_blocks = []
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.finditer(pattern, text, re.DOTALL)
    
    for idx, match in enumerate(matches):
        language = match.group(1) or "unknown"
        code = match.group(2).strip()
        if code:
            code_blocks.append({
                "index": idx,
                "language": language,
                "code": code
            })
    
    return code_blocks


def extract_markdown_tables(text: str) -> List[Dict]:
    """
    Extract markdown tables from text.
    Returns list of tables with their content.
    """
    tables = []
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this line looks like a table row (contains |)
        if '|' in line and line.count('|') >= 2:
            table_lines = [line]
            j = i + 1
            
            # Collect consecutive table lines
            while j < len(lines):
                next_line = lines[j].strip()
                if '|' in next_line:
                    table_lines.append(next_line)
                    j += 1
                elif not next_line:  # Empty line might be inside table
                    j += 1
                else:
                    break
            
            # If we found at least 2 lines (header + separator/data), it's a table
            if len(table_lines) >= 2:
                table_text = '\n'.join(table_lines)
                tables.append({
                    "index": len(tables),
                    "text": table_text,
                    "row_count": len(table_lines)
                })
                i = j
                continue
        
        i += 1
    
    return tables


def extract_structured_content_from_text(path: Path) -> Dict[str, List[Dict]]:
    """
    Extract structured content from markdown/text files including:
    - Paragraphs with section context
    - Code blocks
    - Tables
    - Metadata (if present in YAML front matter)
    
    Returns
    -------
    Dict with keys:
        - paragraphs: List[Dict] with text, section, line_num
        - code_blocks: List[Dict] with code, language
        - tables: List[Dict] with table text
        - metadata: Dict with any front matter metadata
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    text = path.read_text(encoding="utf-8", errors="ignore")
    
    # Extract code blocks first (so we don't treat them as regular text)
    code_blocks = extract_code_blocks(text)
    
    # Extract tables
    tables = extract_markdown_tables(text)
    
    # Remove code blocks from text for paragraph processing
    text_without_code = re.sub(r'```(\w+)?\n.*?```', '', text, flags=re.DOTALL)
    
    # Process paragraphs with section awareness
    paragraphs = []
    current_section = "Overview"
    lines = text_without_code.split('\n')
    current_paragraph_lines = []
    line_num = 0
    
    for line in lines:
        line_num += 1
        stripped = line.strip()
        
        if not stripped:
            # Empty line - paragraph boundary
            if current_paragraph_lines:
                para_text = ' '.join(current_paragraph_lines)
                if len(para_text) > 40:  # Minimum meaningful content
                    paragraphs.append({
                        "text": para_text,
                        "section": current_section,
                        "line_num": line_num
                    })
                current_paragraph_lines = []
            continue
        
        # Check for markdown header
        md_header = detect_markdown_header(stripped)
        if md_header:
            # Save accumulated paragraph
            if current_paragraph_lines:
                para_text = ' '.join(current_paragraph_lines)
                if len(para_text) > 40:
                    paragraphs.append({
                        "text": para_text,
                        "section": current_section,
                        "line_num": line_num
                    })
                current_paragraph_lines = []
            current_section = md_header
            continue
        
        # Check for other section patterns
        section_header = detect_section_patterns(stripped)
        if section_header:
            if current_paragraph_lines:
                para_text = ' '.join(current_paragraph_lines)
                if len(para_text) > 40:
                    paragraphs.append({
                        "text": para_text,
                        "section": current_section,
                        "line_num": line_num
                    })
                current_paragraph_lines = []
            current_section = section_header
            continue
        
        # Skip table separator lines (|---|---|)
        if re.match(r'^[\|\s\-:]+$', stripped):
            continue
        
        # Regular content line
        current_paragraph_lines.append(stripped)
    
    # Don't forget last paragraph
    if current_paragraph_lines:
        para_text = ' '.join(current_paragraph_lines)
        if len(para_text) > 40:
            paragraphs.append({
                "text": para_text,
                "section": current_section,
                "line_num": line_num
            })
    
    return {
        "paragraphs": paragraphs,
        "code_blocks": code_blocks,
        "tables": tables,
        "metadata": {}  # Could be extended to parse YAML front matter
    }


def build_text_chunks(doc_row: Dict, base_data_dir: Path) -> List[Dict]:
    """
    Build enhanced chunk dictionaries for text/markdown docs with:
    - Section-aware paragraphs
    - Separate code blocks
    - Separate tables
    - Line number tracking
    
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
        - chunk_type (text|code|table)
        - line_num (for text) or index (for code/table)
        - source_path
        - language (for code chunks)
    """
    rel_path = doc_row["rel_path"]
    file_path = base_data_dir / "raw" / rel_path
    
    content = extract_structured_content_from_text(file_path)
    
    chunks = []
    
    # Add text paragraph chunks
    for i, para in enumerate(content["paragraphs"]):
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
            "line_num": para["line_num"],
            "source_path": str(file_path),
        })
    
    # Add code block chunks
    for i, code_block in enumerate(content["code_blocks"]):
        chunk_id = f"{doc_row['doc_id']}::code_{i:04d}"
        chunks.append({
            "chunk_id": chunk_id,
            "doc_id": doc_row["doc_id"],
            "title": doc_row["title"],
            "year": int(doc_row["year"]),
            "doc_type": doc_row["doc_type"],
            "eval_type": doc_row["eval_type"],
            "text": code_block["code"],
            "section_heading": "",
            "chunk_type": "code",
            "language": code_block["language"],
            "source_path": str(file_path),
        })
    
    # Add table chunks
    for i, table in enumerate(content["tables"]):
        chunk_id = f"{doc_row['doc_id']}::table_{i:04d}"
        chunks.append({
            "chunk_id": chunk_id,
            "doc_id": doc_row["doc_id"],
            "title": doc_row["title"],
            "year": int(doc_row["year"]),
            "doc_type": doc_row["doc_type"],
            "eval_type": doc_row["eval_type"],
            "text": table["text"],
            "section_heading": "",
            "chunk_type": "table",
            "row_count": table["row_count"],
            "source_path": str(file_path),
        })
    
    return chunks