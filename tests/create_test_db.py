"""创建测试数据库的辅助脚本"""
import asyncio
import asyncmy


async def main():
    conn = await asyncmy.connect(
        host="127.0.0.1", port=3306, user="root", password="root"
    )
    cur = conn.cursor()
    await cur.execute(
        "CREATE DATABASE IF NOT EXISTS wuzuniao_yao_test "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    await cur.close()
    conn.close()
    print("测试数据库 wuzuniao_yao_test 创建成功")


asyncio.run(main())
