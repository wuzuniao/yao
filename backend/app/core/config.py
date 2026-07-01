from pathlib import Path
from pydantic_settings import BaseSettings

# backend/ 目录（config.py 位于 backend/app/core/），用于按绝对路径定位 .env 文件
_BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "无足鸟按时吃药打卡"
    API_V1_STR: str = "/api/v1"

    # 腾讯企业邮 SMTP 配置（发送注册验证码邮件，账号密码从环境变量读取）
    SMTP_HOST: str = "smtp.exmail.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SENDER_NAME: str = "无足鸟"

    # 微信小程序配置（用于微信一键登录）
    WX_APPID: str = ""
    WX_APP_SECRET: str = ""

    # 数据加密密钥（AES-256-GCM，base64 编码的 32 字节密钥）
    # 用于加密邮件客户端专用密码等敏感信息
    ENCRYPTION_SECRET_KEY: str = ""

    class Config:
        env_file = str(_BASE_DIR / ".env")
        extra = "allow"


settings = Settings()
