import secrets
import time
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.security import get_password_hash, verify_password
from ..models.user import User as UserModel
from ..models.user_miniapp_account import UserMiniappAccount
from .email_service import Email


# 邮箱验证码暂存：email:purpose -> (code, expire_timestamp)
# 说明：当前为进程内存储（开发阶段单进程足够），生产环境建议迁移至 Redis
# purpose 用于区分验证码用途：register（注册）、reset（找回密码）、change_old（修改邮箱-旧邮箱验证）、change_new（修改邮箱-新邮箱验证）
_verification_codes: dict[str, tuple[str, float]] = {}
# 验证码有效期 5 分钟
CODE_EXPIRE_SECONDS: int = 300


class User:
    """
    用户业务逻辑类（处理注册、登录、密码找回、资料修改等核心业务）
    --------------------------------------------------------------------------
    - 注册流程：校验验证码 -> 校验用户名/邮箱唯一性 -> 哈希密码 -> 入库
    - 登录流程：用户名/邮箱查找 -> 密码校验 -> 返回用户信息
    - 密码找回：发送验证码 -> 验证验证码 -> 更新密码
    - 资料修改：签名、密码、邮箱（需验证旧密码/旧邮箱）
    - 验证码：生成 6 位数字验证码，支持按用途区分（register/reset/change_old/change_new）
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_username(self, username: str) -> UserModel | None:
        result = await self.db.execute(
            select(UserModel).where(UserModel.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        result = await self.db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> UserModel | None:
        result = await self.db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()

    def _get_code_key(self, email: str, purpose: str) -> str:
        """生成验证码存储的键（email:purpose）"""
        return f"{email}:{purpose}"

    async def send_code_for_purpose(self, email: str, purpose: str) -> str:
        """
        生成并发送验证码（按用途区分）
        :param email: 收件人邮箱
        :param purpose: 验证码用途（register/reset/change_old/change_new）
        :return: 生成的 6 位验证码
        """
        # 生成 6 位数字验证码
        code = "".join(secrets.choice("0123456789") for _ in range(6))
        key = self._get_code_key(email, purpose)
        _verification_codes[key] = (code, time.time() + CODE_EXPIRE_SECONDS)
        # 调用邮箱类发送验证邮件
        Email().send_verification_code(email, code)
        return code

    def verify_code_for_purpose(self, email: str, code: str, purpose: str) -> bool:
        """
        校验验证码是否匹配（按用途区分）
        :param email: 收件人邮箱
        :param code: 用户输入的验证码
        :param purpose: 验证码用途
        :return: True 验证通过，False 验证失败
        """
        key = self._get_code_key(email, purpose)
        record = _verification_codes.get(key)
        if not record:
            return False
        stored_code, expire_at = record
        # 过期判定
        if time.time() > expire_at:
            _verification_codes.pop(key, None)
            return False
        if stored_code != code:
            return False
        # 验证通过，立即销毁验证码（一次性使用）
        _verification_codes.pop(key, None)
        return True

    async def send_code(self, email: str) -> str:
        """
        生成并发送注册验证码（兼容旧接口，调用 send_code_for_purpose）
        :param email: 收件人邮箱
        :return: 生成的 6 位验证码
        """
        # 注册场景：仅允许未注册邮箱
        if await self.get_by_email(email):
            raise ValueError("该邮箱已被注册")
        return await self.send_code_for_purpose(email, "register")

    def verify_code(self, email: str, code: str) -> bool:
        """
        校验注册验证码是否匹配（兼容旧接口，调用 verify_code_for_purpose）
        """
        return self.verify_code_for_purpose(email, code, "register")

    async def register(self, username: str, password: str, email: str, code: str) -> UserModel:
        """
        用户注册：验证码二次校验通过后才允许入库
        """
        # 1. 后端再次校验验证码
        if not self.verify_code(email, code):
            raise ValueError("验证码错误或已过期")
        # 2. 校验用户名唯一性
        if await self.get_by_username(username):
            raise ValueError("用户名已被注册")
        # 3. 校验邮箱唯一性
        if await self.get_by_email(email):
            raise ValueError("邮箱已被注册")
        # 4. 哈希密码并入库
        db_user = UserModel(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            avatar_url="",
            status=1,
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def login(self, username: str, password: str) -> UserModel:
        """
        用户登录：验证用户名/邮箱 + 密码
        :param username: 用户名或邮箱
        :param password: 明文密码
        :return: UserModel（验证成功）
        :raises ValueError: 用户不存在或密码错误
        """
        # 1. 尝试按用户名查找
        user = await self.get_by_username(username)
        # 2. 如果未找到，尝试按邮箱查找
        if not user:
            user = await self.get_by_email(username)
        # 3. 用户不存在
        if not user:
            raise ValueError("用户不存在")
        # 4. 校验密码
        if not verify_password(password, user.password_hash):
            raise ValueError("密码错误")
        # 5. 返回用户对象（包含 username、signature、avatar_url）
        return user

    async def send_reset_code(self, email: str) -> str:
        """
        发送密码找回验证码
        :param email: 收件人邮箱
        :return: 生成的 6 位验证码
        :raises ValueError: 邮箱未注册
        """
        # 仅允许已注册邮箱
        if not await self.get_by_email(email):
            raise ValueError("该邮箱未注册")
        return await self.send_code_for_purpose(email, "reset")

    async def reset_password(self, email: str, code: str, new_password: str) -> UserModel:
        """
        重置密码：验证验证码后更新密码
        :param email: 用户邮箱
        :param code: 验证码
        :param new_password: 新密码
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 验证码错误或已过期、邮箱未注册
        """
        # 1. 校验验证码
        if not self.verify_code_for_purpose(email, code, "reset"):
            raise ValueError("验证码错误或已过期")
        # 2. 查找用户
        user = await self.get_by_email(email)
        if not user:
            raise ValueError("用户不存在")
        # 3. 更新密码
        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_signature(self, user_id: int, signature: str) -> UserModel:
        """
        更新用户签名
        :param user_id: 用户ID
        :param signature: 新签名
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        user.signature = signature
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> UserModel:
        """
        修改密码：验证旧密码后更新新密码
        :param user_id: 用户ID
        :param old_password: 旧密码
        :param new_password: 新密码
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在、旧密码错误
        """
        # 1. 查找用户
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        # 2. 验证旧密码
        if not verify_password(old_password, user.password_hash):
            raise ValueError("旧密码错误")
        # 3. 更新新密码
        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def send_change_email_old_code(self, user_id: int) -> str:
        """
        发送修改邮箱的旧邮箱验证码
        :param user_id: 用户ID
        :return: 生成的 6 位验证码
        :raises ValueError: 用户不存在
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        return await self.send_code_for_purpose(user.email, "change_old")

    async def send_change_email_new_code(self, new_email: str) -> str:
        """
        发送修改邮箱的新邮箱验证码
        :param new_email: 新邮箱地址
        :return: 生成的 6 位验证码
        :raises ValueError: 新邮箱已被注册
        """
        # 新邮箱不能已被注册
        if await self.get_by_email(new_email):
            raise ValueError("该邮箱已被注册")
        return await self.send_code_for_purpose(new_email, "change_new")

    async def change_email(self, user_id: int, old_code: str, new_email: str, new_code: str) -> UserModel:
        """
        修改邮箱：验证旧邮箱验证码和新邮箱验证码后更新邮箱
        :param user_id: 用户ID
        :param old_code: 旧邮箱验证码
        :param new_email: 新邮箱地址
        :param new_code: 新邮箱验证码
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在、旧邮箱验证码错误、新邮箱验证码错误、新邮箱已被注册
        """
        # 1. 查找用户
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        # 2. 验证旧邮箱验证码
        if not self.verify_code_for_purpose(user.email, old_code, "change_old"):
            raise ValueError("旧邮箱验证码错误或已过期")
        # 3. 验证新邮箱验证码
        if not self.verify_code_for_purpose(new_email, new_code, "change_new"):
            raise ValueError("新邮箱验证码错误或已过期")
        # 4. 再次检查新邮箱唯一性（防止竞态条件）
        if await self.get_by_email(new_email):
            raise ValueError("该邮箱已被注册")
        # 5. 更新邮箱
        user.email = new_email
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_avatar(self, user_id: int, avatar_url: str) -> UserModel:
        """
        更新用户头像
        :param user_id: 用户ID
        :param avatar_url: 头像地址
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        user.avatar_url = avatar_url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def schedule_deletion(self, user_id: int) -> UserModel:
        """
        计划注销账号：设置24小时后自动删除
        :param user_id: 用户ID
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        user.deletion_scheduled_at = datetime.now() + timedelta(hours=24)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def cancel_deletion(self, user_id: int) -> UserModel:
        """
        取消账号注销计划
        :param user_id: 用户ID
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        user.deletion_scheduled_at = None
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def _code2session(self, code: str) -> dict:
        """
        调用微信 jscode2session 接口，用 code 换取 openid 和 session_key
        :param code: 前端 wx.login() 获取的临时登录凭证
        :return: {"openid": str, "session_key": str, ...}
        :raises ValueError: 微信接口调用失败
        """
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.WX_APPID,
            "secret": settings.WX_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=10)
            data = resp.json()
        if data.get("errcode", 0) != 0:
            raise ValueError(f"微信登录失败：{data.get('errmsg', '未知错误')}")
        return data

    async def wechat_login(self, code: str) -> UserModel:
        """
        微信一键登录：code → openid → 查找/创建用户 → 返回用户信息
        :param code: 前端 wx.login() 获取的临时登录凭证
        :return: UserModel
        :raises ValueError: 微信接口调用失败
        """
        # 1. 调用微信接口获取 openid 和 session_key
        wx_data = await self._code2session(code)
        openid = wx_data["openid"]
        session_key = wx_data["session_key"]
        app_id = settings.WX_APPID

        # 2. 查询 user_miniapp_accounts 是否已有该 openid 的绑定记录
        result = await self.db.execute(
            select(UserMiniappAccount).where(
                UserMiniappAccount.app_id == app_id,
                UserMiniappAccount.openid == openid,
            )
        )
        miniapp_account = result.scalar_one_or_none()

        if miniapp_account:
            # 2a. 已绑定：更新 session_key，获取关联用户
            miniapp_account.session_key = session_key
            user = await self.get_by_id(miniapp_account.user_id)
            if not user:
                raise ValueError("用户数据异常，请联系管理员")
        else:
            # 2b. 未绑定：创建新用户（微信登录用户 username/email/password 均为空）
            user = UserModel(
                username=None,
                email=None,
                password_hash=None,
                avatar_url="",
                status=1,
            )
            self.db.add(user)
            await self.db.flush()
            miniapp_account = UserMiniappAccount(
                user_id=user.id,
                app_id=app_id,
                openid=openid,
                session_key=session_key,
            )
            self.db.add(miniapp_account)

        # 3. 更新最后登录时间
        user.last_login_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(user)
        return user
