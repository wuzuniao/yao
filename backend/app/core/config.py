from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录（config.py 位于 backend/app/core/），用于按绝对路径定位 .env 文件
_BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "无足鸟按时吃药打卡"
    API_V1_STR: str = "/api/v1"

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

    # 友盟+ U-Push 配置（App 端离线推送，Android / iOS / Harmony 各一套应用密钥）
    # 在友盟+ 控制台 → U-Push → 应用管理中获取 AppKey 与 App Master Secret
    UMENG_ANDROID_APP_KEY: str = ""
    UMENG_ANDROID_MASTER_SECRET: str = ""
    UMENG_IOS_APP_KEY: str = ""
    UMENG_IOS_MASTER_SECRET: str = ""
    # 鸿蒙（HarmonyOS）在友盟+ 控制台作为独立应用创建，复用同一推送接口，密钥单独一套
    UMENG_HARMONY_APP_KEY: str = ""
    UMENG_HARMONY_MASTER_SECRET: str = ""
    # 推送环境开关：true=生产环境，false=测试环境
    # 仅 iOS 生效（决定走 APNs 生产证书还是开发证书）；Android / Harmony 侧友盟忽略该字段
    UMENG_PRODUCTION_MODE: bool = True
    # 点击 App 推送通知后跳转的页面路径（#ifdef APP 由前端 reLaunch 使用）
    UMENG_PUSH_PAGE: str = "/pages/index/index"

    # 数据加密密钥（AES-256-GCM，base64 编码的 32 字节密钥）
    # 用于加密邮件客户端专用密码等敏感信息
    ENCRYPTION_SECRET_KEY: str = ""

    # ==================== auth 统一认证服务配置 ====================
    # auth 服务基础地址（用户模块独立部署后，本服务经域名调用其 /internal/* 接口）
    # 开发环境：http://localhost:10000；生产环境：https://auth.wuzuniao.com
    AUTH_BASE_URL: str = "https://auth.wuzuniao.com"
    # 令牌签发方标识（须与 auth 服务 .env 的 ISSUER 完全一致，否则验签不通过）
    AUTH_ISSUER: str = "https://auth.wuzuniao.com"
    # 服务间通信令牌（调用 auth /internal/* 时携带的 X-Service-Token；
    # 与 auth 服务 .env 的 SERVICE_TOKEN 一致）
    AUTH_SERVICE_TOKEN: str = ""
    # 本项目在 auth oauth_clients 表登记的第一方 client_id
    # （删除上报 purge-report 时携带，auth 按第一方 client 集合判定收齐）
    AUTH_CLIENT_ID: str = "yao"
    # 令牌撤销增量同步间隔（秒）：后台循环每该间隔拉取一次 auth 的撤销日志，
    # 决定「改密码/退出/删号后旧令牌在本服务的最大残留窗口」
    REVOCATION_SYNC_INTERVAL_SECONDS: int = 300

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
