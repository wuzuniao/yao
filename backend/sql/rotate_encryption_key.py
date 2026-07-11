#!/usr/bin/env python3
"""
rotate_encryption_key.py - 邮箱专用密码加密密钥轮换脚本
--------------------------------------------------------------------------
功能：
  1. 从 backend/.env 读取当前 ENCRYPTION_SECRET_KEY（旧密钥）和 DATABASE_URL
  2. 生成新的 AES-256-GCM 密钥（base64 编码的 32 字节随机数）
  3. 用旧密钥解密数据库中所有邮件渠道的 password
  4. 用新密钥重新加密
  5. 在数据库事务中更新所有记录（全部成功提交，否则全部回滚）
  6. 事务提交成功后，原子替换 .env 中的 ENCRYPTION_SECRET_KEY
  7. 用新密钥解密验证更新后的密码
  8. 自动重启后端服务以加载新密钥
     - Docker 环境：提示从宿主机执行 docker restart
     - 开发环境：终止占用 8000 端口的旧进程并后台启动新 uvicorn 进程

用法：
  python3 backend/sql/rotate_encryption_key.py

前置条件：
  - 已安装项目 Python 依赖（asyncmy, cryptography, pydantic-settings）
  - backend/.env 中已配置 DATABASE_URL 和 ENCRYPTION_SECRET_KEY
  - 运行前请备份数据库和 .env 文件
  - 建议在低峰期执行（轮换期间邮件通知功能短暂不可用）
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qs

# 将 backend/ 目录加入 sys.path，以便导入项目配置模块
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    import asyncmy
except ImportError:
    print("错误：未安装 asyncmy，请在项目 Python 环境中运行此脚本", file=sys.stderr)
    sys.exit(1)

try:
    from app.core.config import settings
except Exception as e:
    print(f"错误：无法加载项目配置，请确认 backend/.env 存在且配置完整 - {e}", file=sys.stderr)
    sys.exit(1)

# .env 文件路径
_ENV_FILE = _BACKEND_DIR / ".env"


def parse_db_url(url: str) -> dict:
    """解析 DATABASE_URL，返回 asyncmy.connect() 所需参数"""
    # 去除 mysql+asyncmy:// 等前缀，统一为 mysql:// 供 urlparse 解析
    if "://" in url:
        _, rest = url.split("://", 1)
    else:
        rest = url
    parsed = urlparse(f"mysql://{rest}")
    charset = "utf8mb4"
    if parsed.query:
        qs = parse_qs(parsed.query)
        charset = qs.get("charset", ["utf8mb4"])[0]
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username) if parsed.username else "root",
        "password": unquote(parsed.password) if parsed.password else "",
        "db": parsed.path.lstrip("/"),
        "charset": charset,
    }


def decrypt_with_key(key_b64: str, token: str) -> str:
    """使用指定密钥解密 AES-256-GCM 密文，返回明文"""
    key = base64.b64decode(key_b64)
    aesgcm = AESGCM(key)
    raw = base64.b64decode(token)
    nonce = raw[:12]
    ciphertext = raw[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def encrypt_with_key(key_b64: str, plaintext: str) -> str:
    """使用指定密钥加密明文为 AES-256-GCM 密文，返回 base64 编码"""
    key = base64.b64decode(key_b64)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def update_env_key(new_key: str) -> None:
    """原子更新 .env 中的 ENCRYPTION_SECRET_KEY（临时文件 + os.replace）"""
    with open(_ENV_FILE, "r", encoding="utf-8", newline="") as f:
        content = f.read()
    new_content = re.sub(
        r"^ENCRYPTION_SECRET_KEY=.*$",
        f"ENCRYPTION_SECRET_KEY={new_key}",
        content,
        flags=re.MULTILINE,
    )
    tmp_path = str(_ENV_FILE) + ".tmp"
    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        f.write(new_content)
    os.replace(tmp_path, str(_ENV_FILE))


def restart_backend() -> None:
    """
    重启后端服务以加载新密钥。

    pydantic-settings 的 settings 实例在进程启动时读取 .env 并缓存，
    无法跨进程动态刷新；uvicorn --reload 仅监控 .py 文件变化，
    .env 变更不触发重启。因此轮换成功后必须重启后端进程。

    - Docker 环境（检测 /.dockerenv）：容器内无法重启自身容器，
      提示从宿主机执行 docker restart
    - 开发环境：杀掉占用 8000 端口的旧 uvicorn 进程树，
      后台启动新进程（非 reload 单进程模式）并轮询 /health 验证启动成功

    注意：run.py 使用 uvicorn --reload 模式（主进程 + 子进程），
    若用 reload 模式启动，taskkill 只杀主进程会导致子进程残留并继续占用端口，
    因此脚本启动时改用非 reload 单进程模式，杀进程时用 /T 终止整个进程树。
    """
    import subprocess
    import time
    import urllib.request

    port = 8000
    health_url = f"http://localhost:{port}/health"

    # 检测 Docker 环境
    if Path("/.dockerenv").exists():
        print("")
        print("【Docker 环境提示】当前运行在容器内，无法自动重启容器。")
        print("请在宿主机执行以下命令重启后端容器以加载新密钥：")
        print("  docker restart <backend_container_name>")
        print("（容器启动时会重新读取 .env，新密钥自动生效）")
        return

    print("")
    print("正在重启后端服务以加载新密钥...")

    # 杀掉占用端口的旧 uvicorn 进程树
    # uvicorn --reload 模式有主进程 + 子进程，必须用 /T 终止整个进程树
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=5,
            )
            killed_pids: set[int] = set()
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts and parts[-1].isdigit():
                        pid = int(parts[-1])
                        if pid not in killed_pids:
                            # /T 终止指定进程及其所有子进程
                            subprocess.run(
                                ["taskkill", "/T", "/F", "/PID", str(pid)],
                                capture_output=True, timeout=5,
                            )
                            killed_pids.add(pid)
                            print(f"  已终止旧进程树 PID={pid}")
        except Exception as e:
            print(f"  警告：终止旧进程失败 - {e}", file=sys.stderr)
    else:
        try:
            import signal
            result = subprocess.run(
                ["lsof", "-t", "-i", f":{port}"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines():
                pid = int(line.strip())
                # 杀掉整个进程组（uvicorn --reload 的子进程同属一个进程组）
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                print(f"  已终止旧进程树 PID={pid}")
        except Exception as e:
            print(f"  警告：终止旧进程失败 - {e}", file=sys.stderr)

    time.sleep(2)  # 等待端口释放

    # 后台启动新 uvicorn 进程（非 reload 单进程模式，避免子进程残留问题）
    log_dir = _BACKEND_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = open(log_dir / "uvicorn.log", "a", encoding="utf-8")

    creation_flags = 0
    if sys.platform == "win32":
        # Windows: 创建独立进程组，不继承父进程控制台
        creation_flags = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )

    subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app", "--host", "0.0.0.0", "--port", str(port),
        ],
        cwd=str(_BACKEND_DIR),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        creationflags=creation_flags,
        close_fds=True,
    )

    # 轮询健康检查，确认新进程启动成功（最多等待 20 秒）
    for _ in range(20):
        time.sleep(1)
        try:
            with urllib.request.urlopen(health_url, timeout=2) as resp:
                if resp.status == 200:
                    print("  后端服务已重启，新密钥已生效")
                    return
        except Exception:
            continue

    print("  警告：后端服务可能未在预期时间内启动完成，请检查日志：")
    print(f"    {log_dir / 'uvicorn.log'}", file=sys.stderr)


async def main() -> int:
    # 从项目配置读取旧密钥和数据库连接信息（均来自 backend/.env）
    old_key = settings.ENCRYPTION_SECRET_KEY
    db_url = settings.DATABASE_URL

    if not old_key:
        print("错误：.env 中未配置 ENCRYPTION_SECRET_KEY", file=sys.stderr)
        return 1
    if not db_url:
        print("错误：.env 中未配置 DATABASE_URL", file=sys.stderr)
        return 1

    # 生成新密钥
    new_key = base64.b64encode(os.urandom(32)).decode("ascii")

    print("==========================================")
    print("  邮箱专用密码加密密钥轮换")
    print("==========================================")
    print(f"旧密钥前缀: {old_key[:8]}...")
    print(f"新密钥前缀: {new_key[:8]}...")
    print(f".env 文件:  {_ENV_FILE}")
    print("==========================================")
    print("")

    db_params = parse_db_url(db_url)

    # 连接数据库，关闭自动提交以启用事务模式
    conn = await asyncmy.connect(**db_params, autocommit=False)

    try:
        # asyncmy 的 cursor() 和 fetchall() 为同步方法，无需 await
        cur = conn.cursor()

        # 设置会话时区为上海时间（与项目 database.py 配置一致）
        await cur.execute("SET time_zone = '+08:00'")

        # 1. 查询所有邮件通知渠道
        await cur.execute(
            "SELECT id, channel_value FROM notification_channels "
            "WHERE channel_type = '邮件'"
        )
        rows = await cur.fetchall()
        print(f"找到 {len(rows)} 个邮件通知渠道")

        if not rows:
            print("无邮件渠道需要轮换，跳过数据库更新")
            await cur.close()
            await conn.commit()
            # 即使没有邮件渠道，也更新 .env 中的密钥
            update_env_key(new_key)
            print(".env 文件已更新")
            restart_backend()
            return 0

        # 2. 逐条解密 + 重新加密（在内存中完成，无副作用）
        #    任何一条解密失败都会立即中止，不会触碰数据库
        updates: list[tuple[str, int]] = []
        for row in rows:
            channel_id: int = row[0]
            channel_value: str = row[1]

            # 解析 channel_value JSON
            try:
                cfg = json.loads(channel_value)
            except (json.JSONDecodeError, TypeError) as e:
                print(
                    f"错误：渠道 {channel_id} 的 channel_value JSON 解析失败: {e}",
                    file=sys.stderr,
                )
                return 1

            old_encrypted = cfg.get("password", "")
            if not old_encrypted:
                print(f"  跳过渠道 {channel_id}：password 为空")
                continue

            # 用旧密钥解密
            try:
                plaintext = decrypt_with_key(old_key, old_encrypted)
            except Exception as e:
                print(
                    f"错误：渠道 {channel_id} 的 password 解密失败"
                    f"（密钥可能不匹配或数据损坏）: {e}",
                    file=sys.stderr,
                )
                return 1

            # 用新密钥重新加密
            new_encrypted = encrypt_with_key(new_key, plaintext)
            cfg["password"] = new_encrypted
            new_value = json.dumps(cfg, ensure_ascii=False)
            updates.append((new_value, channel_id))
            print(f"  渠道 {channel_id}：已重新加密")

        if not updates:
            print("没有需要更新的渠道（所有 password 均为空）")
            await cur.close()
            await conn.commit()
            update_env_key(new_key)
            print(".env 文件已更新")
            restart_backend()
            return 0

        # 3. 事务更新数据库（全部成功才提交，否则回滚）
        print(f"开始事务更新 {len(updates)} 条记录...")
        for new_value, channel_id in updates:
            await cur.execute(
                "UPDATE notification_channels "
                "SET channel_value = %s, updated_at = NOW() "
                "WHERE id = %s",
                (new_value, channel_id),
            )

        # 4. 提交事务
        await conn.commit()
        print(f"事务已提交，成功更新 {len(updates)} 条记录")
        await cur.close()

        # 5. 更新 .env 文件（事务提交成功后执行）
        try:
            update_env_key(new_key)
            print(".env 文件已更新")
        except Exception as e:
            print(
                f"严重错误：数据库已更新，但 .env 文件写入失败！"
                f"请手动将以下密钥写入 {_ENV_FILE}：",
                file=sys.stderr,
            )
            print(f"ENCRYPTION_SECRET_KEY={new_key}", file=sys.stderr)
            print(f"错误详情: {e}", file=sys.stderr)
            return 1

        # 6. 用新密钥解密更新后的密码，验证轮换结果正确
        for new_value, channel_id in updates:
            cfg_verify = json.loads(new_value)
            try:
                decrypted = decrypt_with_key(new_key, cfg_verify.get("password", ""))
                print(
                    f"  渠道 {channel_id}：新密钥解密验证通过"
                    f"（明文长度 {len(decrypted)}）"
                )
            except Exception as e:
                print(
                    f"错误：渠道 {channel_id} 新密钥解密验证失败: {e}",
                    file=sys.stderr,
                )
                return 1

        print("")
        print("==========================================")
        print("  轮换成功完成")
        print("==========================================")
        print(f"新密钥: {new_key}")
        print(f".env 文件已更新: {_ENV_FILE}")
        print("==========================================")

        # 7. 自动重启后端服务以加载新密钥
        #    pydantic-settings 无法跨进程动态刷新，必须重启后端进程
        restart_backend()
        return 0

    except Exception as e:
        # 任何异常都回滚，数据库不受影响
        try:
            await conn.rollback()
        except Exception:
            pass
        print(f"错误：轮换失败，数据库已回滚 - {e}", file=sys.stderr)
        return 1
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n错误：用户中断，数据库已回滚", file=sys.stderr)
        sys.exit(1)
