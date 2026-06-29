import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "My Project"
    API_V1_STR: str = "/api/v1"

    # 腾讯企业邮 SMTP 配置（发送注册验证码邮件，账号密码从环境变量读取）
    SMTP_HOST: str = "smtp.exmail.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SENDER_NAME: str = "按时打卡"

    class Config:
        @staticmethod
        def get_env_file():
            if os.getenv("ENV") == "prod":
                return ".env.prod"
            return ".env.dev"

        env_file = get_env_file.__func__()
        extra = "allow"


settings = Settings()
