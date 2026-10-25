import base64
import html
import re
import smtplib
import socket
import ssl
from email.mime.text import MIMEText
from email.utils import formataddr

from ..core.config import settings
from ..core.security import Security
from ..utils.logger import logger

# 邮件头值净化：换行替换为空格（存量数据可能含换行，compat32 MIMEText 不拦截头注入）
_HEADER_NEWLINES = re.compile(r"[\r\n]+")

# TLS 校验上下文（证书链 + 主机名校验）：显式传入两处 TLS 握手——
# smtplib 默认 context（ssl._create_stdlib_context）不校验证书（2026-10-25 安全加固）
_TLS_CONTEXT = ssl.create_default_context()


class _PinnedSMTP(smtplib.SMTP):
    """
    按已校验解析 IP 固定建连的 SMTP 客户端（2026-10-25 安全加固，防 DNS rebinding）：
    - 建连 IP 由 Security.validate_smtp_target 校验并返回，直连该 IP，
      消除「校验时解析/实连时再解析」两次独立 DNS 解析的换绑间隙
    - TLS 握手仍按主机名做 SNI 与证书校验（smtplib 以 self._host 作 server_hostname）
    """

    def __init__(self, hostname: str, pinned_ip: str, port: int, timeout: float) -> None:
        self._pinned_ip = pinned_ip
        super().__init__(host=hostname, port=port, timeout=timeout)

    def _get_socket(self, host, port, timeout):
        # 不对 host 二次 DNS 解析，直连已校验 IP
        return socket.create_connection((self._pinned_ip, port), timeout=timeout)


class _PinnedSMTPSSL(smtplib.SMTP_SSL):
    """同 _PinnedSMTP，465 SSL 直连场景（TLS 层按主机名校验证书）"""

    def __init__(self, hostname: str, pinned_ip: str, port: int, timeout: float) -> None:
        self._pinned_ip = pinned_ip
        super().__init__(host=hostname, port=port, timeout=timeout, context=_TLS_CONTEXT)

    def _get_socket(self, host, port, timeout):
        new_socket = socket.create_connection((self._pinned_ip, port), timeout=timeout)
        # 镜像 SMTP_SSL._get_socket：用 self.context 包 TLS，server_hostname 为主机名
        return self.context.wrap_socket(new_socket, server_hostname=self._host)


def _mask_email(email: str) -> str:
    """邮箱脱敏（写日志用，2026-10-25 安全修复：日志不留 PII 原文）：保留首字符与域名"""
    if "@" not in email:
        return email[:1] + "***"
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}"


class Email:
    """
    邮箱操作类（封装打卡通知邮件发送）
    --------------------------------------------------------------------------
    - send_notification：使用用户自配 SMTP（notification_channels.channel_value）发送打卡通知
    - 验证码邮件已随用户模块迁移至 auth 服务（其 email_service.send_verification_code）
    """

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
        _ = server.login(user, password)

    def send_notification(
        self,
        to_email: str,
        subject: str,
        fields: list[tuple[str, str, bool]],
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

        正文按"结构化字段"逐项渲染（参考验证码邮件样式，遵循 DESIGN-vercel.md 的 Geist 设计规范）：
        - fields 为 (字段名, 值, 是否加粗) 三元组列表；字段名用 mute 色 500 衬底，
          加粗值用 ink 色 600 突出（突出通知内容），不加粗值用正文灰色 400（如备注说明）。
        - 值可含多行（如备注）：整体作为该字段的值渲染，换行转 <br>——
          多行内容中即使含冒号也不会被误拆为新字段（旧版按行+冒号切分的协议已废弃）。
        - 字段行统一置于 hairline-soft 高亮容器内，前后各附一句引导与提示语。
        :raises RuntimeError: SMTP 连接或发送失败
        """
        # 发信端 SSRF 兜底闸门：API 层创建/更新已校验，此处覆盖存量数据与任何绕过路径
        # （send_notification 由调度器经线程池调用，阻塞 DNS 查询无碍事件循环）；
        # 返回通过校验的解析 IP，建连固定直连该 IP（防 DNS rebinding TOCTOU）
        pinned_ip = Security.validate_smtp_target(smtp_host)
        Security.validate_smtp_port(smtp_port)

        home_url = "https://www.wuzuniao.com"
        logo_url = "https://www.wuzuniao.com/images/logo_wuzuniao_com_s.png"

        # 逐字段渲染：字段名：值；值转义后换行转 <br>，按加粗标志选择值样式
        p_style = "margin:0 0 8px;font-size:14px;font-weight:400;line-height:20px;color:#4d4d4d;"
        field_rows: list[str] = []
        for label, value, bold in fields:
            value_html = html.escape(value or "").replace("\n", "<br>")
            if bold:
                value_style = "color:#171717;font-weight:600;"
            else:
                value_style = "color:#4d4d4d;font-weight:400;"
            field_rows.append(
                f'<p style="{p_style}"><span style="color:#8f8f8f;font-weight:500;">{html.escape(label)}：</span>'
                f'<span style="{value_style}">{value_html}</span></p>'
            )
        # 最后一行去除 8px 下边距，使容器内收尾紧凑
        if field_rows:
            field_rows[-1] = field_rows[-1].replace("margin:0 0 8px;", "margin:0;", 1)
        fields_html = "".join(field_rows)

        body = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background-color:#fafafa;font-family:Geist,Arial,'PingFang SC','Microsoft YaHei',sans-serif;-webkit-font-smoothing:antialiased;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#fafafa;">
    <tr>
      <td align="center" style="padding:64px 16px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:480px;background-color:#ffffff;border:1px solid #ebebeb;border-radius:12px;overflow:hidden;">
          <tr>
            <td align="center" style="padding:32px 24px 20px;">
              <a href="{home_url}" style="display:inline-block;">
                <img src="{logo_url}" alt="无足鸟" style="display:block;border:0;outline:none;">
              </a>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 20px;">
              <p style="margin:0;font-size:14px;font-weight:400;line-height:20px;color:#4d4d4d;">您的打卡计划已触发通知，详情如下：</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 20px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f2f2f2;border-radius:12px;">
                <tr>
                  <td style="padding:16px 24px;">
                    {fields_html}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 24px;">
              <p style="margin:0;font-size:14px;font-weight:400;line-height:20px;color:#8f8f8f;">请尽快打开小程序完成打卡。</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 32px;border-top:1px solid #ebebeb;">
              <p style="margin:24px 0 0;font-size:12px;font-weight:400;line-height:16px;color:#a1a1a1;text-align:center;">
                此邮件由 <a href="{home_url}" style="color:#0070f3;text-decoration:none;">无足鸟</a> 自动发送
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

        msg = MIMEText(body, "html", "utf-8")
        # Subject 含计划名等用户输入：换行替换为空格，防邮件头注入（存量数据兜底）
        msg["Subject"] = _HEADER_NEWLINES.sub(" ", subject)
        # 发件人显示名：项目名称（原 SMTP_SENDER_NAME 配置已随验证码邮件迁 auth 服务）
        msg["From"] = formataddr((settings.PROJECT_NAME, from_email))
        msg["To"] = to_email

        try:
            if smtp_port == 465:
                # SSL 直连（如腾讯企业邮、QQ 邮箱）
                with _PinnedSMTPSSL(smtp_host, pinned_ip, smtp_port, timeout=10) as server:
                    self._smtp_authenticate(server, from_email, smtp_password)
                    _ = server.sendmail(from_email, [to_email], msg.as_string())
            else:
                # STARTTLS（如 Gmail 587、Outlook 587）；显式传入校验 context
                with _PinnedSMTP(smtp_host, pinned_ip, smtp_port, timeout=10) as server:
                    _ = server.starttls(context=_TLS_CONTEXT)
                    self._smtp_authenticate(server, from_email, smtp_password)
                    _ = server.sendmail(from_email, [to_email], msg.as_string())
            logger.info(f"打卡通知邮件发送成功：{_mask_email(from_email)} -> {_mask_email(to_email)}")
        except smtplib.SMTPAuthenticationError as e:
            if isinstance(e.smtp_error, bytes):
                err_detail = e.smtp_error.decode("utf-8", errors="replace")
            elif e.smtp_error:
                err_detail = str(e.smtp_error)
            else:
                err_detail = str(e)
            logger.error(
                f"打卡通知邮件发送失败：{_mask_email(from_email)} -> {_mask_email(to_email)}，"
                f"SMTP 认证失败（{e.smtp_code}）：{err_detail}"
            )
            raise RuntimeError(f"邮件发送失败：SMTP 认证失败（{e.smtp_code}）：{err_detail}")
        except Exception as e:
            logger.error(f"打卡通知邮件发送失败：{_mask_email(from_email)} -> {_mask_email(to_email)}，错误：{e}")
            raise RuntimeError(f"邮件发送失败：{e}")
