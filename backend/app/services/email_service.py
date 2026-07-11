import base64
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from ..core.config import settings
from ..utils.logger import logger


class Email:
    """
    邮箱操作类（封装邮件发送功能）
    --------------------------------------------------------------------------
    - send_verification_code：使用系统腾讯企业邮（smtp.exmail.qq.com:465 SSL）发送验证码
    - send_notification：使用用户自配 SMTP（notification_channels.channel_value）发送打卡通知
    """

    def __init__(self) -> None:
        self.host: str = settings.SMTP_HOST
        self.port: int = settings.SMTP_PORT
        self.user: str = settings.SMTP_USER
        self.password: str = settings.SMTP_PASSWORD
        self.sender_name: str = settings.SMTP_SENDER_NAME

    @staticmethod
    def _smtp_authenticate(server: smtplib.SMTP, user: str, password: str) -> None:
        """
        单次 SMTP 认证（避免 login() 多方式重试掩盖真实错误）

        背景：smtplib 的 login() 会依次尝试 AUTH PLAIN → AUTH LOGIN。QQ 邮箱等
        服务商在 AUTH PLAIN 返回 535 后会直接关闭连接，导致 login() 继续尝试
        AUTH LOGIN 时抛出 SMTPServerDisconnected，掩盖真实的 535 认证失败信息。

        本方法优先使用 PLAIN、其次 LOGIN，只尝试一次，认证失败直接抛出
        SMTPAuthenticationError（含服务器返回的真实错误码与提示）。
        若服务器未声明认证方式（罕见），退回 login()。
        """
        server.ehlo_or_helo_if_needed()
        # Python 3.14 移除了 esmtp_auth 属性，改从 esmtp_features["auth"] 解析
        auth_str = server.esmtp_features.get("auth", "")
        methods = auth_str.split() if auth_str else []

        # 优先 PLAIN：一次性发送凭证，兼容主流邮箱
        if "PLAIN" in methods:
            payload = base64.b64encode(f"\0{user}\0{password}".encode("utf-8")).decode("ascii")
            code, resp = server.docmd("AUTH", "PLAIN " + payload)
            if code == 235:
                return
            raise smtplib.SMTPAuthenticationError(code, resp)

        # 其次 LOGIN：分两步发送用户名与密码
        if "LOGIN" in methods:
            code, resp = server.docmd("AUTH", "LOGIN")
            if code != 334:
                raise smtplib.SMTPAuthenticationError(code, resp)
            code, resp = server.docmd(base64.b64encode(user.encode("utf-8")).decode("ascii"))
            if code != 334:
                raise smtplib.SMTPAuthenticationError(code, resp)
            code, resp = server.docmd(base64.b64encode(password.encode("utf-8")).decode("ascii"))
            if code == 235:
                return
            raise smtplib.SMTPAuthenticationError(code, resp)

        # 服务器未声明认证方式（罕见），退回 login()
        server.login(user, password)

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
                self._smtp_authenticate(server, self.user, self.password)
                server.sendmail(self.user, [to_email], msg.as_string())
            logger.info(f"验证码邮件发送成功：{to_email}")
        except smtplib.SMTPAuthenticationError as e:
            err_detail = e.smtp_error.decode("utf-8", errors="replace") if e.smtp_error else str(e)
            logger.error(f"验证码邮件发送失败：{to_email}，SMTP 认证失败（{e.smtp_code}）：{err_detail}")
            raise RuntimeError(f"邮件发送失败：SMTP 认证失败（{e.smtp_code}）：{err_detail}")
        except Exception as e:
            logger.error(f"验证码邮件发送失败：{to_email}，错误：{e}")
            raise RuntimeError(f"邮件发送失败：{e}")

    def send_notification(
        self,
        to_email: str,
        subject: str,
        content: str,
        smtp_host: str,
        smtp_port: int,
        from_email: str,
        smtp_password: str,
    ) -> None:
        """
        使用用户自配 SMTP 发送打卡通知邮件（供 SchedulerService 调用）
        - 发件人 = from_email（channel_value.email，即 SMTP 登录账号）
        - 收件人 = to_email（users.email，即用户绑定的邮箱）
        - 端口 465 走 SSL，其他端口走 STARTTLS（兼容主流邮箱）
        :raises RuntimeError: SMTP 连接或发送失败
        """
        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr((self.sender_name, from_email))
        msg["To"] = to_email

        try:
            if smtp_port == 465:
                # SSL 直连（如腾讯企业邮、QQ 邮箱）
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                    self._smtp_authenticate(server, from_email, smtp_password)
                    server.sendmail(from_email, [to_email], msg.as_string())
            else:
                # STARTTLS（如 Gmail 587、Outlook 587）
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.starttls()
                    self._smtp_authenticate(server, from_email, smtp_password)
                    server.sendmail(from_email, [to_email], msg.as_string())
            logger.info(f"打卡通知邮件发送成功：{from_email} -> {to_email}")
        except smtplib.SMTPAuthenticationError as e:
            err_detail = e.smtp_error.decode("utf-8", errors="replace") if e.smtp_error else str(e)
            logger.error(f"打卡通知邮件发送失败：{from_email} -> {to_email}，SMTP 认证失败（{e.smtp_code}）：{err_detail}")
            raise RuntimeError(f"邮件发送失败：SMTP 认证失败（{e.smtp_code}）：{err_detail}")
        except Exception as e:
            logger.error(f"打卡通知邮件发送失败：{from_email} -> {to_email}，错误：{e}")
            raise RuntimeError(f"邮件发送失败：{e}")
