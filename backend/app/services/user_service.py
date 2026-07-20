import asyncio
import secrets
import time
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.security import Security
from ..models.user import User as UserModel
from ..models.user_miniapp_account import UserMiniappAccount
from ..models.notification_channel import NotificationChannel
from ..models.plan import CheckinPlan, PlanNotificationTime, PlanNotificationChannel
from ..models.checkin_record import CheckinRecord
from ..models.notification_log import NotificationLog
from ..schemas.notification_channel import CHANNEL_TYPE_ZNX
from ..utils.timezone import now_shanghai
from ..utils.logger import logger
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
        :raises RuntimeError: 邮件发送失败（由 API 层捕获并返回给用户）
        """
        # 生成 6 位数字验证码
        code = "".join(secrets.choice("0123456789") for _ in range(6))
        key = self._get_code_key(email, purpose)
        _verification_codes[key] = (code, time.time() + CODE_EXPIRE_SECONDS)
        # 同步发送验证邮件（在线程池中执行同步 SMTP 调用，避免阻塞事件循环）
        # 失败时 RuntimeError 向上传播，由 API 层返回 500，前端提示用户可重试
        await asyncio.to_thread(Email().send_verification_code, email, code)
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
        # 4. 哈希密码并入库（设置默认头像 hei 与默认签名）
        db_user = UserModel(
            username=username,
            email=email,
            password_hash=Security.hash_password(password),
            avatar_url="hei",
            signature="蜗角虚名，蝇头微利，算来著甚干忙。事皆前定，谁弱又谁强。",
            status=1,
        )
        self.db.add(db_user)
        await self.db.flush()
        # 5. 自动为新用户创建站内信通知渠道（channel_value=用户ID）
        await self._ensure_znx_channel(db_user.id)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def _ensure_znx_channel(self, user_id: int) -> NotificationChannel:
        """
        为用户创建站内信通知渠道（注册时自动调用）
        - channel_type='站内信'，channel_value=用户ID（字符串形式）
        - 若已存在则直接返回现有记录
        """
        result = await self.db.execute(
            select(NotificationChannel).where(
                NotificationChannel.user_id == user_id,
                NotificationChannel.channel_type == CHANNEL_TYPE_ZNX,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        channel = NotificationChannel(
            user_id=user_id,
            channel_type=CHANNEL_TYPE_ZNX,
            channel_value=str(user_id),
            enabled=True,
        )
        self.db.add(channel)
        await self.db.flush()
        return channel

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
        if not Security.verify_password(password, user.password_hash):
            raise ValueError("密码错误")
        # 5. 更新最后登录时间
        user.last_login_at = now_shanghai()
        await self.db.commit()
        await self.db.refresh(user)
        # 6. 返回用户对象（包含 username、signature、avatar_url）
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
        user.password_hash = Security.hash_password(new_password)
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
        if not Security.verify_password(old_password, user.password_hash):
            raise ValueError("旧密码错误")
        # 3. 更新新密码
        user.password_hash = Security.hash_password(new_password)
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

    async def send_change_email_new_code(self, new_email: str, allow_existing: bool = False) -> str:
        """
        发送修改/绑定邮箱的新邮箱验证码
        :param new_email: 新邮箱地址
        :param allow_existing: 是否允许邮箱已存在（绑定邮箱触发账号合并场景需允许）
        :return: 生成的 6 位验证码
        :raises ValueError: 新邮箱已被注册（仅 allow_existing=False 时校验）
        """
        # 修改邮箱场景：新邮箱不能已被注册；绑定邮箱场景：允许已存在（触发账号合并）
        if not allow_existing and await self.get_by_email(new_email):
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
        计划删除账号：将 status 置为 0，后台任务在 updated_at 24小时后自动清理
        :param user_id: 用户ID
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        user.status = 0
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def cancel_deletion(self, user_id: int) -> UserModel:
        """
        取消账号删除计划：将 status 恢复为 1
        :param user_id: 用户ID
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        user.status = 1
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def purge_expired_deletions(self) -> int:
        """
        清理已到期的删除计划账号：删除 status=0 且 updated_at 超过24小时的用户及其所有关联数据
        --------------------------------------------------------------------------
        关联数据清理顺序（均以 user_id 为过滤条件，避免误删他人数据）：
          1. plan_notification_times / plan_notification_channels：计划关联的时间点和渠道
          2. checkin_records：打卡记录
          3. notification_logs：通知发送记录
          4. notification_channels：通知渠道配置
          5. checkin_plans：打卡计划主表
          6. user_miniapp_accounts：小程序绑定记录（用户库）
          7. users：用户主记录（用户库）
        :return: 已删除的用户数量
        """
        now = now_shanghai()
        threshold = now - timedelta(hours=24)
        result = await self.db.execute(
            select(UserModel).where(
                UserModel.status == 0,
                UserModel.updated_at <= threshold,
            )
        )
        expired_users = result.scalars().all()
        count = 0
        for user in expired_users:
            user_id = user.id

            # 1. 查询该用户所有的计划 ID（用于删除计划关联表）
            plan_ids_result = await self.db.execute(
                select(CheckinPlan.id).where(CheckinPlan.user_id == user_id)
            )
            plan_ids = plan_ids_result.scalars().all()

            # 2. 删除计划关联的时间点和渠道关联（通过 plan_id 过滤）
            if plan_ids:
                await self.db.execute(
                    delete(PlanNotificationTime).where(
                        PlanNotificationTime.plan_id.in_(plan_ids)
                    )
                )
                await self.db.execute(
                    delete(PlanNotificationChannel).where(
                        PlanNotificationChannel.plan_id.in_(plan_ids)
                    )
                )

            # 3. 删除打卡记录（user_id 过滤）
            await self.db.execute(
                delete(CheckinRecord).where(CheckinRecord.user_id == user_id)
            )

            # 4. 删除通知发送记录（user_id 过滤）
            await self.db.execute(
                delete(NotificationLog).where(NotificationLog.user_id == user_id)
            )

            # 5. 删除通知渠道配置（user_id 过滤）
            await self.db.execute(
                delete(NotificationChannel).where(
                    NotificationChannel.user_id == user_id
                )
            )

            # 6. 删除打卡计划主表（user_id 过滤）
            await self.db.execute(
                delete(CheckinPlan).where(CheckinPlan.user_id == user_id)
            )

            # 7. 删除关联的小程序账号记录（user_id 过滤，位于用户库）
            miniapp_result = await self.db.execute(
                select(UserMiniappAccount).where(
                    UserMiniappAccount.user_id == user_id
                )
            )
            for account in miniapp_result.scalars().all():
                await self.db.delete(account)

            # 8. 删除用户主记录
            await self.db.delete(user)
            count += 1
        if count > 0:
            await self.db.commit()
        return count

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
            # 2b. 未绑定：创建新用户（设置默认用户名/头像/签名）
            user = UserModel(
                username=await self._generate_default_username(),
                email=None,
                password_hash=None,
                avatar_url="lan",
                signature="行有不得，反求诸己。",
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
            # 自动为新微信登录用户创建站内信通知渠道（channel_value=用户ID）
            await self._ensure_znx_channel(user.id)

        # 3. 更新最后登录时间
        user.last_login_at = now_shanghai()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def _generate_default_username(self) -> str:
        """
        生成默认用户名：无足鸟 + 自增数字（如 无足鸟1、无足鸟2）
        :return: 唯一的默认用户名
        """
        result = await self.db.execute(
            select(UserModel.username).where(UserModel.username.like("无足鸟%"))
        )
        existing_usernames = result.scalars().all()
        max_num = 0
        prefix = "无足鸟"
        for uname in existing_usernames:
            if uname and uname.startswith(prefix):
                suffix = uname[len(prefix) :]
                if suffix.isdigit():
                    max_num = max(max_num, int(suffix))
        return f"{prefix}{max_num + 1}"

    async def update_username(self, user_id: int, new_username: str) -> UserModel:
        """
        更新用户名（含唯一性校验）
        :param user_id: 用户ID
        :param new_username: 新用户名
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在、用户名已被占用
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        # 校验用户名唯一性（排除当前用户自身）
        existing = await self.get_by_username(new_username)
        if existing and existing.id != user_id:
            raise ValueError("用户名已被占用")
        user.username = new_username
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_password(self, user_id: int, new_password: str) -> UserModel:
        """
        设置密码（用于无密码用户，如微信登录用户首次设置密码）
        :param user_id: 用户ID
        :param new_password: 新密码
        :return: UserModel（更新后的用户对象）
        :raises ValueError: 用户不存在、用户已设置密码
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        if user.password_hash:
            raise ValueError("用户已设置密码，请使用修改密码功能")
        user.password_hash = Security.hash_password(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def bind_email(self, user_id: int, new_email: str, new_code: str) -> UserModel:
        """
        绑定邮箱（用于无邮箱用户，如微信登录用户首次绑定邮箱）
        - 若邮箱不存在：直接绑定到当前账号
        - 若邮箱已存在：触发账号合并，以已有邮箱账号为主账号，合并当前账号信息后删除当前账号
        :param user_id: 当前用户ID（无邮箱账号）
        :param new_email: 新邮箱地址
        :param new_code: 新邮箱验证码
        :return: UserModel（绑定/合并后的主账号对象）
        :raises ValueError: 用户不存在、用户已绑定邮箱、验证码错误
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        if user.email:
            raise ValueError("用户已绑定邮箱，请使用修改邮箱功能")
        # 验证新邮箱验证码（复用 change_new 用途）
        if not self.verify_code_for_purpose(new_email, new_code, "change_new"):
            raise ValueError("邮箱验证码错误或已过期")

        # 检查新邮箱是否已存在
        existing_user = await self.get_by_email(new_email)

        if not existing_user:
            # 情况1：邮箱不存在，直接绑定到当前账号
            user.email = new_email
            await self.db.commit()
            await self.db.refresh(user)
            return user

        # 情况2：邮箱已存在，触发账号合并
        # 主账号 = existing_user（已有邮箱），从账号 = user（当前无邮箱账号）
        main_user = existing_user
        sub_user = user

        # 先转移从账号的小程序绑定记录到主账号（此时 sub_user 尚未删除，可正常查询）
        miniapp_result = await self.db.execute(
            select(UserMiniappAccount).where(UserMiniappAccount.user_id == sub_user.id)
        )
        for account in miniapp_result.scalars().all():
            account.user_id = main_user.id

        # 先删除从账号并 flush，避免合并字段时唯一约束冲突
        # （SQLAlchemy flush 顺序为 INSERT→UPDATE→DELETE，若不先 flush 删除，
        #   合并字段的 UPDATE 会先于 DELETE 执行，此时从账号仍存在导致唯一约束冲突）
        await self.db.delete(sub_user)
        await self.db.flush()

        # 合并字段：主账号字段为空时用从账号填充，字段冲突时保留主账号
        if not main_user.username and sub_user.username:
            main_user.username = sub_user.username
        if not main_user.password_hash and sub_user.password_hash:
            main_user.password_hash = sub_user.password_hash
        if not main_user.signature and sub_user.signature:
            main_user.signature = sub_user.signature
        if not main_user.avatar_url and sub_user.avatar_url:
            main_user.avatar_url = sub_user.avatar_url
        # last_login_at 取较新值
        if sub_user.last_login_at and (
            not main_user.last_login_at or sub_user.last_login_at > main_user.last_login_at
        ):
            main_user.last_login_at = sub_user.last_login_at

        await self.db.commit()
        await self.db.refresh(main_user)
        return main_user
