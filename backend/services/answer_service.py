from typing import List, Dict
from backend.rag.types import GeminiClientConfig

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

    
def generate_answer(query: str, context_chunks: List[Dict], max_tokens: int = 5000) -> str:
    """
    Generate an answer using retrieved context
    
    Args:
        query: User's question
        context_chunks: Retrieved relevant chunks
        max_tokens: Maximum tokens for response
        
    Returns:
        Generated answer
    """
    if not context_chunks:
        return "I couldn't find any relevant information in your uploaded files to answer this question."
    
    context_text = "\n\n".join([
        f"From {chunk['chunk']['metadata']['filename']}:\n{chunk['chunk']['text']}"
        for chunk in context_chunks[:3]
    ])
    
    prompt = f"""Based on the following context from the user's uploaded files, please answer their question. If the context doesn't contain enough information to answer the question, please say so.

Context:
{context_text}

Question: {query}

Answer:"""
    
    try:
        model_name = "gemini-2.5-flash" #Need to move away from hardcoding
        text_responses_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        client = GeminiClientConfig(model_name=model_name, url=text_responses_url)
        return client.get_text_response(prompt, max_tokens)
    except Exception as e:
        logger.error(f"Failed to generate LLM response: {e}")
        return "I encountered an error while generating the response. Please try again."
