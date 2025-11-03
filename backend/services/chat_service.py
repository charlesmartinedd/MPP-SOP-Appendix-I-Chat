import os
from openai import OpenAI
import google.generativeai as genai
from typing import List, Dict, Optional
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling AI chat with Dual AI Verification

    Flow:
    1. Grok 4 (xAI) generates response (Spanish -> English)
    2. Gemini verifies and synthesizes final answer (Spanish -> English)
    """

    def __init__(self):
        # xAI Grok API client
        grok_key = os.getenv("GROK_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.grok_client = None
        self.grok_model = None
        self.grok_provider = None

        if grok_key:
            self.grok_client = OpenAI(
                api_key=grok_key,
                base_url=os.getenv("GROK_API_BASE", "https://api.x.ai/v1")
            )
            self.grok_model = os.getenv("GROK_MODEL", "grok-4-0709")
            self.grok_provider = "xai"
            logger.info("Grok 4 configured via xAI endpoint")
        elif openrouter_key:
            openrouter_base = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            default_headers = {}
            site_url = os.getenv("OPENROUTER_SITE_URL")
            app_name = os.getenv("OPENROUTER_APP_NAME", "MPP SOP & Appendix I Chat")
            if site_url:
                default_headers["HTTP-Referer"] = site_url
            if app_name:
                default_headers["X-Title"] = app_name

            self.grok_client = OpenAI(
                api_key=openrouter_key,
                base_url=openrouter_base,
                default_headers=default_headers or None,
            )
            self.grok_model = os.getenv("OPENROUTER_MODEL", "x-ai/grok-beta")
            self.grok_provider = "openrouter"
            logger.info("Grok 4 configured via OpenRouter")
        else:
            logger.warning("GROK_API_KEY or OPENROUTER_API_KEY not set; Grok 4 disabled")

        # Google Gemini API client
        gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = None
        self.gemini_model_name = None
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
            self.gemini_model = genai.GenerativeModel(self.gemini_model_name)
            logger.info("Gemini configured (model: %s)", self.gemini_model_name)
        else:
            logger.warning("GEMINI_API_KEY not set")

        self.max_tokens = int(os.getenv("MAX_COMPLETION_TOKENS", "2500"))
        self.temperature = float(os.getenv("COMPLETION_TEMPERATURE", "0.2"))

    def capitalize_mentor_protege(self, text: str) -> str:
        """Ensure Mentor and Protégé are always capitalized"""
        text = re.sub(r'\bmentor\b', 'Mentor', text, flags=re.IGNORECASE)
        text = re.sub(r'\bmentors\b', 'Mentors', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprotege\b', 'Protégé', text, flags=re.IGNORECASE)
        text = re.sub(r'\bproteges\b', 'Protégés', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprotégé\b', 'Protégé', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprotégés\b', 'Protégés', text, flags=re.IGNORECASE)
        return text

    def get_bilingual_system_prompt(self, context: Optional[List[Dict]] = None, verification_pass: int = 1) -> str:
        """Generate system prompt for bilingual Spanish/English responses

        Args:
            context: Retrieved document chunks
            verification_pass: 1 for initial analysis, 2 for second verification pass
        """

        pass_description = "análisis inicial" if verification_pass == 1 else "segunda verificación"

        system_message = f"""Eres un asistente experto del Programa de Mentor-Protégé del DoD (MPP).
**PASE DE VERIFICACIÓN: {verification_pass} de 2 ({pass_description})**

**REGLAS CRÍTICAS:**
1. SIEMPRE proporciona tu respuesta PRIMERO en ESPAÑOL, luego en INGLÉS
2. SIEMPRE capitaliza "Mentor" y "Protégé" (M y P mayúsculas)
3. SIEMPRE incluye CITAS TEXTUALES EXACTAS de la documentación
4. Proporciona PÁGINA Y SECCIÓN: Página [X], Sección [X.X.X], Párrafo [X]
5. SOLO usa información de MPP SOP, DFARS Appendix I y eLearning SOP

**CAPACIDADES:**
- Responder preguntas sobre MPP SOP, DFARS Appendix I y eLearning SOP
- Analizar texto compartido por el usuario para verificar precisión
- Sugerir correcciones SOLO si hay desinformación grave Y confianza >=95%

**SI EL USUARIO COMPARTE TEXTO PARA ANALIZAR:**
1. Analiza el texto palabra por palabra contra la documentación
2. Identifica cualquier inexactitud o error
3. SOLO sugiere correcciones si:
   - Hay desinformación GRAVE (hechos incorrectos, requisitos falsos, etc.)
   - Tu confianza es >=95% basada en documentación exacta
4. Para pequeñas diferencias de redacción (<95% confianza), menciona "El texto es generalmente correcto"

**FORMATO DE RESPUESTA:**

**ESPAÑOL:**
**Respuesta:**
[Tu respuesta detallada en español]

**Citas Textuales de la Documentación:**
> "[Cita exacta del documento]"
- Fuente: [Nombre del Documento], Página [X], Sección [X.X.X] "[Título]", Párrafo [X]

**[Si se compartió texto para analizar]**
**Análisis de Precisión:**
- Estado: [Correcto / Necesita corrección]
- Confianza: [Porcentaje]%
- Problemas encontrados: [Lista de errores graves, si hay]
- Correcciones sugeridas: [Solo si confianza >=95% Y desinformación grave]

---

**ENGLISH:**
**Response:**
[Your detailed response in English]

**Exact Quotes from Documentation:**
> "[Exact quote from document]"
- Source: [Document Name], Page [X], Section [X.X.X] "[Title]", Paragraph [X]

**[If text was shared for analysis]**
**Accuracy Analysis:**
- Status: [Correct / Needs correction]
- Confidence: [Percentage]%
- Issues found: [List of serious errors, if any]
- Suggested corrections: [Only if confidence >=95% AND serious misinformation]

**NUNCA ALUCINES - Solo usa la documentación proporcionada. Incluye CITAS TEXTUALES EXACTAS para respaldar cada afirmación.**"""

        if context and len(context) > 0:
            context_text = "\n\n".join([
                f"[{item['source']}]\n{item['text']}"
                for item in context
            ])
            system_message += f"\n\n**Contexto de Documentación:**\n{context_text}"

        return system_message


    def call_grok(
        self,
        user_message: str,
        context: Optional[List[Dict]] = None,
        verification_pass: int = 1,
        previous_response: Optional[str] = None,
    ) -> str:
        """Call Grok 4 to generate or refine a response."""
        if not self.grok_client or not self.grok_model:
            raise RuntimeError("Grok 4 client is not configured.")

        try:
            pass_label = "inicial" if verification_pass == 1 else "segunda"
            provider = self.grok_provider or "unknown"
            logger.info(
                "Calling Grok 4 via %s (pass %s - %s)",
                provider,
                verification_pass,
                pass_label,
            )

            messages = [
                {
                    "role": "system",
                    "content": self.get_bilingual_system_prompt(context, verification_pass),
                },
                {"role": "user", "content": user_message},
            ]

            if verification_pass == 2 and previous_response:
                messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            "**PASE 1 COMPLETADO (referencia interna):**\n"
                            f"{previous_response}\n\n"
                            "**Realiza el Pase 2 con verificación adicional.**"
                        ),
                    }
                )

            response = self.grok_client.chat.completions.create(
                model=self.grok_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            content_text = response.choices[0].message.content
            if not content_text:
                raise RuntimeError("Grok 4 returned an empty response.")

            logger.info("Grok 4 pass %s response received", verification_pass)
            return content_text
        except Exception as exc:
            raise RuntimeError(f"Grok 4 pass {verification_pass} error: {exc}") from exc


    def call_gemini_verifier(
        self,
        user_message: str,
        grok_response: str,
        context: Optional[List[Dict]] = None,
        verification_pass: int = 1,
    ) -> str:
        """Use Gemini to validate and refine the Grok response."""
        if not self.gemini_model:
            raise RuntimeError("Gemini verification model is not configured.")

        context_block = self._build_context_section(context)
        if context_block:
            context_block = "\n" + context_block

        verification_prompt = f"""Eres Gemini {self.gemini_model_name or '2.5 Pro'}. Revisa la respuesta producida por Grok 4 durante el pase {verification_pass}.

Pregunta del usuario:
{user_message}

Respuesta de Grok 4:
{grok_response}

Instrucciones:
1. Confirma citas, páginas y secciones. Corrige cualquier inconsistencia.
2. Mantén el formato bilingüe (español primero, inglés después) con citas textuales exactas.
3. Si se analizó texto del usuario, indica estado, confianza y sugiere correcciones solo con evidencia >=95%.
4. Asegúrate de que "Mentor" y "Protégé" estén capitalizados.
5. Si falta evidencia documental, decláralo explícitamente.
{context_block}
Devuelve la respuesta final verificada en ambos idiomas siguiendo el formato solicitado (español primero, inglés después).
"""

        try:
            response = self.gemini_model.generate_content(verification_prompt)
            text_output = getattr(response, "text", "")
        except Exception as exc:
            raise RuntimeError(f"Gemini pass {verification_pass} error: {exc}") from exc

        if not text_output:
            raise RuntimeError("Gemini returned an empty response.")

        logger.info("Gemini pass %s verification complete", verification_pass)
        return text_output

    def _build_context_section(self, context: Optional[List[Dict]] = None) -> str:
        """Build context section from retrieved documents"""
        if not context or len(context) == 0:
            return ""

        context_text = "\n\n".join([
            f"[{item['source']}]\n{item['text']}"
            for item in context
        ])
        return f"**Contexto de Documentación:**\n{context_text}"

    def generate_response(self, user_message: str, context: Optional[List[Dict]] = None) -> str:
        """Generate a response using Grok 4 and optional Gemini verification."""
        if not self.grok_client:
            return (
                "Error: No generative model configured. Set GROK_API_KEY (xAI) or "
                "OPENROUTER_API_KEY in the .env file."
            )

        try:
            logger.info("=" * 80)
            logger.info("MPP Dual-Pass Pipeline")
            logger.info("Provider: Grok 4 via %s", self.grok_provider or "unconfigured")
            if self.gemini_model:
                logger.info("Verifier: Gemini %s (dual pass)", self.gemini_model_name or "2.5 Pro")
            else:
                logger.info("Verifier: Gemini (disabled)")
            logger.info("=" * 80)

            grok_pass1 = self.call_grok(user_message, context, verification_pass=1)

            if not self.gemini_model:
                logger.info("Returning Grok-only response (Gemini not configured).")
                return self.capitalize_mentor_protege(grok_pass1)

            gemini_pass1 = self.call_gemini_verifier(
                user_message, grok_pass1, context, verification_pass=1
            )
            grok_pass2 = self.call_grok(
                user_message,
                context,
                verification_pass=2,
                previous_response=gemini_pass1,
            )
            final_response = self.call_gemini_verifier(
                user_message, grok_pass2, context, verification_pass=2
            )

            logger.info("Dual-pass verification complete.")
            return self.capitalize_mentor_protege(final_response)

        except RuntimeError as exc:
            logger.error("Verification pipeline failed: %s", exc)
            return f"Error generating response: {exc}"
        except Exception as exc:
            logger.exception("Unexpected error in verification pipeline")
            return f"Error generating response: {exc}"

