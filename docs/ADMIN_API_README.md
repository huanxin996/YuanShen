# Admin 管理模块文档

本文档详细介绍 YuanShen API 框架中的 admin 管理模块相关接口和功能。

## 🌟 功能概览

Admin 管理模块是 YuanShen API 框架的核心控制中心，提供以下关键功能：

- **API 状态管理**：动态启用/禁用 API 路由
- **Token 安全管理**：为每个 API 配置独立的 Token 验证
- **访问统计与数据分析**：实时监控 API 调用情况和趋势
- **系统资源监控**：CPU、内存使用率及运行环境信息展示
- **可视化管理界面**：友好的 Web 管理后台

## 🚀 主要接口

### 管理界面及数据接口

| 端点 | 方法 | 描述 | 权限要求 |
|------|------|------|---------|
| `/admin/manage` | GET | 路由状态管理界面 | 管理员 |
| `/admin/stats` | GET | API统计和系统监控界面 | 管理员 |
| `/admin/settings` | GET | 系统设置界面 | 管理员 |
| `/admin/action` | POST | 控制 API 启用/禁用 | 管理员 |
| `/admin/token/action` | POST | Token 配置管理 | 管理员 |
| `/admin/token/query` | POST | 查询 Token 信息和使用统计 | 管理员 |

### 管理后台功能详解

#### `/admin/manage` - 路由状态管理界面

提供一个可视化的路由管理界面，包含：

- **路由列表**：显示所有 API 路由及其状态
- **搜索功能**：快速查找特定路由
- **状态控制**：一键启用/禁用 API
- **Token 配置**：为每个 API 配置独立的 Token 验证
- **访问统计**：显示每个 API 的调用次数

**界面特性：**
- 实时状态显示（启用/禁用）
- Token 配置状态（未启用/默认Token/自定义Token）
- 操作按钮（启用/禁用、Token设置）
- 搜索过滤功能

#### `/admin/stats` - 统计分析界面

提供全面的系统统计信息和数据可视化：

- **总体统计**：API 总数、总调用次数、禁用数量
- **热门排行**：访问量前三的 API
- **趋势图表**：过去 7 天的调用趋势
- **饼图分析**：API 调用分布情况
- **系统监控**：CPU、内存使用率、运行环境信息

#### `/admin/action` - API 控制

用于动态控制 API 的启用或禁用状态。

**请求参数（表单数据）：**

```
action: "disable:/maimai/b50"  # 操作类型:路径，格式为 "enable:路径" 或 "disable:路径"
```

**响应：**
- 成功：重定向到管理界面
- 失败：返回 JSON 错误信息

#### `/admin/token/action` - Token 管理

用于配置和管理 API 的 Token 验证。

**请求参数（表单数据）：**

```
api_path: "/maimai/b50"        # API 路径
token_action: "enable"         # 操作类型
custom_token: "abc123..."      # 自定义 Token（可选）
expire_time: 3600000          # 过期时间（毫秒）
```

**支持的操作类型：**
- `enable`：启用 Token 验证
- `disable`：禁用 Token 验证
- `set_custom`：设置自定义 Token
- `generate`：生成新的随机 Token
- `remove_custom`：移除自定义 Token，使用默认 Token

**响应：**
- 成功：重定向到管理界面
- 失败：返回 JSON 错误信息

#### `/admin/token/query` - Token 信息查询

用于查询 API 的 Token 配置和使用统计。

**请求参数（表单数据）：**

```
api_path: "/maimai/b50"        # API 路径
query_type: "info"             # 查询类型：info 或 usage
days: 7                        # 统计天数（仅 usage 查询需要）
```

**info 查询响应格式：**

```json
{
  "success": true,
  "query_type": "info",
  "api_path": "/maimai/b50",
  "token_enabled": true,         # Token 是否启用
  "has_custom_token": true,      # 是否有自定义 Token
  "custom_token": "abc123...",   # 自定义 Token
  "expire_time_ms": 3600000,     # 过期时间（毫秒）
  "default_token": "def456...",  # 默认 Token
  "default_expire_ms": 3600000   # 默认过期时间
}
```

**usage 查询响应格式：**

```json
{
  "success": true,
  "query_type": "usage",
  "api_path": "/maimai/b50",
  "days": 7,
  "usage_stats": {
    "stats": {
      "/maimai/b50": {
        "total_success": 150,      # 总成功次数
        "total_failure": 5,        # 总失败次数
        "dates": {                 # 每日统计
          "2025-06-15": {
            "success": 30,
            "failure": 1,
            "total": 31
          }
        }
      }
    },
    "summary": {
      "total_apis": 1,
      "date_range": "2025-06-10 to 2025-06-16"
    }
  }
}
```

## 📊 Token 管理系统

### Token 验证机制

1. **默认 Token**：系统全局默认 Token，所有启用验证的 API 共享
2. **自定义 Token**：为特定 API 设置独立的 Token
3. **过期时间**：Token 的有效期，默认 1 小时（3600000 毫秒）
4. **验证统计**：记录每次 Token 验证的成功/失败情况

### Token 配置流程

1. **启用验证**：在管理界面点击 Token 设置按钮
2. **选择类型**：使用默认 Token 或设置自定义 Token
3. **配置参数**：设置 Token 值和过期时间
4. **保存配置**：提交后立即生效

### 安全特性

- **独立验证**：每个 API 可配置独立的 Token
- **动态管理**：支持实时启用/禁用，无需重启服务
- **使用统计**：详细记录 Token 使用情况，便于审计
- **过期控制**：灵活的过期时间设置

## 📈 统计数据说明

### API 访问统计

- `api_count:{path}`：API 总调用次数
- `api_daily_stats:{path}`：API 每日调用统计
- `api_total_daily_stats`：全站每日总调用统计

### Token 使用统计

- 记录每次 Token 验证的结果
- 按日期统计成功/失败次数
- 计算成功率和趋势分析

### 系统监控数据

```json
{
  "system_info": {
    "os_info": "Linux 5.4.0",           # 操作系统信息
    "container_env": "Docker",           # 容器环境
    "fastapi_version": "0.95.1",         # FastAPI 版本
    "mem_total": "8.00 GB",              # 总内存
    "mem_used": "2.50 GB",               # 已用内存
    "mem_available": "5.50 GB",          # 可用内存
    "system_mem_percent": 31.25,         # 系统内存使用率
    "process_mem": "256.00 MB",          # 进程内存使用
    "process_percent": "3.1%",           # 进程内存占比
    "system_cpu_percent": 15.2,          # 系统 CPU 使用率
    "cpu_count": 4,                      # CPU 核心数
    "process_cpu_percent": 2.1,          # 进程 CPU 使用率
    "server_start_timestamp": 1684234567  # 服务启动时间戳
  }
}
```

## 💻 使用示例

### Python 脚本控制API状态

```python
import requests

# 禁用特定API
def disable_api(api_path):
    url = "https://your-api-domain.com/admin/action"
    data = {
        "action": f"disable:{api_path}"
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code == 303:  # 重定向表示成功
        print(f"成功禁用 API: {api_path}")
    else:
        print(f"操作失败: {response.text}")

# 启用API的Token验证
def enable_token(api_path, custom_token=None, expire_time=3600000):
    url = "https://your-api-domain.com/admin/token/action"
    data = {
        "api_path": api_path,
        "token_action": "set_custom" if custom_token else "enable",
        "expire_time": expire_time
    }
    
    if custom_token:
        data["custom_token"] = custom_token
    
    response = requests.post(url, data=data)
    
    if response.status_code == 303:
        print(f"成功配置 Token: {api_path}")
    else:
        print(f"配置失败: {response.text}")

# 查询Token信息
def get_token_info(api_path):
    url = "https://your-api-domain.com/admin/token/query"
    data = {
        "api_path": api_path,
        "query_type": "info"
    }
    
    response = requests.post(url, data=data)
    info = response.json()
    
    if info.get("success"):
        print(f"API: {info['api_path']}")
        print(f"Token启用: {info['token_enabled']}")
        print(f"自定义Token: {info['has_custom_token']}")
        print(f"过期时间: {info['expire_time_ms']}ms")
    else:
        print(f"查询失败: {info.get('error')}")

# 使用示例
disable_api("/maimai/b50")
enable_token("/maimai/b50", "my_custom_token_123", 7200000)
get_token_info("/maimai/b50")
```

### 获取使用统计

```python
def get_token_usage(api_path, days=7):
    url = "https://your-api-domain.com/admin/token/query"
    data = {
        "api_path": api_path,
        "query_type": "usage",
        "days": days
    }
    
    response = requests.post(url, data=data)
    usage = response.json()
    
    if usage.get("success"):
        stats = usage["usage_stats"]["stats"].get(api_path, {})
        if stats:
            print(f"API: {api_path}")
            print(f"成功: {stats['total_success']} 次")
            print(f"失败: {stats['total_failure']} 次")
            print(f"成功率: {stats['total_success']/(stats['total_success']+stats['total_failure'])*100:.1f}%")
        else:
            print(f"暂无使用记录: {api_path}")
    else:
        print(f"查询失败: {usage.get('error')}")

# 使用示例
get_token_usage("/maimai/b50", 30)
```

## 🎨 管理界面特性

### 响应式设计

- 支持桌面端和移动端访问
- 自适应布局，优化不同屏幕尺寸显示

### 交互体验

- **模态框设计**：Token 配置使用流畅的模态框交互
- **动画效果**：页面切换和操作反馈有流畅的渐入渐出动画
- **实时反馈**：操作状态实时更新，提供清晰的视觉反馈
- **搜索过滤**：支持实时搜索过滤路由列表

### 数据可视化

- **ECharts 图表**：使用专业图表库展示统计数据
- **饼图分析**：API 调用分布一目了然
- **趋势线图**：历史调用趋势清晰展示
- **实时监控**：系统资源使用情况实时更新

## ⚠️ 注意事项

1. **Token 安全**：
   - 定期更换 Token 以提高安全性
   - 避免在日志中记录完整 Token
   - 合理设置过期时间

2. **性能考虑**：
   - 避免频繁启用/禁用API，可能影响系统稳定性
   - Token 验证会增加请求处理时间
   - 统计数据存储在数据库中，定期清理历史数据

3. **备份数据**：
   - 定期备份 API 统计和配置数据
   - Token 配置信息存储在 `token_configs` 表中

4. **访问控制**：
   - 管理界面无需额外 Token 验证
   - 所有 `/admin/` 路径自动放行
   - 确保管理界面的网络访问安全

## 🔍 故障排查

1. **API状态修改未生效**
   - 检查路由保护中间件是否正常运行
   - 查看应用日志确认操作是否成功
   - 尝试重启服务

2. **Token验证异常**
   - 检查 Token 配置是否正确
   - 确认过期时间设置合理
   - 查看 Token 使用统计排查问题

3. **模态框显示异常**
   - 确保静态文件正常加载
   - 检查浏览器控制台是否有 JavaScript 错误
   - 清除浏览器缓存重试

4. **统计数据不准确**
   - 检查数据库是否正常工作
   - 确认路由中间件正常运行
   - 查看日志确认统计记录是否正常

5. **系统监控数据异常**
   - 确保已安装 `psutil` 库
   - 在容器环境中，部分系统数据可能无法准确获取
   - 检查系统权限是否足够

## 🔗 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Psutil 文档](https://psutil.readthedocs.io/)
- [ECharts 文档](https://echarts.apache.org/)
- [Jinja2 模板文档](https://jinja.palletsprojects.com/)