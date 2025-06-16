# YuanShen API框架

YuanShen 是一个基于 FastAPI 的高性能 API 框架，支持多种数据服务模块的灵活接入与统一管理。框架内置了 API 管理后台、Token安全管理、访问统计、动态路由控制、日志系统等功能，适合二次开发和多业务场景扩展。

---

## 🌟 框架亮点

- **模块化设计**：支持多业务模块（如 maimai、admin、looking）灵活接入
- **API 访问统计与热门排行**：自动统计各 API 调用次数，后台可视化展示
- **动态路由管理**：支持在线启用/禁用 API，无需重启服务
- **Token 安全管理**：为每个 API 配置独立的 Token 验证，支持自定义Token和使用统计
- **强大的管理后台**：可视化操作、权限控制、实时监控、流畅的用户交互
- **安全与访问控制**：内置路由保护中间件，静态资源与管理端独立隔离
- **高效日志系统**：日志按日期自动轮转，便于追踪与审计
- **系统资源监控**：实时监控服务器CPU、内存占用及运行环境
- **响应式设计**：管理界面支持桌面和移动端访问，自适应各种屏幕尺寸

---

## 🆕 更新内容

### 2025年6月更新

- **Token 安全管理系统**：
  - 为每个 API 配置独立的 Token 验证
  - 支持默认 Token 和自定义 Token 两种模式
  - Token 过期时间灵活配置，默认1小时
  - 完整的 Token 使用统计和成功率分析
  - 可视化的 Token 配置界面，支持一键生成随机Token

- **管理界面优化**：
  - 全新的模态框设计，支持流畅的渐入渐出动画
  - 响应式布局，适配桌面端和移动端
  - 优化的交互体验，实时状态反馈
  - 改进的搜索和过滤功能

- **API 接口整合**：
  - 将 Token 相关的 GET 路由整合为统一的 POST 接口
  - 避免路径参数问题，提高接口稳定性
  - 统一的响应格式和错误处理

### 2025年5月更新

- **改进数据库操作**：重构 GlobalVars 全局变量存储系统，引入表管理机制
- **API 统计优化**：API 调用统计存储在专用表中，提高高并发访问性能
- **每日趋势分析**：增加 API 调用的日统计数据，支持历史趋势展示
- **系统监控面板**：管理后台增加系统信息展示，包括CPU、内存使用率等
- **Docker容器支持**：自动检测并适配容器环境，显示运行环境信息

---

## 🧩 框架模块说明

### 1. `maimai` 模块

- 提供舞萌DX玩家成绩相关的多种 B50 生成接口
- 支持标准、Bypass、理论值、累计分数、高分、AP、FC 等多种视图
- 支持曲目信息查询、图片生成、定数表查询等功能
- 包含超过15个图片生成API
- 支持 Token 验证，保护API安全访问
- 基于 [nonebot-plugin-maimaidx](https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx) 项目改造开发
- 静态资源文件请从原项目中获取，并放在main.py同级目录下

👉 [查看完整maimai API文档](./docs/MAIMAI_API_README.md)

### 2. `admin` 管理模块

- 提供 `/admin/manage` 管理后台页面，可视化管理所有API
- 支持 API 路由启用/禁用、Token 配置、访问统计、热门排行等功能
- **Token 安全管理**：为每个 API 配置独立的 Token 验证
  - 默认 Token 和自定义 Token 两种模式
  - 灵活的过期时间配置
  - 详细的使用统计和成功率分析
  - 一键生成随机 Token
- 可视化展示 API 总数、总访问量、访问量前三的 API
- 支持一键操作 API 状态，安全高效
- 系统资源监控，包括CPU使用率、内存占用、运行环境等
- 响应式设计，支持桌面和移动端访问

👉 [查看完整admin模块文档](./docs/ADMIN_API_README.md)

### 3. `looking` 模块

- 提供 looking.moe 站相关接口
- 设备管理和保活监控功能
- 支持设备状态查询、事件记录、存活管理等
- 完整的设备生命周期管理

👉 [查看完整looking模块文档](./docs/LOOKING_API_README.md)

---

## ⚙️ 安装与配置

### 前提条件

- Python 3.8+

### 安装步骤

1. 克隆代码库

    ```bash
    git clone https://github.com/huanxin996/YuanShen.git
    cd YuanShen
    ```

2. 安装依赖

    ```bash
    pip install -r requirements.txt
    ```

3. 配置

    编辑 `config.py` 文件，设置必要参数：

    ```python
    maimaitoken = "你的水鱼token"      # 水鱼Token
    admin_token = "你的管理员token"    # 管理员访问Token（可选，用于额外验证）
    log_level = "info"                # 日志级别，可选值：debug, info, warning, error
    ```

4. 运行服务

    ```bash
    python main.py
    ```

---

## 🚀 API 快速参考

### 模块概览

| 模块      | 主要功能                     | 典型接口                  | Token验证 | 详细文档 |
|-----------|------------------------------|---------------------------|-----------|---------|
| `maimai`  | 舞萌DX成绩图片生成           | `/maimai/b50`, `/maimai/minfo` | 支持 | [查看文档](./docs/MAIMAI_API_README.md) |
| `admin`   | 系统管理与监控               | `/admin/manage`, `/admin/stats` | 免验证 | [查看文档](./docs/ADMIN_API_README.md) |
| `looking` | 设备管理和保活监控           | `/looking/device-status`, `/looking/keep-alive` | 支持 | [查看文档](./docs/LOOKING_API_README.md) |

### Token 验证机制

- **默认模式**：所有 API 共享系统默认 Token
- **自定义模式**：为特定 API 设置独立的 Token
- **验证方式**：通过 `token` 查询参数或请求头传递
- **过期控制**：灵活设置 Token 有效期，默认1小时
- **使用统计**：详细记录每次验证的成功/失败情况

### 主要返回格式

**成功响应：**

```json
{
  "returnCode": 1,      // 1表示成功
  "base64": "...",      // 图片base64字符串（如有）
  "data": {...}         // 返回数据（如有）
}
```

**错误响应：**

```json
{
  "returnCode": 100,    // 100表示参数错误，101表示内部错误，401表示Token验证失败
  "msg": "错误信息",     // 具体错误描述
  "data": {             // 错误详情（可选）
    "error_type": "token_verification_failed",
    "api_path": "/maimai/b50"
  }
}
```

**Token 验证失败响应：**

```json
{
  "returnCode": 401,
  "msg": "Token验证失败: Token无效或已过期",
  "data": {
    "error_type": "token_verification_failed",
    "api_path": "/maimai/b50",
    "debug_info": {...}  // 调试信息（仅DEBUG模式）
  }
}
```

---

## 🔐 Token 管理指南

### 配置 Token 验证

1. **访问管理后台**：打开 `/admin/manage` 页面
2. **选择 API**：找到需要配置的 API，点击"Token设置"按钮
3. **配置验证**：
   - **启用默认 Token**：使用系统全局 Token
   - **设置自定义 Token**：为该 API 设置专用 Token
   - **生成随机 Token**：一键生成32位随机 Token
   - **配置过期时间**：设置 Token 有效期（毫秒）

### 使用 Token 访问 API

**方式一：查询参数**
```bash
curl "https://your-api.com/maimai/b50?username=test&token=your_token_here"
```

**方式二：请求头**
```bash
curl -H "Authorization: Bearer your_token_here" \
     "https://your-api.com/maimai/b50?username=test"
```

**方式三：自定义请求头**
```bash
curl -H "token: your_token_here" \
     "https://your-api.com/maimai/b50?username=test"
```

### Token 安全最佳实践

1. **定期更换**：建议定期更换 Token，特别是自定义 Token
2. **权限分离**：不同业务模块使用不同的自定义 Token
3. **合理过期时间**：根据使用频率设置合适的过期时间
4. **监控使用情况**：定期查看 Token 使用统计，发现异常及时处理
5. **安全存储**：避免在代码、日志中明文存储 Token

---

## 📝 日志系统

- 日志存储在项目根目录下的 `log` 文件夹
- 日志文件按日期命名（YYYY-MM-DD.log）
- 日志级别可在 `config.py` 中配置
- Token 验证日志包含详细的验证过程和结果

---

## 🔒 路由与安全

- 所有 API 路由均通过 `RouteProtectionMiddleware` 进行保护
- 管理界面（`/admin/`）自动放行，无需 Token 验证
- 静态资源有专门的访问控制
- 支持动态启用/禁用 API 路由
- Token 验证中间件提供多层安全保护

### 安全特性

- **路径保护**：只允许访问已注册的路由
- **Token 验证**：支持 API 级别的独立 Token 验证
- **访问统计**：记录所有 API 访问情况，便于审计
- **动态控制**：支持运行时启用/禁用 API，无需重启服务
- **错误隔离**：Token 验证失败不影响其他功能正常使用

---

## 🛠️ 扩展开发

### 添加新的业务模块

1. **创建模块目录**：
   ```
   api/your_module/          # 业务逻辑
   routes/your_module/       # 路由定义
   ```

2. **实现路由注册**：
   ```python
   # routes/your_module/your_routes.py
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/your_module", tags=["your_module"])
   
   @router.get("/test")
   async def test_api():
       return {"message": "Hello from your module"}
   
   def register_routes(app):
       app.include_router(router)
   ```

3. **注册到主应用**：在 `main.py` 中添加模块导入和注册

### Token 验证集成

新模块的 API 会自动支持 Token 验证，无需额外配置。如需自定义验证逻辑：

```python
from methods.token_manner import verify_api_token

@router.get("/secure-endpoint")
async def secure_endpoint(request: Request):
    # 手动验证 Token（可选）
    is_valid, message, debug_info = verify_api_token("/your_module/secure-endpoint", request)
    
    if not is_valid:
        return {"error": f"Token验证失败: {message}"}
    
    return {"message": "验证通过"}
```

---

## 📊 管理后台功能

### 路由管理

- **状态控制**：一键启用/禁用 API
- **搜索过滤**：快速查找特定路由
- **批量操作**：支持批量管理路由状态

### Token 管理

- **配置界面**：直观的 Token 配置模态框
- **统计分析**：Token 使用情况统计和趋势分析
- **安全监控**：Token 验证成功率和异常监控

### 系统监控

- **实时监控**：CPU、内存使用率实时显示
- **运行环境**：系统信息、容器环境检测
- **性能分析**：API 调用频率和响应时间分析

### 数据可视化

- **图表展示**：使用 ECharts 展示统计数据
- **趋势分析**：API 调用趋势和热门排行
- **自定义视图**：支持多种图表类型和时间范围

---

## ❓ 常见问题

### API 访问问题

1. **API 返回 403 错误**
   - 可能是 API 被管理员禁用，请联系管理员
   - 检查是否访问了未注册的路由

2. **Token 验证失败 (401)**
   - 检查 Token 是否正确
   - 确认 Token 是否已过期
   - 查看管理后台确认 API 是否启用了 Token 验证

3. **获取不到成绩数据**
   - 检查 maimai Token 是否正确
   - 检查网络连接
   - 确认用户名是否存在

### 系统问题

4. **日志文件不生成**
   - 确认程序有写入权限
   - 检查磁盘空间
   - 查看控制台是否有权限错误

5. **系统监控数据不准确**
   - 在容器或虚拟环境中，某些系统信息可能无法准确获取
   - 确保已安装 psutil 库：`pip install psutil`

6. **管理界面显示异常**
   - 清除浏览器缓存重试
   - 检查静态文件是否正常加载
   - 查看浏览器控制台是否有 JavaScript 错误

### Token 管理问题

7. **Token 设置无效**
   - 确认是否已提交配置
   - 检查 Token 格式是否正确
   - 查看日志确认配置是否成功

8. **统计数据不更新**
   - 检查数据库是否正常工作
   - 确认中间件是否正常运行
   - 查看日志确认统计记录是否正常

---

## 📈 性能优化建议

### 数据库优化

- 定期清理历史统计数据
- 使用索引优化查询性能
- 合理设置数据库连接池

### Token 验证优化

- 避免设置过短的过期时间，减少验证频率
- 合理使用缓存机制
- 定期清理过期的 Token 配置

### 系统资源优化

- 监控 CPU 和内存使用情况
- 合理设置日志级别，避免过多调试日志
- 使用负载均衡分散请求压力

---

## 🔄 部署建议

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 9090

CMD ["python", "main.py"]
```

### 生产环境配置

1. **使用 HTTPS**：配置 SSL 证书
2. **反向代理**：使用 Nginx 或其他代理服务器
3. **安全**：
   - 定期更换 Token
   - 限制管理界面访问IP
   - 启用访问日志审计

---

## 🙏 鸣谢

- [Yuri-YuzuChaN](https://github.com/Yuri-YuzuChaN) - maimai 模块原作者，提供了优秀的 [nonebot-plugin-maimaidx](https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx) 项目
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能的 Python Web 框架
- [ECharts](https://echarts.apache.org/) - 强大的数据可视化库
- [Psutil](https://psutil.readthedocs.io/) - 系统和进程监控库
- 所有为本项目提供反馈、建议和贡献的开发者和用户

---

## 📄 许可证

本项目基于 MIT 许可证开源。

maimai 相关模块基于 [nonebot-plugin-maimaidx](https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx) 项目修改，请遵循原项目的许可要求。

---

## 🔗 相关链接

- [项目首页](https://github.com/huanxin996/YuanShen)
- [问题反馈](https://github.com/huanxin996/YuanShen/issues)
- [更新日志](https://github.com/huanxin996/YuanShen/releases)
- [开发文档](./docs/)

---

**YuanShen API框架 - 让API管理更简单、更安全、更高效！**