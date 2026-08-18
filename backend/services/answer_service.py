from typing import List, Dict
from backend.rag.types import GeminiClientConfig
import requests
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiGenerationClient:
    def __init__(self, generation_model = "gemini-2.5-flash"):
        self.config = GeminiClientConfig(model_name=generation_model)
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{generation_model}:generateContent"
    
    def generate_answer(
            self,
            query: str,
            context_chunks: List[Dict],
            max_tokens: int = 5000
        ) -> str:
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
        
        try:
            headers = self._build_headers()
            data = self._build_body(context_chunks, query, max_tokens)

            response = requests.post(self.url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Gemini API response: {result}")
            return result['candidates'][0]['content']['parts'][0]['text']

        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            return "I encountered an error while generating the response. Please try again."

    def _build_headers(self):
        return {
                "x-goog-api-key": self.config.api_key,
                "Content-Type": "application/json"
            }

    def _build_body(self, context_chunks: List[Dict], query: str, max_tokens: int):
        return {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": self._build_prompt(context_chunks, query)
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens
                    },
                    "systemInstruction": {
                        "parts": [
                            {
                                "text": "You are a helpful assistant that answers questions based on the provided context from user's documents."
                            }
                        ]
                    }
                }
        

    def _build_prompt(context_chunks: List[Dict], query: str):
        context_text = "\n\n".join([
                    f"From {chunk['chunk']['metadata']['filename']}:\n{chunk['chunk']['text']}"
                    for chunk in context_chunks[:3]
                ])
        return f"""
        Based on the following context from the user's uploaded files, please answer their question.
        If the context doesn't contain enough information to answer the question, always say so.

        Context: {context_text}

        Question: {query}

        Answer:
        """
