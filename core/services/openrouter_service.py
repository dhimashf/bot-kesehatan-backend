# src/services/openrouter_service.py
import httpx
import logging
import os
import sys
import asyncio
from typing import Optional, Dict

from common.config.settings import settings
from common.utils.text_utils import TextUtils
from common.data.kitab_loader import kitab_loader
from core.services.rag_service import rag_service

logger = logging.getLogger(__name__)

class OpenRouterService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.api_url = settings.OPENROUTER_API_URL

        self.available_models = [
            "deepseek/deepseek-r1",
            "deepseek/deepseek-chat-v3.1",
            "deepseek/deepseek-chat-v3-0324",
            "deepseek/deepseek-r1-0528",
        ]
        self.default_model = "deepseek/deepseek-r1"

    def build_profile_context(self, profile: Dict) -> str:
        """Build context string dari hasil survey profil user (WHO-5, GAD-7, MBI, NAQ-R, K10)"""
        # The new profile structure has 'biodata' and 'health_results'
        if not profile or not profile.get("health_results"):
            return ""

        from core.services.profiling_service import profiling_service

        context_parts = []
        
        # Use the latest health result for context
        latest_result = profile["health_results"][0] if profile["health_results"] else None
        if not latest_result:
            return ""

        # WHO-5
        total_who5, category_who5 = profiling_service.get_who5_result([latest_result['who5_total']])
        context_parts.append(f"WHO-5 Well-Being Index: Skor {total_who5}/30, Kategori: {category_who5}")

        # GAD-7
        total_gad7, category_gad7 = profiling_service.get_gad7_result([latest_result['gad7_total']])
        context_parts.append(f"GAD-7 (Kecemasan): Skor {total_gad7}/21, Kategori: {category_gad7}")

        # MBI
        mbi_ee_cat = profiling_service.get_mbi_category('emosional', latest_result['mbi_emosional_total'])
        mbi_cyn_cat = profiling_service.get_mbi_category('sinis', latest_result['mbi_sinis_total'])
        mbi_pa_cat = profiling_service.get_mbi_category('pencapaian', latest_result['mbi_pencapaian_total'])
        context_parts.append(
            f"MBI (Burnout): Kelelahan Emosional {latest_result['mbi_emosional_total']} ({mbi_ee_cat}), "
            f"Sinis {latest_result['mbi_sinis_total']} ({mbi_cyn_cat}), "
            f"Pencapaian Pribadi {latest_result['mbi_pencapaian_total']} ({mbi_pa_cat})"
        )

        # NAQ-R
        naqr_total = latest_result['naqr_pribadi_total'] + latest_result['naqr_pekerjaan_total'] + latest_result['naqr_intimidasi_total']
        context_parts.append(
            f"NAQ-R (Perundungan): Pribadi {latest_result['naqr_pribadi_total']}, "
            f"Pekerjaan {latest_result['naqr_pekerjaan_total']}, "
            f"Intimidasi {latest_result['naqr_intimidasi_total']}, "
            f"Total {naqr_total}"
        )

        # K10
        total_k10, category_k10 = profiling_service.get_k10_result([latest_result['k10_total']])
        context_parts.append(f"K10 (Distres Psikososial): Skor {total_k10}/50, Kategori: {category_k10}")

        return "\n".join(context_parts)

    async def get_Psiko_answer(self, question: str, profile: Optional[Dict] = None) -> Optional[str]:
        try:
            logger.info(f"Processing question: {question}")

            # Get RAG context
            kitab_context = ""
            try:
                kitab_context = rag_service.get_context_for_question(question, top_k=5, max_chars=1500)
                logger.info(f"RAG context length: {len(kitab_context)}")
            except Exception as e:
                logger.warning(f"RAG failed: {e}")
                if kitab_loader.paragraphs:
                    kitab_context = " ".join(kitab_loader.paragraphs[:5])

            # Build profile context
            profile_context = self.build_profile_context(profile) if profile else ""

            # If question not Psiko and no context found -> reject politely
            if not TextUtils.is_psikologi_related(question) and (not kitab_context or kitab_context.strip().lower().startswith("data kitab")):
                return "Maaf, saya hanya bisa menjawab pertanyaan seputar Psikologi atau konten yang ada di kitab yang tersedia."

            # Try default model then fallbacks
            try:
                answer = await self._make_api_request(question, kitab_context, profile_context, self.default_model)
                logger.info(f"Default model answer length: {len(answer) if answer else 0}")
                if answer and not answer.startswith("Maaf"):
                    return answer
            except Exception as e:
                logger.warning(f"Default model failed: {e}")

            for model in self.available_models:
                if model == self.default_model:
                    continue
                try:
                    answer = await self._make_api_request(question, kitab_context, profile_context, model)
                    if answer and not answer.startswith("Maaf"):
                        return answer
                except Exception as e:
                    logger.warning(f"Fallback {model} failed: {e}")
                    continue

            return "Maaf, saat ini tidak dapat terhubung ke AI service. Silakan coba lagi nanti."

        except Exception as e:
            logger.exception(f"Error in get_Psiko_answer: {e}")
            return "Maaf, terjadi kesalahan sistem. Silakan coba lagi."

    async def _make_api_request(self, question: str, kitab_context: str, profile_context: str, model: str, retries: int = 3) -> str:
        system_prompt = """
Kamu adalah Chatbot Psikologi dan Kesehatan yang membantu user memahami isu-isu psikologi, kesehatan mental, dan kesejahteraan.

Aturan menjawab:
1. Jika pertanyaan sesuai dengan konteks psikologi atau kesehatan, jawab berdasarkan data yang sudah dimuat dari kitab.pdf.
2. Jika pertanyaan tidak murni psikologi/kesehatan, tapi ada jawaban relevan di kitab.pdf, tetap jawab dengan jelas.
3. Jika pertanyaan benar-benar di luar konteks data, jawab dengan sopan bahwa bot ini hanya fokus pada psikologi dan kesehatan sesuai data yang tersedia.
4. Sertakan sumber jika jawaban diambil dari kitab.pdf.
5. PENTING: Sesuaikan gaya bahasa dan kedalaman penjelasan dengan profil user yang diberikan (hasil survey WHO-5, GAD-7, MBI, NAQ-R, K10).
"""

        # Tambahkan profile context ke system prompt
        if profile_context:
            system_prompt += f"\n\nProfil User:\n{profile_context}"

        user_prompt = f"""
Pertanyaan: {question}

Konteks relevan (diambil dari kitab):
{kitab_context if kitab_context else '[Tidak ada konteks relevan dari kitab]'}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.2,
            "top_p": 0.9,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Psiko-bot",
            "X-Title": "Chatbot Psiko Indonesia"
        }

        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    logger.info(f"Sending request to OpenRouter model={model} attempt={attempt}")
                    response = await client.post(self.api_url, json=payload, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        raw_answer = data["choices"][0]["message"]["content"]
                        formatted = TextUtils.format_response(raw_answer)
                        return formatted if formatted else raw_answer
                    elif response.status_code == 429:
                        logger.warning(f"Rate limited (429) on attempt {attempt}")
                        if attempt < retries:
                            await asyncio.sleep(2 * attempt)
                            continue
                        else:
                            return ""
                    else:
                        logger.error(f"OpenRouter error {response.status_code}: {response.text}")
                        return ""
            except httpx.TimeoutException:
                logger.warning("Timeout, retrying...")
                if attempt < retries:
                    await asyncio.sleep(2 * attempt)
                    continue
                return ""
            except Exception as e:
                logger.exception(f"Request error: {e}")
                return ""
        return ""

# singleton
openrouter_service = OpenRouterService()