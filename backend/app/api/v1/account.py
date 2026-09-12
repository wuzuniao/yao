"""
账号生命周期接口（业务项目侧主动执行，auth 不再回调）
--------------------------------------------------------------------------
- POST /account/merge  账号合并（bind-email 邮箱冲突触发 need_merge 后由前端调用）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.deps import get_current_user_id
from ...core.rate_limit import limit_authenticated
from ...services.account_service import request_account_merge

router = APIRouter()


@router.post("/merge", dependencies=[Depends(limit_authenticated)])
async def merge_account(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    账号合并接口（user_id 来自 JWT，作为从账号）
    - 前置条件：用户已在 auth 绑定邮箱时命中已有邮箱（bind-email 返回 need_merge）
    - 流程：从 auth 获取合并任务的真实主账号 → 迁移本服务业务数据 → confirm 上报
    - 返回 status=completed：合并完成，从账号令牌已被撤销，前端应清除本地登录态
      并引导使用主账号重新登录
    - 返回 status=processing：业务数据已迁移，confirm 上报失败待后台重试，
      前端同样应提示稍后重新登录
    """
    try:
        status = await request_account_merge(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    msg = (
        "账号合并完成，请使用主账号重新登录"
        if status == "completed"
        else "账号合并处理中，请稍后重新登录"
    )
    return {"code": 0, "msg": msg, "data": {"status": status}}
