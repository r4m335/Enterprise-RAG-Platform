from typing import List, Dict, Any
from pydantic import BaseModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
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

def chunk_document(parsed_doc: ParsedDocument, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[ChunkData]:
    """
    Uses RecursiveCharacterTextSplitter to split the document pages into smaller chunks.
    Maintains page references and metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = []
    
    for page in parsed_doc.pages:
        # Split each page's text
        texts = splitter.split_text(page.text)
        
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
