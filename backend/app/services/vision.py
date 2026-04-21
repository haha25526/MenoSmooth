"""
Vision Service - OCR for lab test and health app screenshots
"""
import base64
import re
import json
import logging
from typing import Dict, Optional
import httpx
from app.config import settings
from app.core.exceptions import ExternalServiceException

logger = logging.getLogger(__name__)

class VisionService:
    def __init__(self):
        self.api_key = settings.VISION_API_KEY
        self.model = settings.VISION_MODEL
        self.base_url = settings.VISION_BASE_URL

    async def parse_lab_test(self, image_base64: str) -> Dict:
        """Parse lab test screenshot"""
        prompt = """你是专业的化验单识别助手。从图片中提取化验数据，返回 JSON。
包含的指标可能有：E2(雌二醇)、FSH(促卵泡激素)、LH(促黄体生成素)、progesterone(黄体酮)、prolactin(催乳素)、calcium(钙)、vitamin_d(维生素D)。

返回 JSON 格式：
{
    "test_date": "YYYY-MM-DD",
    "e2": 数字或null,
    "fsh": 数字或null,
    "lh": 数字或null,
    "progesterone": 数字或null,
    "prolactin": 数字或null,
    "calcium": 数字或null,
    "vitamin_d": 数字或null
}

只返回 JSON，不要其他文字。"""
        return await self._call_vision(prompt, image_base64)

    async def parse_health_screenshot(self, image_base64: str) -> Dict:
        """Parse health app screenshot"""
        prompt = """你是专业的健康数据识别助手。从截图中提取日常健康数据，返回 JSON。
包含的指标可能有：weight(体重kg)、body_fat(体脂%)、temperature(体温)、sleep_hours(睡眠时长小时)。

返回 JSON 格式：
{
    "recorded_date": "YYYY-MM-DD",
    "weight": 数字或null,
    "body_fat": 数字或null,
    "temperature": 数字或null,
    "sleep_hours": 数字或null
}

只返回 JSON，不要其他文字。"""
        return await self._call_vision(prompt, image_base64)

    async def _call_vision(self, prompt: str, image_base64: str) -> Dict:
        if not self.api_key:
            raise ExternalServiceException("Vision API key not configured", service="vision")

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        }]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                result = self._parse_json(content)
                return {"success": True, "data": result}
        except httpx.HTTPStatusError as e:
            logger.error(f"Vision API error: {e.response.text}")
            raise ExternalServiceException(f"Vision service error: {e.response.status_code}", service="vision")
        except Exception as e:
            raise ExternalServiceException(f"Vision service error: {str(e)}", service="vision")

    def _parse_json(self, content: str) -> Dict:
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content).strip()
        match = re.search(r"\{.*?\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}

vision_service = VisionService()
