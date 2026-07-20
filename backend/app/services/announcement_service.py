from sqlalchemy import select, update, delete, func, text

from ..models.announcement import Announcement


class AnnouncementService:
    """
    公告业务逻辑服务
    --------------------------------------------------------------------------
    - 发布公告：写入 announcements 单行记录
    - 查询：按创建时间倒序返回全部公告
    - 更新/删除：按公告ID操作（仅管理员可调用，权限由路由依赖保证）
    """

    def __init__(self, db) -> None:
        self.db = db

    async def publish(self, title: str, content: str) -> Announcement:
        """发布一条公告，返回新建记录"""
        announcement = Announcement(title=title, content=content)
        self.db.add(announcement)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(announcement)
        return announcement

    async def list_all(self) -> list[Announcement]:
        """查询全部公告，按创建时间倒序（最新在前）"""
        result = await self.db.execute(
            select(Announcement).order_by(Announcement.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_recent(self, days: int = 7) -> list[Announcement]:
        """查询最近 days 天内发布的公告，按创建时间倒序（最新在前）

        - 采用数据库服务器时间 func.now()，避免应用层时区偏差
        - 仅返回 created_at >= now - days 的记录
        - MariaDB 日期运算使用 DATE_SUB(NOW(), INTERVAL N DAY)，
          避免 SQLAlchemy 将 timedelta 误当作绑定参数
        """
        since = func.date_sub(func.now(), text(f"INTERVAL {days} DAY"))
        result = await self.db.execute(
            select(Announcement)
            .where(Announcement.created_at >= since)
            .order_by(Announcement.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, announcement_id: int, title: str, content: str) -> Announcement:
        """更新指定公告，返回更新后的记录"""
        announcement = await self._get_by_id(announcement_id)
        if not announcement:
            raise ValueError("公告不存在")
        announcement.title = title
        announcement.content = content
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(announcement)
        return announcement

    async def delete(self, announcement_id: int) -> None:
        """删除指定公告"""
        announcement = await self._get_by_id(announcement_id)
        if not announcement:
            raise ValueError("公告不存在")
        await self.db.delete(announcement)
        await self.db.commit()

    async def _get_by_id(self, announcement_id: int) -> Announcement | None:
        """根据ID查询公告"""
        result = await self.db.execute(
            select(Announcement).where(Announcement.id == announcement_id)
        )
        return result.scalar_one_or_none()
