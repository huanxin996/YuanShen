# Admin 管理模块文档

本文档详细介绍 YuanShen API 框架中的 admin 管理模块相关接口和功能。

## 🌟 功能概览

Admin 管理模块是 YuanShen API 框架的核心控制中心，提供以下关键功能：

- API 状态管理（启用/禁用）
- 访问统计与数据分析
- 系统资源监控
- 运行环境信息展示

## 🚀 主要接口

### 管理界面及数据接口

| 端点 | 方法 | 描述 | 权限要求 |
|------|------|------|---------|
| `/admin/manage` | GET | 访问管理后台界面 |
| `/admin/action` | POST | 控制 API 启用/禁用 |
| `/admin/stats` | GET | 获取 API 统计和系统信息 |

### 管理后台功能详解

#### `/admin/manage` - 管理界面

提供一个可视化的管理界面，包含：

- API 路由总览
- 系统状态监控面板
- API 调用统计图表
- 控制中心功能区


#### `/admin/action` - API 控制

用于动态控制 API 的启用或禁用状态。

**请求参数：**

```json
{
  "path": "/maimai/b50",   // 要操作的API路径
  "action": "disable",     // 操作类型：enable 或 disable
  "token": "your_admin_token" // 管理员令牌
}
```

**响应格式：**

```json
{
  "status": "success",     // 操作状态：success 或 error
  "message": "API已禁用",   // 操作结果描述
  "api_path": "/maimai/b50" // 被操作的API路径
}
```

#### `/admin/stats` - 统计信息

提供系统统计信息和 API 调用数据。

**请求方式：**

```
GET https://your-api-domain.com/admin/stats?token=your_admin_token
```

**响应格式：**

```json
{
  "api_stats": {
    "total_apis": 15,            // API总数
    "total_calls": 1245,         // API总调用次数
    "most_popular": [            // 最热门的三个API
      {
        "path": "/maimai/b50",
        "calls": 532
      },
      {
        "path": "/maimai/minfo",
        "calls": 312
      },
      {
        "path": "/maimai/fc50",
        "calls": 198
      }
    ],
    "daily_trend": [             // 过去7天的API调用趋势
      {"date": "2025-05-15", "calls": 120},
      {"date": "2025-05-16", "calls": 145},
      // ...其他日期数据
    ]
  },
  "system_info": {
    "cpu_usage": 32.5,           // CPU使用率(%)
    "memory_usage": {
      "used": 1024,              // 已用内存(MB)
      "total": 8192,             // 总内存(MB)
      "percent": 12.5            // 内存使用百分比
    },
    "environment": {
      "system": "Linux",         // 操作系统类型
      "in_container": true,      // 是否在容器中运行
      "python_version": "3.9.6", // Python版本
      "fastapi_version": "0.95.1" // FastAPI版本
    },
    "uptime": "5d 12h 34m"       // 系统运行时间
  }
}
```

## 📊 数据存储

管理模块使用以下数据表：

1. `api_routes` - 存储API路由信息和状态
2. `api_stats` - 存储API调用统计数据
3. `daily_stats` - 按天存储API调用趋势
4. `admin_logs` - 存储管理操作日志

## 💻 使用示例

### Python 脚本控制API状态

```python
import requests
import json

# 禁用特定API
def disable_api(api_path):
    url = "https://your-api-domain.com/admin/action"
    payload = {
        "path": api_path,
        "action": "disable",
        "token": "your_admin_token"
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    if result.get("status") == "success":
        print(f"成功: {result.get('message')}")
    else:
        print(f"失败: {result.get('message')}")

# 使用示例
disable_api("/maimai/b50")
```

### 获取系统状态

```python
import requests

def get_system_stats():
    url = "https://your-api-domain.com/admin/stats"
    params = {"token": "your_admin_token"}
    
    response = requests.get(url, params=params)
    stats = response.json()
    
    print(f"系统信息:")
    print(f"- CPU使用率: {stats['system_info']['cpu_usage']}%")
    print(f"- 内存使用: {stats['system_info']['memory_usage']['percent']}%")
    print(f"- 运行环境: {stats['system_info']['environment']['system']}")
    print(f"- 运行时间: {stats['system_info']['uptime']}")
    print("\nAPI统计:")
    print(f"- 总API数: {stats['api_stats']['total_apis']}")
    print(f"- 总调用次数: {stats['api_stats']['total_calls']}")
    print("- 最热门API:")
    for api in stats['api_stats']['most_popular']:
        print(f"  * {api['path']}: {api['calls']}次调用")

# 使用示例
get_system_stats()
```

## ⚠️ 注意事项

1. **频繁操作**：避免频繁启用/禁用API，可能影响系统稳定性
2. **备份数据**：定期备份API统计和配置数据
3. **监控告警**：建议配置系统资源使用率告警

## 🔍 故障排查

1. **API状态修改未生效**
   - 检查管理日志确认操作是否成功
   - 尝试刷新缓存或重启服务

2. **系统监控数据异常**
   - 确保已安装 `psutil` 库
   - 在容器环境中，部分系统数据可能无法准确获取

3. **统计数据不准确**
   - 检查数据库是否正常工作
   - 确认路由中间件正常运行

## 🔗 相关资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Psutil 文档](https://psutil.readthedocs.io/)
- [SQLite 文档](https://www.sqlite.org/docs.html)