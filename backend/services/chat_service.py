import os
from openai import OpenAI
from typing import List, Dict, Optional
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling AI chat with Grok 4 via OpenRouter"""

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning("OPENROUTER_API_KEY not set.")
            self.client = None
        else:
            # Configure OpenRouter client (OpenAI-compatible)
            self.client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            )

        self.model = os.getenv("OPENROUTER_MODEL", "x-ai/grok-beta")
        self.max_tokens = 2500

    def capitalize_mentor_protege(self, text: str) -> str:
        """Ensure Mentor and Protégé are always capitalized"""
        # Replace all variations
        text = re.sub(r'\bmentor\b', 'Mentor', text, flags=re.IGNORECASE)
        text = re.sub(r'\bmentors\b', 'Mentors', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprotege\b', 'Protégé', text, flags=re.IGNORECASE)
        text = re.sub(r'\bproteges\b', 'Protégés', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprotégé\b', 'Protégé', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprotégés\b', 'Protégés', text, flags=re.IGNORECASE)
        return text

    def verify_response(self, user_message: str, context: Optional[List[Dict]], attempt: int = 1) -> str:
        """Generate response with verification pass"""
        system_message = """You are an expert DoD Mentor-Protégé Program (MPP) accuracy verification and content development assistant.

**CRITICAL RULES:**
1. ALWAYS capitalize "Mentor" and "Protégé" (M and P capitalized)
2. Provide EXACT citations with section numbers and paragraphs (NO page numbers unless user asks)
3. ONLY use information from MPP SOP, DFARS Appendix I, and eLearning SOP
4. When user shares text, respond with this EXACT format:

**Accuracy Assessment:** [percentage]% accurate

**Source Verification:**
- [Document Name], Section [X.X.X] "[Title]", Paragraph [X]
- [Additional sources...]

**Discrepancies Identified:**
- [List any inaccuracies or missing information]

**Rewritten Version (eLearning SOP Style):**

[Provide the rewritten text in eLearning SOP format with:
- Clear headers (###)
- Bullet points (•)
- Proper capitalization (Mentor, Protégé)
- Citations in italics at the end: *Source: [Document], Section [X.X.X]*
- NO explanations of changes - just the rewritten content]

**NEVER HALLUCINATE - Only use provided documentation. If uncertain, state limitations clearly.**"""

        if context and len(context) > 0:
            context_text = "\n\n".join([
                f"[{item['source']}]\n{item['text']}"
                for item in context
            ])
            system_message += f"\n\n**Documentation Context:**\n{context_text}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=self.max_tokens,
            temperature=0.15 if attempt == 2 else 0.2  # Even lower temp on second pass
        )

        return response.choices[0].message.content

    def generate_response(self, user_message: str, context: Optional[List[Dict]] = None) -> str:
        """Generate response using Grok 4 with double-verification"""

        if not self.client:
            return "Error: OpenRouter API key not configured. Please set OPENROUTER_API_KEY in .env file."

        try:
            # First verification pass
            logger.info("Verification pass 1/2...")
            response_1 = self.verify_response(user_message, context, attempt=1)

            # Second verification pass (with slightly different temperature)
            logger.info("Verification pass 2/2...")
            response_2 = self.verify_response(user_message, context, attempt=2)

            # Use the second response (more conservative temperature)
            raw_response = response_2
            logger.info("✓ Double-verification complete")

            # Ensure capitalization
            formatted_response = self.capitalize_mentor_protege(raw_response)

            return formatted_response

        except Exception as e:
            logger.error(f"Error with Grok 4: {str(e)}")
            return f"Error generating response: {str(e)}"
