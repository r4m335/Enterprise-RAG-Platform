from typing import List, Dict
from models.message import Message
from rag.retrieval import RetrievedChunk

class ContextBuilder:
    SYSTEM_PROMPT = """You are an enterprise document assistant.

Answer using the supplied document context.
If the context does not contain enough information, state that the information is unavailable.

Do not invent facts or sources. Do not hallucinate document identifiers.
"""

    @staticmethod
    def build_messages(
        question: str, 
        history: List[Message], 
        retrieved_chunks: List[RetrievedChunk]
    ) -> List[Dict[str, str]]:
        
        # 1. System Message
        messages = [{"role": "system", "content": ContextBuilder.SYSTEM_PROMPT}]
        
        # 2. History
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
            
        # 3. Context & Current Question
        context_str = ""
        if retrieved_chunks:
            context_str = "RETRIEVED DOCUMENTS\n\n"
            for i, chunk in enumerate(retrieved_chunks, 1):
                page_str = f"\nPage: {chunk.page_number}" if chunk.page_number else ""
                context_str += f"[SOURCE {i}]\nDocument ID: {chunk.document_id}{page_str}\nContent:\n{chunk.text}\n\n"
        else:
            context_str = "No documents found."
            
        user_prompt = f"{context_str}\nCURRENT QUESTION\n\n{question}"
        
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
