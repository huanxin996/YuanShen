# KFC50 API服务

KFC50 是一个基于 FastAPI 的后端服务，为舞萌DX（maimai）玩家提供 B50 成绩数据生成、分析和管理功能。项目支持多种自定义 B50 视图生成方式，并内置了强大的 API 管理后台。

---

## 功能特性

- 多种 B50 成绩视图生成（标准、Bypass、理论值、累计分数、高分、AP、FC 等）
- API 访问统计与热门排行
- 路由状态管理（支持启用/禁用 API）
- 管理后台界面，支持可视化操作
- 访问控制与安全保护
- 按日期自动轮转的日志系统

---

## 安装与配置

### 前提条件

- Python 3.8+
- 舞萌DX账号 Token

### 安装步骤

1. 克隆代码库

    ```bash
    git clone https://github.com/huanxin996/kfc50.git
    cd kfc50
    ```

2. 安装依赖

    ```bash
    pip install -r requirements.txt
    ```

3. 配置

    编辑 `config.py` 文件，设置必要参数：

    ```python
    maimaitoken = "你的水鱼token"      # 舞萌DX账号Token
    admin_token = "你的管理员token"    # 管理员访问Token
    log_level = "info"                # 日志级别，可选值：debug, info, warning, error
    ```

4. 运行服务

    ```bash
    python main.py
    ```

---

## API文档

服务默认运行在 `http://0.0.0.0:9090`

### 主要 API 端点

#### 成绩生成类 API

| 端点                  | 方法 | 描述                       |
|-----------------------|------|----------------------------|
| `/maimai/b50`         | POST | 生成标准B50图片            |
| `/maimai/bypass50`    | POST | 生成Bypass B50图片         |
| `/maimai/theoretical50` | POST | 生成理论值B50图片         |
| `/maimai/cum50`       | POST | 生成积分B50图片            |
| `/maimai/abstract50`  | POST | 生成简洁版B50图片          |
| `/maimai/high50`      | POST | 生成高分B50图片            |
| `/maimai/ap50`        | POST | 生成AP成绩B50图片          |
| `/maimai/fc50`        | POST | 生成FC成绩B50图片          |
| `/maimai/minfo`       | POST | 获取maimai歌曲基本信息图片 |

#### 管理 API

| 端点            | 方法 | 描述                       |
|-----------------|------|----------------------------|
| `/admin/manage` | GET  | 访问管理界面               |
| `/admin/action` | POST | 启用/禁用指定API           |

---

### 请求参数说明

- 所有 B50 相关 API 均需 POST JSON 请求体，参数示例：

    ```json
    {
      "qq": "12345678",      // QQ号（可选）
      "name": "玩家昵称"      // 玩家昵称（可选，qq和name至少填一个）
    }
    ```

- `/maimai/minfo` 需额外提供 `songid` 字段。

---

### 响应格式

所有 API 返回 JSON 格式数据：

```json
{
  "returnCode": 1,      // 1表示成功，100/101等为错误码
  "msg": "success",     // 状态描述
  "base64": "..."       // 图片base64字符串（如有）
}
```

---

## 管理界面

系统提供了一个可视化管理后台，便于监控和管理 API：

- 访问地址：`/admin/manage`
- 功能：
  - 查看 API 总数和总调用次数
  - 查看热门 API 排行（调用频率最高的3个API）
  - 启用/禁用特定 API 端点
  - 查看每个 API 的访问次数

---

## 日志系统

- 日志存储在项目根目录下的 `log` 文件夹
- 日志文件按日期命名（YYYY-MM-DD.log）
- 日志级别可在 `config.py` 中配置

---

## 路由与安全

- 所有 API 路由均通过 `RouteProtectionMiddleware` 进行保护
- 管理界面和静态资源有专门的访问控制
- 支持动态启用/禁用 API 路由

---

## 扩展开发

如需添加新的 B50 生成方式：

1. 在 `api/maimai50/` 目录下实现相应功能
2. 在 `routes/maimai50/50routes.py` 中注册新路由

---

## 常见问题

1. **API 返回 403 错误**
    - 可能是 API 被管理员禁用，请联系管理员

2. **获取不到成绩数据**
    - 检查 Token 是否正确
    - 检查网络连接

3. **日志文件不生成**
    - 确认程序有写入权限
    - 检查磁盘空间

---

## 开发者信息

- 作者：HuanXin996
- 版本：1.0.0
- 许可证：MIT

---