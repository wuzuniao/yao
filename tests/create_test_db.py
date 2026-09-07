"""创建测试数据库的辅助脚本（业务测试库，与开发环境完全隔离；用户库已归 auth 服务）"""
import asyncio
import asyncmy


async def main():
    conn = await asyncmy.connect(
        host="127.0.0.1", port=3306, user="root", password="root"
    )
    cur = conn.cursor()
    # 业务测试库
    await cur.execute(
        "CREATE DATABASE IF NOT EXISTS wuzuniao_yao_test "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    await cur.close()
    conn.close()
    print("测试数据库创建成功：wuzuniao_yao_test")


asyncio.run(main())
