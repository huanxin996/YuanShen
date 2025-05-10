# YuanShen API框架

YuanShen 是一个基于 FastAPI 的高性能 API 框架，支持多种数据服务模块的灵活接入与统一管理。框架内置了 API 管理后台、访问统计、动态路由控制、日志系统等功能，适合二次开发和多业务场景扩展。

---

## 🌟 框架亮点

- **模块化设计**：支持多业务模块（如 maimai、admin）灵活接入
- **API 访问统计与热门排行**：自动统计各 API 调用次数，后台可视化展示
- **动态路由管理**：支持在线启用/禁用 API，无需重启服务
- **强大的管理后台**：可视化操作、权限控制、实时监控
- **安全与访问控制**：内置路由保护中间件，静态资源与管理端独立隔离
- **高效日志系统**：日志按日期自动轮转，便于追踪与审计
- **系统资源监控**：实时监控服务器CPU、内存占用及运行环境

---

## 🆕 更新内容

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
- 支持曲目信息查询、图片生成等功能
- 典型接口如 `/maimai/b50`、`/maimai/minfo` 等
- 基于 [nonebot-plugin-maimaidx](https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx) 项目改造开发
- 静态资源文件请从原项目中获取，并放在main.py同级目录下

### 2. `admin` 管理模块

- 提供 `/admin/manage` 管理后台页面
- 支持 API 路由启用/禁用、访问统计、热门排行等功能
- 可视化展示 API 总数、总访问量、访问量前三的 API
- 支持一键操作 API 状态，安全高效
- 系统资源监控，包括CPU使用率、内存占用、运行环境等

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
    admin_token = "你的管理员token"    # 管理员访问Token
    log_level = "info"                # 日志级别，可选值：debug, info, warning, error
    ```

4. 运行服务

    ```bash
    python main.py
    ```

---

## 🚀 API 快速参考

### maimai 成绩生成类 API

| 端点                      | 方法 | 描述                       |
|---------------------------|------|----------------------------|
| `/maimai/b50`             | POST | 生成标准B50图片            |
| `/maimai/bypass50`        | POST | 生成Bypass B50图片         |
| `/maimai/theoretical50`   | POST | 生成理论值B50图片          |
| `/maimai/cum50`           | POST | 生成积分B50图片            |
| `/maimai/abstract50`      | POST | 生成简洁版B50图片          |
| `/maimai/high50`          | POST | 生成高分B50图片            |
| `/maimai/ap50`            | POST | 生成AP成绩B50图片          |
| `/maimai/fc50`            | POST | 生成FC成绩B50图片          |
| `/maimai/minfo`           | POST | 获取maimai歌曲基本信息图片 |

**请求参数示例：**

```json
{
  "qq": "12345678",      // QQ号（可选）
  "name": "玩家昵称"      // 玩家昵称（可选，qq和name至少填一个）
}
```

- `/maimai/minfo` 需额外提供 `songid` 字段。

**响应格式：**

```json
{
  "returnCode": 1,      // 1表示成功，100/101等为错误码
  "base64": "..."       // 图片base64字符串（如有）
}
```

---

### admin 管理模块 API

| 端点            | 方法 | 描述                       |
|-----------------|------|----------------------------|
| `/admin/manage` | GET  | 访问管理界面               |
| `/admin/action` | POST | 启用/禁用指定API           |
| `/admin/stats`  | GET  | 查看API统计和系统信息      |

**管理后台功能：**

- 查看 API 总数和总调用次数
- 热门 API 排行（调用频率最高的3个API）
- API 调用趋势图（最近7天）
- 启用/禁用特定 API 端点
- 系统资源监控（CPU、内存使用率）
- 运行环境信息（系统类型、容器状态、FastAPI版本）

---

## 📝 日志系统

- 日志存储在项目根目录下的 `log` 文件夹
- 日志文件按日期命名（YYYY-MM-DD.log）
- 日志级别可在 `config.py` 中配置

---

## 🔒 路由与安全

- 所有 API 路由均通过 `RouteProtectionMiddleware` 进行保护
- 管理界面和静态资源有专门的访问控制
- 支持动态启用/禁用 API 路由

---

## 🛠️ 扩展开发

如需添加新的业务模块：

1. 在 `api/` 目录下添加新目录
   - 例如：`api/maimai50/`
2. 在 `routes/maimai50/除__init__.py文件的py文件` 中使用register_routes注册新路由
3. 如需扩展maimai50模块，可在 `routes/maimai50/` 目录下开发
4. 如需扩展管理功能，可在 `routes/admin/` 目录下开发

---

## ❓ 常见问题

1. **API 返回 403 错误**
    - 可能是 API 被管理员禁用，请联系管理员

2. **获取不到成绩数据**
    - 检查 Token 是否正确
    - 检查网络连接

3. **日志文件不生成**
    - 确认程序有写入权限
    - 检查磁盘空间

4. **系统监控数据不准确**
    - 在容器或虚拟环境中，某些系统信息可能无法准确获取
    - 确保已安装 psutil 库：`pip install psutil`

---

## 🙏 鸣谢

- [Yuri-YuzuChaN](https://github.com/Yuri-YuzuChaN) - maimai 模块原作者，提供了优秀的 [nonebot-plugin-maimaidx](https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx) 项目
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能的 Python Web 框架
- 所有为本项目提供反馈、建议和贡献的开发者和用户

---

## 📄 许可证

本项目基于 MIT 许可证开源。

maimai 相关模块基于 [nonebot-plugin-maimaidx](https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx) 项目修改，请遵循原项目的许可要求。
