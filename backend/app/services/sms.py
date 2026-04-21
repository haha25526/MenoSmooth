"""
SMS Service - Send verification codes
"""
import random
import httpx
import hashlib
import time
from app.config import settings
from app.core.exceptions import ExternalServiceException

# 测试账号固定验证码
TEST_ACCOUNTS = {
    "13712345678": "1234",
}

class SMSService:
    async def send_verification_code(self, phone: str, code: str) -> bool:
        if settings.SMS_PROVIDER == 'aliyun':
            return await self._send_aliyun(phone, code)
        return False

    async def _send_aliyun(self, phone: str, code: str) -> bool:
        url = "https://dysmsapi.aliyuncs.com/"
        params = {
            "Action": "SendSms",
            "Version": "2017-05-25",
            "AccessKeyId": settings.ALIYUN_ACCESS_KEY_ID,
            "Format": "JSON",
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "SignatureVersion": "1.0",
            "SignatureNonce": str(random.randint(10000000, 99999999)),
            "PhoneNumbers": phone,
            "SignName": settings.ALIYUN_SMS_SIGN_NAME,
            "TemplateCode": settings.ALIYUN_SMS_TEMPLATE_CODE,
            "TemplateParam": f'{{"code":"{code}"}}',
        }
        sign_string = "&".join([f"{k}={self._url_encode(v)}" for k, v in sorted(params.items())])
        sign_string = "GET&%2F&" + self._url_encode(sign_string)
        signature = self._hmac_sha1(sign_string, settings.ALIYUN_ACCESS_KEY_SECRET + "&")
        params["Signature"] = signature
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                response = await client.get(url, params=params, timeout=10.0)
                return response.json().get("Code") == "OK"
        except Exception as e:
            print(f"SMS send failed: {e}")
            return False

    @staticmethod
    def generate_code(length: int = 4) -> str:
        return "".join([str(random.randint(0, 9)) for _ in range(length)])

    @staticmethod
    def _url_encode(s: str) -> str:
        import urllib.parse
        return urllib.parse.quote(str(s), safe="")

    @staticmethod
    def _hmac_sha1(data: str, key: str) -> str:
        import hmac
        import base64
        return base64.b64encode(hmac.new(key.encode(), data.encode(), hashlib.sha1).digest()).decode()

sms_service = SMSService()
