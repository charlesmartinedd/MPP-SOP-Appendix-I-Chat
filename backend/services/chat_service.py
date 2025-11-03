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
    1. Grok 4 (xAI) generates response (Spanish → English)
    2. Gemini verifies and synthesizes final answer (Spanish → English)
    """

    def __init__(self):
        # xAI Grok API client
        grok_key = os.getenv("GROK_API_KEY")
        if grok_key:
            self.grok_client = OpenAI(
                api_key=grok_key,
                base_url="https://api.x.ai/v1"
            )
            self.grok_model = os.getenv("GROK_MODEL", "grok-4-0709")
            logger.info("✓ Grok 4 configured (xAI)")
        else:
            self.grok_client = None
            logger.warning("✗ GROK_API_KEY not set")

        # Google Gemini API client
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel(
                os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
            )
            logger.info("✓ Gemini configured (Google)")
        else:
            self.gemini_model = None
            logger.warning("✗ GEMINI_API_KEY not set")

        self.max_tokens = 2500

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
- Sugerir correcciones SOLO si hay desinformación grave Y confianza ≥95%

**SI EL USUARIO COMPARTE TEXTO PARA ANALIZAR:**
1. Analiza el texto palabra por palabra contra la documentación
2. Identifica cualquier inexactitud o error
3. SOLO sugiere correcciones si:
   - Hay desinformación GRAVE (hechos incorrectos, requisitos falsos, etc.)
   - Tu confianza es ≥95% basada en documentación exacta
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
- Correcciones sugeridas: [Solo si confianza ≥95% Y desinformación grave]

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
- Suggested corrections: [Only if confidence ≥95% AND serious misinformation]

**NUNCA ALUCINES - Solo usa la documentación proporcionada. Incluye CITAS TEXTUALES EXACTAS para respaldar cada afirmación.**"""

        if context and len(context) > 0:
            context_text = "\n\n".join([
                f"[{item['source']}]\n{item['text']}"
                for item in context
            ])
            system_message += f"\n\n**Contexto de Documentación:**\n{context_text}"

        return system_message

    def call_grok(self, user_message: str, context: Optional[List[Dict]] = None, verification_pass: int = 1, previous_response: str = None) -> str:
        """Call Grok 4 via xAI API

        Args:
            user_message: User's question
            context: Retrieved document chunks
            verification_pass: 1 for initial, 2 for second verification
            previous_response: Response from previous verification pass
        """
        if not self.grok_client:
            return "Error: Grok 4 no configurado"

        try:
            pass_label = "inicial" if verification_pass == 1 else "segunda"
            logger.info(f"🤖 Calling Grok 4 (xAI) - Pase {verification_pass} ({pass_label})...")

            messages = [
                {"role": "system", "content": self.get_bilingual_system_prompt(context, verification_pass)},
                {"role": "user", "content": user_message}
            ]

            # For second pass, include previous verification results
            if verification_pass == 2 and previous_response:
                messages.append({
                    "role": "assistant",
                    "content": f"**PASE 1 COMPLETADO:**\n{previous_response}\n\n**AHORA REALIZANDO PASE 2 DE VERIFICACIÓN...**"
                })

            response = self.grok_client.chat.completions.create(
                model=self.grok_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.2
            )
            result = response.choices[0].message.content
            logger.info(f"✓ Grok 4 Pase {verification_pass} response received")
            return result
        except Exception as e:
            logger.error(f"✗ Grok 4 Pase {verification_pass} error: {str(e)}")
            return f"Error en Grok 4 Pase {verification_pass}: {str(e)}"

    def call_gemini_verifier(self, user_message: str, grok_response: str, context: Optional[List[Dict]] = None, verification_pass: int = 1) -> str:
        """Call Gemini to verify and enhance Grok's response

        Args:
            user_message: User's question
            grok_response: Grok's response to verify
            context: Retrieved document chunks
            verification_pass: 1 for first verification, 2 for second verification
        """
        if not self.gemini_model:
            return "Error: Gemini no configurado"

        try:
            pass_label = "primera" if verification_pass == 1 else "segunda"
            logger.info(f"🤖 Calling Gemini Verifier (Google) - Pase {verification_pass} ({pass_label})...")

            verification_prompt = f"""Eres un verificador experto del Programa de Mentor-Protégé del DoD (MPP).
**PASE DE VERIFICACIÓN GEMINI: {verification_pass} de 2 ({pass_label} verificación)**

Se te ha proporcionado una respuesta de Grok 4 a una pregunta del usuario. Tu trabajo es:
1. Verificar la precisión de la respuesta contra la documentación
2. Verificar que todas las citas sean EXACTAS y TEXTUALES
3. Verificar que se incluyan PÁGINA Y SECCIÓN (Página [X], Sección [X.X.X], Párrafo [X])
4. Si el usuario compartió texto para analizar, verificar el análisis de precisión de Grok 4
5. Validar que las correcciones sugeridas cumplan: confianza ≥95% Y desinformación grave
6. Mejorar la respuesta si es necesario
7. Proporcionar la respuesta final PRIMERO en ESPAÑOL, luego en INGLÉS

**PREGUNTA DEL USUARIO:**
{user_message}

**RESPUESTA DE GROK 4 (PASE {verification_pass}):**
{grok_response}

**DOCUMENTACIÓN DE REFERENCIA:**
{chr(10).join([f"[{item['source']}] {item['text']}" for item in context]) if context else "No se proporcionó contexto"}

**INSTRUCCIONES CRÍTICAS:**
1. Analiza la respuesta de Grok 4 cuidadosamente
2. Verifica contra la documentación palabra por palabra
3. Asegúrate de que las citas sean TEXTUALES (no parafraseadas)
4. Verifica que incluya Página Y Sección en cada cita
5. Si hay análisis de texto compartido, confirma que:
   - Las correcciones sugeridas son necesarias (desinformación grave)
   - La confianza declarada es ≥95% con evidencia documental sólida
   - Si confianza <95%, NO sugerir correcciones (solo mencionar "generalmente correcto")
6. Proporciona una respuesta final mejorada y verificada
7. Usa el formato con ESPAÑOL PRIMERO, luego INGLÉS
8. SIEMPRE capitaliza "Mentor" y "Protégé"

**FORMATO DE RESPUESTA FINAL:**

**ESPAÑOL:**
**Respuesta Verificada (Pase {verification_pass}):**
[Tu respuesta verificada y mejorada en español]

**Citas Textuales Verificadas:**
> "[Cita exacta del documento]"
- Fuente: [Nombre del Documento], Página [X], Sección [X.X.X] "[Título]", Párrafo [X]

**[Si se analizó texto compartido]**
**Análisis de Precisión Verificado:**
- Estado: [Correcto / Necesita corrección]
- Confianza: [Porcentaje]%
- Problemas confirmados: [Solo errores graves verificados]
- Correcciones finales: [Solo si ≥95% confianza Y grave]

---

**ENGLISH:**
**Verified Response (Pass {verification_pass}):**
[Your verified and improved response in English]

**Verified Exact Quotes:**
> "[Exact quote from document]"
- Source: [Document Name], Page [X], Section [X.X.X] "[Title]", Paragraph [X]

**[If shared text was analyzed]**
**Verified Accuracy Analysis:**
- Status: [Correct / Needs correction]
- Confidence: [Percentage]%
- Confirmed issues: [Only verified serious errors]
- Final corrections: [Only if ≥95% confidence AND serious]

**VERIFICACIÓN GEMINI (PASE {verification_pass}):**
- Precisión de Grok 4: [alta/media/baja]
- Citas verificadas: [número de citas verificadas]
- Páginas y secciones confirmadas: [Sí/No]
- Análisis de texto validado: [Si aplica - confianza y correcciones apropiadas]
- Mejoras realizadas: [cualquier observación importante]
"""

            response = self.gemini_model.generate_content(verification_prompt)
            result = response.text
            logger.info(f"✓ Gemini Pase {verification_pass} verification complete")
            return result
        except Exception as e:
            logger.error(f"✗ Gemini Pase {verification_pass} error: {str(e)}")
            return f"Error en Gemini Pase {verification_pass}: {str(e)}"

    def generate_response(self, user_message: str, context: Optional[List[Dict]] = None) -> str:
        """Generate response using Dual-Pass Dual AI Verification

        Flow:
        PASS 1:
        1. Grok 4 initial analysis with exact quotes
        2. Gemini 2.5 Pro verification #1

        PASS 2:
        3. Grok 4 second analysis (reviewing Pass 1 results)
        4. Gemini 2.5 Pro final verification #2

        Both AIs verify TWICE before reaching final agreement.
        """

        if not self.grok_client and not self.gemini_model:
            return "Error: No AI models configured. Please set API keys in .env file."

        try:
            logger.info("=" * 80)
            logger.info("DUAL-PASS DUAL AI VERIFICATION SYSTEM")
            logger.info("Grok 4 + Gemini 2.5 Pro - Each AI Verifies TWICE")
            logger.info("=" * 80)

            # ============================================================
            # PASS 1: Initial Analysis and First Verification
            # ============================================================
            logger.info("\n" + "=" * 80)
            logger.info("PASS 1: INITIAL ANALYSIS AND FIRST VERIFICATION")
            logger.info("=" * 80)

            # Step 1: Grok 4 initial analysis (Pass 1)
            grok_pass1 = self.call_grok(user_message, context, verification_pass=1)

            # Step 2: Gemini first verification (Pass 1)
            gemini_pass1 = self.call_gemini_verifier(user_message, grok_pass1, context, verification_pass=1)

            # ============================================================
            # PASS 2: Second Analysis and Final Verification
            # ============================================================
            logger.info("\n" + "=" * 80)
            logger.info("PASS 2: SECOND ANALYSIS AND FINAL VERIFICATION")
            logger.info("=" * 80)

            # Step 3: Grok 4 second analysis (Pass 2) - reviews Pass 1 results
            grok_pass2 = self.call_grok(user_message, context, verification_pass=2, previous_response=gemini_pass1)

            # Step 4: Gemini final verification (Pass 2)
            final_response = self.call_gemini_verifier(user_message, grok_pass2, context, verification_pass=2)

            logger.info("\n" + "=" * 80)
            logger.info("✓ DUAL-PASS VERIFICATION COMPLETE")
            logger.info("Both Grok 4 and Gemini 2.5 Pro have verified TWICE")
            logger.info("=" * 80)

            # Ensure capitalization
            formatted_response = self.capitalize_mentor_protege(final_response)

            return formatted_response

        except Exception as e:
            logger.error(f"Error in dual-pass verification: {str(e)}")
            return f"Error generating response: {str(e)}"
