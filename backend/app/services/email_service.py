import base64
import html
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
        _ = server.login(user, password)

    def send_verification_code(self, to_email: str, code: str) -> None:
        """
        发送验证码邮件（注册、密码找回、修改邮箱等场景共用）
        :param to_email: 收件人邮箱
        :param code:     6 位数字验证码
        """
        if not self.user or not self.password:
            # 源邮箱未配置，给出明确提示
            raise ValueError(
                "SMTP 邮箱未配置，请在 .env 中设置 SMTP_USER 与 SMTP_PASSWORD（腾讯企业邮账号与客户端专用密码）"
            )

        subject = "【按时吃药】验证码"
        home_url = "https://www.wuzuniao.com"
        logo_url = "https://www.wuzuniao.com/images/logo_wuzuniao_com_s.png"
        content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>按时吃药 - 验证码</title>
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
              <p style="margin:0;font-size:14px;font-weight:400;line-height:20px;color:#4d4d4d;">请在页面中输入以下验证码完成验证：</p>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:4px 24px 24px;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="background-color:#f2f2f2;border-radius:12px;">
                <tr>
                  <td style="padding:16px 32px;">
                    <span style="font-family:'Geist Mono',ui-monospace,SFMono-Regular,Menlo,monospace;font-size:32px;font-weight:600;letter-spacing:8px;color:#171717;">{code}</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 24px;">
              <p style="margin:0 0 8px;font-size:14px;font-weight:400;line-height:20px;color:#4d4d4d;">验证码有效期为 <strong style="color:#171717;font-weight:600;">5 分钟</strong>，请勿泄露给他人。</p>
              <p style="margin:0;font-size:14px;font-weight:400;line-height:20px;color:#8f8f8f;">如非本人操作，请忽略本邮件。</p>
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

        msg = MIMEText(content, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr((self.sender_name, self.user))
        msg["To"] = to_email

        try:
            # 腾讯企业邮使用 SSL（端口 465）
            with smtplib.SMTP_SSL(self.host, self.port, timeout=10) as server:
                self._smtp_authenticate(server, self.user, self.password)
                _ = server.sendmail(self.user, [to_email], msg.as_string())
            logger.info(f"验证码邮件发送成功：{to_email}")
        except smtplib.SMTPAuthenticationError as e:
            if isinstance(e.smtp_error, bytes):
                err_detail = e.smtp_error.decode("utf-8", errors="replace")
            elif e.smtp_error:
                err_detail = str(e.smtp_error)
            else:
                err_detail = str(e)
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

        正文按"字段行"逐行渲染（参考验证码邮件样式，遵循 DESIGN-vercel.md 的 Geist 设计规范）：
        - 约定调用方传入的 content 每行为一个字段，格式"字段名：值"或"字段名: 值"；
          本方法按首个冒号（全角：或半角:）切分字段名/值，字段名用 mute 色 500 衬底，值用 ink 色 600 的 strong 突出（突出通知内容）。
        - 无冒号的行作为普通段落整行渲染。
        - 字段行统一置于 hairline-soft 高亮容器内，前后各附一句引导与提示语。
        :raises RuntimeError: SMTP 连接或发送失败
        """
        home_url = "https://www.wuzuniao.com"
        logo_url = "https://www.wuzuniao.com/images/logo_wuzuniao_com_s.png"

        # 将传入的纯文本 content 按行拆分，逐行渲染为"字段行"
        # 识别首个冒号（全角：或半角:）切分字段名/值；无冒号的行作为普通段落整行渲染
        p_style = "margin:0 0 8px;font-size:14px;font-weight:400;line-height:20px;color:#4d4d4d;"
        field_rows: list[str] = []
        for raw_line in content.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            label = ""
            value = ""
            sep_matched = ""
            for sep in ("：", ":"):
                idx = line.find(sep)
                if idx > 0:
                    label = line[:idx].strip()
                    value = line[idx + len(sep):].strip()
                    sep_matched = sep
                    break
            if sep_matched:
                field_rows.append(
                    f'<p style="{p_style}"><span style="color:#8f8f8f;font-weight:500;">{html.escape(label)}{sep_matched}</span><strong style="color:#171717;font-weight:600;">{html.escape(value)}</strong></p>'
                )
            else:
                field_rows.append(f'<p style="{p_style}">{html.escape(line)}</p>')
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
        msg["Subject"] = subject
        msg["From"] = formataddr((self.sender_name, from_email))
        msg["To"] = to_email

        try:
            if smtp_port == 465:
                # SSL 直连（如腾讯企业邮、QQ 邮箱）
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                    self._smtp_authenticate(server, from_email, smtp_password)
                    _ = server.sendmail(from_email, [to_email], msg.as_string())
            else:
                # STARTTLS（如 Gmail 587、Outlook 587）
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    _ = server.starttls()
                    self._smtp_authenticate(server, from_email, smtp_password)
                    _ = server.sendmail(from_email, [to_email], msg.as_string())
            logger.info(f"打卡通知邮件发送成功：{from_email} -> {to_email}")
        except smtplib.SMTPAuthenticationError as e:
            if isinstance(e.smtp_error, bytes):
                err_detail = e.smtp_error.decode("utf-8", errors="replace")
            elif e.smtp_error:
                err_detail = str(e.smtp_error)
            else:
                err_detail = str(e)
            logger.error(f"打卡通知邮件发送失败：{from_email} -> {to_email}，SMTP 认证失败（{e.smtp_code}）：{err_detail}")
            raise RuntimeError(f"邮件发送失败：SMTP 认证失败（{e.smtp_code}）：{err_detail}")
        except Exception as e:
            logger.error(f"打卡通知邮件发送失败：{from_email} -> {to_email}，错误：{e}")
            raise RuntimeError(f"邮件发送失败：{e}")
