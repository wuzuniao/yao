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

    # 微信订阅消息配置（一次性订阅模板，用于打卡提醒下发）
    # 模板 ID 非机密信息，可在微信公众平台「订阅消息」中查看
    WX_SUBSCRIBE_TEMPLATE_ID: str = ""
    # 点击订阅消息后跳转的小程序页面路径
    WX_SUBSCRIBE_PAGE: str = "/pages/index/index"
    # 订阅消息「机构名称」字段（thing12）展示值
    WX_SUBSCRIBE_ORG_NAME: str = "无足鸟"

    # 数据加密密钥（AES-256-GCM，base64 编码的 32 字节密钥）
    # 用于加密邮件客户端专用密码等敏感信息
    ENCRYPTION_SECRET_KEY: str = ""

    # JWT 认证配置（用户登录态签名密钥与过期时间）
    JWT_SECRET_KEY: str = ""
    JWT_EXPIRE_DAYS: int = 7

    class Config:
        env_file = str(_BASE_DIR / ".env")
        extra = "allow"


settings = Settings()
