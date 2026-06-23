import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_db_connection():
    # 先连接到服务器而不指定数据库
    SERVER_URL = "mysql+asyncmy://root:root@127.0.0.1:3306?charset=utf8mb4"
    DATABASE_URL = "mysql+asyncmy://root:root@127.0.0.1:3306/mydb?charset=utf8mb4"
    
    try:
        print("正在连接数据库服务器...")
        print(f"连接地址: 127.0.0.1:3306")
        print(f"用户名: root")
        
        # 连接到服务器
        server_engine = create_async_engine(SERVER_URL, echo=False)
        async with server_engine.connect() as conn:
            print("\n[OK] 数据库服务器连接成功！")
            
            # 获取MariaDB版本
            result = await conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"[OK] MariaDB 版本: {version}")
            
            # 列出所有数据库
            result = await conn.execute(text("SHOW DATABASES"))
            databases = [row[0] for row in result.fetchall()]
            print(f"[OK] 当前数据库列表: {', '.join(databases)}")
            
            # 检查mydb是否存在
            if 'mydb' not in databases:
                print("\n正在创建 'mydb' 数据库...")
                await conn.execute(text("CREATE DATABASE IF NOT EXISTS mydb DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                await conn.commit()
                print("[OK] 数据库 'mydb' 创建成功！")
            else:
                print("\n[OK] 数据库 'mydb' 已存在")
        
        await server_engine.dispose()
        
        # 连接到mydb数据库验证
        print("\n正在连接到 'mydb' 数据库...")
        db_engine = create_async_engine(DATABASE_URL, echo=False)
        async with db_engine.connect() as conn:
            print("[OK] 'mydb' 数据库连接成功！")
        
        await db_engine.dispose()
        print("\n测试完成！")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 数据库操作失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db_connection())
    exit(0 if success else 1)
