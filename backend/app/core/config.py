from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

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

    # 友盟+ U-Push 配置（App 端离线推送，Android / iOS 各一套应用密钥）
    # 在友盟+ 控制台 → U-Push → 应用管理中获取 AppKey 与 App Master Secret
    UMENG_ANDROID_APP_KEY: str = ""
    UMENG_ANDROID_MASTER_SECRET: str = ""
    UMENG_IOS_APP_KEY: str = ""
    UMENG_IOS_MASTER_SECRET: str = ""
    # 推送环境开关：true=生产环境，false=测试环境
    # 仅 iOS 生效（决定走 APNs 生产证书还是开发证书）；Android 侧友盟忽略该字段
    UMENG_PRODUCTION_MODE: bool = True
    # 点击 App 推送通知后跳转的页面路径（#ifdef APP-PLUS 由前端 reLaunch 使用）
    UMENG_PUSH_PAGE: str = "/pages/index/index"

    # 数据加密密钥（AES-256-GCM，base64 编码的 32 字节密钥）
    # 用于加密邮件客户端专用密码等敏感信息
    ENCRYPTION_SECRET_KEY: str = ""

    # JWT 认证配置（用户登录态签名密钥与过期时间）
    JWT_SECRET_KEY: str = ""
    JWT_EXPIRE_DAYS: int = 7

    # CORS 允许的源（逗号分隔，如 "https://yao.wuzuniao.com,http://localhost:8000"）
    # 微信小程序请求不携带 Origin 头，不受 CORS 限制；此项主要约束 Web 端访问
    # 实际值从 .env 文件读取，此处为开发环境默认值
    CORS_ALLOW_ORIGINS: str = "https://yao.wuzuniao.com,http://localhost:8000"

    @property
    def cors_origins_list(self) -> list[str]:
        """解析 CORS_ALLOW_ORIGINS 为列表（去除空白与重复项）"""
        return list(dict.fromkeys(
            origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",") if origin.strip()
        ))

    model_config = SettingsConfigDict(
        env_file=str(_BASE_DIR / ".env"),
        extra="allow",
    )


settings = Settings()
