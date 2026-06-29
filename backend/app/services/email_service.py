import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from ..core.config import settings
from ..utils.logger import logger


class Email:
    """
    邮箱操作类（封装邮件发送功能）
    --------------------------------------------------------------------------
    - 使用 SMTP 协议经腾讯企业邮（smtp.exmail.qq.com:465 SSL）发送邮件
    - 源邮箱地址、授权码从环境变量读取（SMTP_USER / SMTP_PASSWORD）
    - 当前主要用途：注册时向用户邮箱发送验证码
    """

    def __init__(self) -> None:
        self.host: str = settings.SMTP_HOST
        self.port: int = settings.SMTP_PORT
        self.user: str = settings.SMTP_USER
        self.password: str = settings.SMTP_PASSWORD
        self.sender_name: str = settings.SMTP_SENDER_NAME

    def send_verification_code(self, to_email: str, code: str) -> None:
        """
        发送注册验证码邮件
        :param to_email: 收件人邮箱（用户注册表单中填写的电子邮箱）
        :param code:     6 位数字验证码
        """
        if not self.user or not self.password:
            # 源邮箱未配置，给出明确提示
            raise ValueError(
                "SMTP 邮箱未配置，请在 .env 中设置 SMTP_USER 与 SMTP_PASSWORD（腾讯企业邮账号与客户端专用密码）"
            )

        subject = "【按时打卡】注册验证码"
        content = (
            "您正在注册「按时打卡」账号，验证码为：\n\n"
            f"    {code}\n\n"
            "验证码有效期为 5 分钟，请勿泄露给他人。如非本人操作，请忽略本邮件。"
        )

        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr((self.sender_name, self.user))
        msg["To"] = to_email

        try:
            # 腾讯企业邮使用 SSL（端口 465）
            with smtplib.SMTP_SSL(self.host, self.port, timeout=10) as server:
                server.login(self.user, self.password)
                server.sendmail(self.user, [to_email], msg.as_string())
            logger.info(f"验证码邮件发送成功：{to_email}")
        except Exception as e:
            logger.error(f"验证码邮件发送失败：{to_email}，错误：{e}")
            raise RuntimeError(f"邮件发送失败：{e}")
