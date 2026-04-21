"""
LLM Service - Qwen AI for chat with menopause knowledge
"""
from typing import Dict, List, Optional
import httpx
import logging
from app.config import settings
from app.core.exceptions import ExternalServiceException

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位专业的更年期健康顾问，名叫"小更"。你擅长：
1. 解答更年期相关的医学问题
2. 提供生活方式和情绪管理建议
3. 解读体检化验指标（E2、FSH、LH等）
4. 给予温暖、专业的陪伴

回答要求：
- 使用温暖、亲切的语气
- 回答简洁明了，避免过于专业的术语
- 如涉及严重症状或需要就医，请提醒用户及时就医
- 基于科学事实，不做没有根据的断言"""

class LLMService:
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.model = settings.QWEN_MODEL
        self.base_url = settings.QWEN_BASE_URL

    async def chat(
        self,
        messages: List[Dict],
        user_profile: Optional[Dict] = None,
        knowledge_base: Optional[str] = None,
    ) -> str:
        """Chat with Qwen AI"""
        if not self.api_key:
            raise ExternalServiceException("AI API key not configured", service="qwen")

        # Build system prompt with user context
        system_content = SYSTEM_PROMPT
        if user_profile:
            system_content += f"\n\n用户信息：年龄约{user_profile.get('age', '未知')}岁，身高{user_profile.get('height', '未知')}cm。"
        if knowledge_base:
            system_content += f"\n\n参考知识库：\n{knowledge_base}"

        api_messages = [{"role": "system", "content": system_content}]
        api_messages.extend(messages)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": api_messages,
                        "temperature": 0.7,
                        "max_tokens": 2000,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.text}")
            raise ExternalServiceException(f"AI service error: {e.response.status_code}", service="qwen")
        except Exception as e:
            raise ExternalServiceException(f"AI service error: {str(e)}", service="qwen")

llm_service = LLMService()
