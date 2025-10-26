"""
Simplified Embedding System (Text-Only, Multi-Provider)
- Text: Multi-provider (OpenAI, Anthropic, Gemini) - Settings-driven
- Images: Vision LLM → Text → Text embeddings (no CLIP)
"""
from typing import List, Dict, Any, Optional
from PIL import Image
import base64
from pathlib import Path
import os


class TextEmbedder:
    """
    Multi-provider text embeddings driven by settings.json

    Supports:
    - OpenAI: text-embedding-3-small, text-embedding-3-large
    - Anthropic: voyage-2 (via Voyage AI partnership)
    - Gemini: text-embedding-004
    """

    def __init__(self):
        from src.core.config.settings import get_settings
        self.settings = get_settings()

        self.provider = self.settings.embedding_provider
        self.model = self.settings.embedding_model
        self.dimensions = self.settings.embedding_dimensions

        # Initialize provider client
        self._init_client()

    def _init_client(self):
        """Initialize the appropriate embedding client based on provider"""
        if self.provider == "openai":
            from openai import OpenAI
            api_key = self.settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
            self.client = OpenAI(api_key=api_key) if api_key else OpenAI()

        elif self.provider == "anthropic":
            # Anthropic uses Voyage AI for embeddings
            # https://docs.anthropic.com/claude/docs/embeddings
            import voyageai
            api_key = self.settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
            self.client = voyageai.Client(api_key=api_key) if api_key else voyageai.Client()

        elif self.provider == "gemini":
            import google.generativeai as genai
            api_key = self.settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            self.client = genai

        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.provider == "openai":
            # OpenAI embeddings API
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [data.embedding for data in response.data]

        elif self.provider == "anthropic":
            # Voyage AI API (Anthropic's embedding partner)
            # API: vo.embed(texts, model, input_type)
            result = self.client.embed(
                texts=texts,
                model=self.model or "voyage-3",
                input_type="document"  # For RAG document storage
            )
            return result.embeddings

        elif self.provider == "gemini":
            # Gemini embedding API
            # embed_content() for single text, batch for multiple
            embeddings = []
            for text in texts:
                result = self.client.embed_content(
                    model=f"models/{self.model}" if not self.model.startswith("models/") else self.model,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            return embeddings

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def embed_single(self, text: str) -> List[float]:
        """Generate single text embedding"""
        return self.embed_texts([text])[0]


class ImageEmbedder:
    """
    Simplified Image Embeddings (Vision LLM Only, No CLIP)

    Strategy:
    1. Vision Model → Comprehensive text description (OCR + visual analysis)
    2. Text embeddings of description → Semantic search
    3. Single storage → Text collection only (no visual embeddings)
    """

    def __init__(self):
        """
        Initialize image embedder with vision LLM (no CLIP)
        """
        from src.core.config.settings import get_settings
        self.settings = get_settings()

        # Vision model for image descriptions (settings-driven)
        # Use same provider as embeddings for consistency
        embedding_provider = self.settings.embedding_provider

        # Auto-select vision model based on embedding provider
        vision_model = self.settings.vision_model

        # If vision_model doesn't match embedding_provider, override with provider-specific default
        if embedding_provider == "openai" and not (vision_model.startswith("gpt-4")):
            vision_model = "gpt-4o"
            print(f"ℹ️ Using OpenAI vision model: {vision_model}")
        elif embedding_provider == "anthropic" and not vision_model.startswith("claude"):
            vision_model = "claude-3-5-sonnet-20241022"
            print(f"ℹ️ Using Anthropic vision model: {vision_model}")
        elif embedding_provider == "gemini" and not vision_model.startswith("gemini"):
            vision_model = "gemini-2.5-flash"
            print(f"ℹ️ Using Gemini vision model: {vision_model}")

        self.vision_model = vision_model
        self.vision_provider = embedding_provider  # ALWAYS use same provider

        # Initialize vision client based on provider
        self._init_vision_client()

        print(f"✅ Vision LLM ready: {self.vision_model} (no CLIP)")

    def _init_vision_client(self):
        """Initialize vision client based on provider"""
        if self.vision_provider == "openai":
            from openai import OpenAI
            api_key = self.settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
            self.vision_client = OpenAI(api_key=api_key) if api_key else OpenAI()

        elif self.vision_provider == "anthropic":
            from anthropic import Anthropic
            api_key = self.settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
            self.vision_client = Anthropic(api_key=api_key) if api_key else Anthropic()

        elif self.vision_provider == "gemini":
            import google.generativeai as genai
            api_key = self.settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            self.vision_client = genai

    async def get_vision_description(self, image_path: str) -> str:
        """
        Get text description of image using configured vision model

        Args:
            image_path: Path to image

        Returns:
            Text description (for human-readable context)
        """
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Enhanced prompt for comprehensive OCR and description
        prompt = (
            "Extract and describe ALL content from this image in detail:\n\n"
            "**For document images (CVs, forms, scanned docs):**\n"
            "- Extract ALL visible text verbatim (preserve formatting, line breaks)\n"
            "- Include names, dates, numbers, addresses, emails, phone numbers\n"
            "- Capture tables, lists, sections, headings\n\n"
            "**For visual images (photos, diagrams, charts):**\n"
            "- Describe what's shown (objects, people, scenes, UI elements)\n"
            "- Explain visual details (colors, layout, composition)\n"
            "- Extract any text, labels, or data points\n"
            "- Describe context and purpose\n\n"
            "Write as continuous, detailed text optimized for semantic search."
        )

        if self.vision_provider == "openai":
            # OpenAI Vision API (GPT-4o, GPT-4-turbo with vision)
            response = self.vision_client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=10000  # Increased for comprehensive OCR
            )
            return response.choices[0].message.content

        elif self.vision_provider == "anthropic":
            # Claude Vision API (Claude 3+ supports vision)
            # Supported formats: JPEG, PNG, GIF, WebP
            import mimetypes
            mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"

            response = self.vision_client.messages.create(
                model=self.vision_model,
                max_tokens=10000,  # Increased for comprehensive OCR
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": base64_image
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            )
            return response.content[0].text

        elif self.vision_provider == "gemini":
            # Gemini Vision API (gemini-2.5-flash, gemini-2.5-pro)
            model = self.vision_client.GenerativeModel(self.vision_model)
            img = Image.open(image_path)
            response = model.generate_content(
                [prompt, img],
                generation_config={"max_output_tokens": 10000}  # Increased for comprehensive OCR
            )
            return response.text

        else:
            raise ValueError(f"Unsupported vision provider: {self.vision_provider}")

    async def get_image_description(self, image_path: str) -> str:
        """
        Get comprehensive text description of image (Vision LLM only)

        Args:
            image_path: Path to image

        Returns:
            Detailed text description for semantic search
        """
        return await self.get_vision_description(image_path)


class HybridEmbedder:
    """
    Simplified Embedding Pipeline (Text-Only, Universal)

    For Text Documents: Direct text embedding
    For Images: Vision LLM → Text → Text embedding
    For All: Single unified text collection
    """

    def __init__(self):
        self.text_embedder = TextEmbedder()
        self.image_embedder = None  # Lazy load

    def _ensure_image_embedder(self):
        """Lazy load image embedder"""
        if self.image_embedder is None:
            self.image_embedder = ImageEmbedder()

    async def embed_document(
        self,
        content: str,
        modality: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Embed document (text-only pipeline, universal for all types)

        Args:
            content: Extracted text content (or placeholder for images)
            modality: "text", "structured", or "image"
            file_path: Original file path (needed for images to get vision description)

        Returns:
            {
                "text_embedding": [...],  # Always text embeddings only
                "description": "...",     # Text content or vision description
                "modality": "..."
            }
        """
        if modality == "image" and file_path:
            # Ensure image embedder loaded
            self._ensure_image_embedder()

            # Vision LLM generates comprehensive text description
            description = await self.image_embedder.get_image_description(file_path)

            # Embed the description as text (same as text documents)
            text_emb = self.text_embedder.embed_single(description)

            return {
                "text_embedding": text_emb,
                "description": description,
                "modality": "image"
            }
        else:
            # Text-only embedding (for text/structured docs)
            text_emb = self.text_embedder.embed_single(content)

            return {
                "text_embedding": text_emb,
                "description": content,
                "modality": modality
            }


# Lazy-loaded global instances (avoid requiring API keys at import time)
_text_embedder_instance = None
_hybrid_embedder_instance = None

class LazyTextEmbedder:
    def __getattribute__(self, name):
        global _text_embedder_instance
        if _text_embedder_instance is None:
            _text_embedder_instance = TextEmbedder()
        return getattr(_text_embedder_instance, name)

class LazyHybridEmbedder:
    def __getattribute__(self, name):
        global _hybrid_embedder_instance
        if _hybrid_embedder_instance is None:
            _hybrid_embedder_instance = HybridEmbedder()
        return getattr(_hybrid_embedder_instance, name)

# Global instances
text_embedder = LazyTextEmbedder()
hybrid_embedder = LazyHybridEmbedder()
