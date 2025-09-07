import os
from typing import List, Dict, Iterable
from .base import LLMProvider

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    import httpx

class GeminiProvider(LLMProvider):
    def __init__(self, settings):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        self.model_name = settings.llm.get("model", "gemini-1.5-flash")
        self.temperature = settings.llm.get("temperature", 0.2)
        self.max_tokens = settings.llm.get("max_tokens", 4096)
        
        if GENAI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat completion request to Gemini API"""
        try:
            if GENAI_AVAILABLE:
                return self._chat_with_genai(messages)
            else:
                return self._chat_with_httpx(messages)
        except Exception as e:
            return f"Error: {str(e)}"

    def _chat_with_genai(self, messages: List[Dict[str, str]]) -> str:
        """Use official Google Generative AI library"""
        # Convert messages to chat format
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # System messages can be prepended to first user message
                if chat_messages and chat_messages[-1]["role"] == "user":
                    chat_messages[-1]["parts"][0] = f"{msg['content']}\n\n{chat_messages[-1]['parts'][0]}"
                else:
                    chat_messages.append({"role": "user", "parts": [msg["content"]]})
            else:
                role = "user" if msg["role"] == "user" else "model"
                chat_messages.append({"role": role, "parts": [msg["content"]]})

        # Start chat and send message
        chat = self.model.start_chat(history=chat_messages[:-1])
        response = chat.send_message(
            chat_messages[-1]["parts"][0],
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
        )
        return response.text

    def _chat_with_httpx(self, messages: List[Dict[str, str]]) -> str:
        """Fallback using direct HTTP calls"""
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            }
        }

        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/models/{self.model_name}:generateContent",
                params={"key": self.api_key},
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "candidates" in result and len(result["candidates"]) > 0:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return "No response generated"

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Gemini embedding model"""
        try:
            embeddings = []
            
            if GENAI_AVAILABLE:
                for text in texts:
                    result = genai.embed_content(
                        model="models/text-embedding-004",
                        content=text
                    )
                    embeddings.append(result['embedding'])
            else:
                # Fallback HTTP method
                for text in texts:
                    payload = {
                        "model": "models/text-embedding-004",
                        "content": {"parts": [{"text": text}]}
                    }
                    
                    with httpx.Client() as client:
                        response = client.post(
                            f"{self.base_url}/models/text-embedding-004:embedContent",
                            params={"key": self.api_key},
                            json=payload,
                            headers={"Content-Type": "application/json"},
                            timeout=30.0
                        )
                        response.raise_for_status()
                        
                        result = response.json()
                        embedding = result.get("embedding", {}).get("values", [])
                        embeddings.append(embedding)
                        
            return embeddings
            
        except Exception as e:
            # Return dummy embeddings on error
            return [[0.0] * 768 for _ in texts]

    def stream(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        """Stream chat completion"""
        if GENAI_AVAILABLE:
            try:
                # Convert messages for streaming
                chat_messages = []
                for msg in messages[:-1]:  # All but last message for history
                    role = "user" if msg["role"] == "user" else "model"
                    chat_messages.append({"role": role, "parts": [msg["content"]]})

                chat = self.model.start_chat(history=chat_messages)
                response = chat.send_message(
                    messages[-1]["content"],
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                    ),
                    stream=True
                )
                
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                        
            except Exception:
                # Fallback to non-streaming
                response = self.chat(messages)
                yield response
        else:
            # Fallback to non-streaming for HTTP client
            response = self.chat(messages)
            yield response
