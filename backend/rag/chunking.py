from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from rag.parser import ParsedDocument

class ChunkData(BaseModel):
    text: str
    token_count: int
    page_number: int
    metadata: Dict[str, Any]

def estimate_tokens(text: str) -> int:
    """
    Very rough approximation of tokens for chunking limits. 
    1 token ~ 4 characters in English.
    """
    return len(text) // 4

def _split_text_recursive(
    text: str, 
    chunk_size: int = 1000, 
    chunk_overlap: int = 200, 
    separators: Optional[List[str]] = None
) -> List[str]:
    """
    Pure Python recursive character text splitter mimicking LangChain's logic.
    Eliminates heavy dependency loading overhead while preserving exact splitting behavior.
    """
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]
        
    separator = separators[-1]
    new_separators = []
    for i, s in enumerate(separators):
        if s == "":
            separator = ""
            break
        if s in text:
            separator = s
            new_separators = separators[i + 1:]
            break

    splits = text.split(separator) if separator else list(text)
    
    good_splits = []
    for s in splits:
        if len(s) <= chunk_size:
            good_splits.append(s)
        else:
            if new_separators:
                good_splits.extend(_split_text_recursive(s, chunk_size, chunk_overlap, new_separators))
            else:
                good_splits.append(s)
                
    chunks = []
    current_chunk: List[str] = []
    current_len = 0
    
    for s in good_splits:
        s_len = len(s) + (len(separator) if current_chunk else 0)
        if current_len + s_len > chunk_size and current_chunk:
            doc = separator.join(current_chunk)
            if doc.strip():
                chunks.append(doc)
            while current_chunk and current_len > chunk_overlap:
                popped = current_chunk.pop(0)
                current_len -= len(popped) + len(separator)
        current_chunk.append(s)
        current_len += s_len
        
    if current_chunk:
        doc = separator.join(current_chunk)
        if doc.strip():
            chunks.append(doc)
            
    return chunks

def chunk_document(parsed_doc: ParsedDocument, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[ChunkData]:
    """
    Splits the document pages into smaller chunks.
    Maintains page references and metadata.
    """
    chunks = []
    
    for page in parsed_doc.pages:
        texts = _split_text_recursive(page.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        for idx, chunk_text in enumerate(texts):
            chunks.append(ChunkData(
                text=chunk_text,
                token_count=estimate_tokens(chunk_text),
                page_number=page.page_number,
                metadata={
                    "mime_type": parsed_doc.mime_type,
                    "chunk_index": idx
                }
            ))
            
    return chunks
