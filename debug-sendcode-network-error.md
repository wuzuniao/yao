# Debug Session: sendcode-network-error
- **Status**: [FIXED]
- **Issue**: 注册页点击"获取验证码"触发"网络请求失败:fail"（已勾选"不校验合法域名"）
- **Secondary Issue**: 验证码正确但提交注册失败（passlib/bcrypt 不兼容）
- **Debug Server**: 未启动（静态证据已足够定位根因）
- **Log File**: N/A（通过 netstat/curl/uvicorn 日志直接定位）

## Reproduction Steps
1. 打开注册页 register.vue
2. 填写邮箱（如 bbs.wuzuniao@qq.com）
3. 点击"获取验证码"按钮 → 邮箱收到验证码 ✓
4. 填写验证码并点击"注册" → 提示"验证码错误或已过期"

## Hypotheses & Verification
| ID | Hypothesis | Likelihood | Effort | Evidence |
|----|------------|------------|--------|----------|
| A | 后端 FastAPI 服务未启动，连接被拒绝 | High | Low | **Confirmed (Phase 1)** - netstat :8000 无输出 |
| B | 后端已启动但 send-code 因 SMTP 未配置抛 500 | Med | Low | **Rejected** - SMTP 已配置，邮件发送成功 |
| C | 请求 URL 路径拼接错误 | Low | Low | **Rejected** - curl 测试路径正确 |
| D | 微信小程序无法访问 localhost | Med | Med | **Rejected** - 0.0.0.0:8000 绑定 |
| E | 前端运行旧构建产物 | Med | Low | **Rejected** - 根因为后端未运行 |
| F | passlib 1.7.4 与 bcrypt 5.0.0 不兼容导致密码哈希失败 | High | Low | **Confirmed (Phase 2)** - 插桩日志显示 verify_code 通过但 bcrypt 抛 ValueError |

## Root Cause Analysis

### Phase 1: 网络请求失败
**根因链**：
1. 后端 Python 依赖未安装（pydantic_settings / passlib / email-validator 等缺失）
2. → `python-jose` 在 Python 3.14 上无可用版本，导致 `pip install -r requirements.txt` 整体失败
3. → 后端 FastAPI 服务无法启动
4. → 8000 端口无监听进程
5. → 前端 uni.request 连接被拒绝
6. → fail 回调触发 → "网络请求失败:fail"

### Phase 2: 验证码正确但注册失败
**根因链**：
1. `passlib 1.7.4` 内部访问 `bcrypt.__about__.__version__`，但 `bcrypt 5.0.0` 已移除 `__about__` 模块
2. → passlib 的 `detect_wrap_bug` 调用 `bcrypt.hashpw` 时抛出 `ValueError: password cannot be longer than 72 bytes`
3. → `get_password_hash()` 抛出异常 → `register()` 抛出 ValueError → HTTP 400
4. → 验证码在 `verify_code` 通过后被消费（一次性使用）
5. → 用户第二次/第三次提交时，验证码记录已不存在 → "验证码错误或已过期"

**关键插桩证据**（来自后端日志）：
```
# 第一次提交（验证码正确）
[DEBUG] verify_code 输入: email='bbs.wuzuniao@qq.com', code='715239', 已存储keys=['bbs.wuzuniao@qq.com']
[DEBUG] verify_code 验证通过: email='bbs.wuzuniao@qq.com'
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes
HTTP 400 Bad Request

# 第二次提交（验证码已被消费）
[DEBUG] verify_code 输入: email='bbs.wuzuniao@qq.com', code='715239', 已存储keys=[]
[DEBUG] verify_code 记录不存在: email='bbs.wuzuniao@qq.com'
HTTP 400 Bad Request
```

## Fix Applied

### Phase 1: 网络请求失败修复
1. **安装缺失依赖**：pip install pydantic-settings passlib[bcrypt] python-multipart email-validator（清华镜像源）
2. **替换 python-jose 为 pyjwt**：requirements.txt 中 `python-jose[cryptography]>=3.3.0` → `pyjwt>=2.8.0`
3. **启动后端服务**：uvicorn app.main:app --host 0.0.0.0 --port 8000

### Phase 2: 密码哈希失败修复
1. **移除 passlib，直接使用 bcrypt 原生 API**：
   - `security.py` 中 `passlib.CryptContext` → `bcrypt.gensalt()` + `bcrypt.hashpw()` + `bcrypt.checkpw()`
   - 原因：passlib 1.7.4 自 2020 年停止维护，与 bcrypt 5.0.0 不兼容；bcrypt 5.0.0 原生 API 更简洁
2. **更新 requirements.txt**：`passlib[bcrypt]>=1.7.4` → `bcrypt>=4.0.0`

## Verification Conclusion
### Pre-fix（修复前）
- Phase 1: `netstat :8000` 无输出 → 前端 "网络请求失败:fail"
- Phase 2: `verify_code` 通过但 `get_password_hash` 抛 ValueError → 400 → 验证码被消费 → 后续提交"验证码错误"

### Post-fix（修复后）
- Phase 1: `netstat :8000` LISTENING → send-code 200 `{"code":0,"msg":"验证码已发送"}`
- Phase 2: 端到端服务层测试通过：
  - `[1] 验证码已生成: 184489`
  - `verify_code 验证通过`
  - `INSERT INTO users` → `[2] 注册成功: id=1, username=e2e_user`
  - `[3] 密码校验: True`
- 网络错误已消除，密码哈希正常工作，完整注册流程通过

## Instrumentation
- ~~`user_service.py` verify_code 方法添加 4 处 debug-point F 日志~~ **已移除**（用户验证通过后清理）
