"""账号合并同步任务 ORM 模型（对应 wuzuniao_yao.merge_sync_tasks）"""
from sqlalchemy import Column, BigInteger, SmallInteger, DateTime
from sqlalchemy.sql import func

from ..core.database import Base

# status 取值
MERGE_SYNC_PENDING = 0  # 业务数据已迁移，待 auth 确认合并
MERGE_SYNC_DONE = 1     # auth 已完成用户库合并


class MergeSyncTask(Base):
    """账号合并同步任务（业务数据迁移完成状态的本地记录）

    生命周期：auth bind-email 邮箱冲突创建合并任务 → 前端调 POST /api/v1/account/merge
    → 本服务迁移业务数据并落 pending 记录（与迁移同事务）→ confirm 上报 auth
    → 成功置 done；confirm 失败由后台循环重试上报直至 done。
    """

    __tablename__ = "merge_sync_tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    # 从账号（发起绑定邮箱、被合并删除的账号；唯一：同时至多一条待同步记录）
    from_user_id = Column(BigInteger, nullable=False, unique=True, comment="从账号 users.id（被合并删除）")
    to_user_id = Column(BigInteger, nullable=False, comment="主账号 users.id（合并后保留，来自 auth 合并任务下发）")
    status = Column(SmallInteger, nullable=False, default=MERGE_SYNC_PENDING,
                    comment="状态：0-已迁移待确认，1-auth 已合并完成")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
