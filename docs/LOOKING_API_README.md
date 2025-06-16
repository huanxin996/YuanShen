# Looking 设备监控模块文档

本文档详细介绍 YuanShen API 框架中的 Looking 设备监控模块相关接口和功能。

## 🌟 功能概览

Looking 设备监控模块是专为 Android 设备设计的全方位监控解决方案，提供以下核心功能：

- **设备事件监控**：实时捕获锁屏/解锁事件，自动计算亮屏时间
- **保活连接管理**：维护设备连接状态，自动检测离线设备
- **设备状态收集**：收集详细的系统状态信息（CPU、内存、电池、网络等）
- **使用统计分析**：基于北京时间的设备使用习惯分析
- **签名验证安全**：支持MD5签名验证，确保数据来源可信

## 🚀 主要接口

### 核心监控接口

| 端点 | 方法 | 描述 | 签名要求 |
|------|------|------|---------|
| `/looking/device-event` | POST | 接收设备锁屏事件 | ✅ 必需 |
| `/looking/keep-alive` | POST | 设备保活心跳 | ✅ 必需（特殊处理） |
| `/looking/device-status` | POST | 上报设备状态信息 | ✅ 必需 |

### 数据查询接口

| 端点 | 方法 | 描述 | 权限要求 |
|------|------|------|---------|
| `/looking/device-list` | GET | 获取所有监控设备列表 | 🔓 公开 |
| `/looking/device-summary/{device_id}` | GET | 获取设备使用摘要 | 🔓 公开 |
| `/looking/device-status/{device_id}` | GET | 获取设备最新状态 | 🔓 公开 |

### 保活管理接口

| 端点 | 方法 | 描述 | 权限要求 |
|------|------|------|---------|
| `/looking/alive-manager/status` | GET | 获取保活管理器状态 | 🔓 公开 |
| `/looking/alive-manager/check/{device_id}` | POST | 强制检查设备保活状态 | 🔓 公开 |
| `/looking/alive-manager/device/{device_id}` | GET | 获取设备保活详细信息 | 🔓 公开 |

## 📱 核心接口详解

### `/looking/device-event` - 设备事件上报

接收 Android 设备的锁屏/解锁事件，自动计算设备使用时间。

**请求方式：** POST

**必需 Headers：**
```http
Content-Type: application/json
X-Device-Id: HW_20b539c032526f01a171b35884404a23
X-Device-Model: HUAWEI P40 Pro
X-Device-Brand: HUAWEI
X-Android-Version: 10
X-SDK-Int: 29
X-App-Version: 1.0.0
X-Event-Type: lock_event
X-Timestamp: 1749889822687
X-Signature: e6fd8d7547b51828991b1f010025515b
```

**请求体格式：**
```json
{
  "event_type": "lock_event",
  "timestamp": 1749889822687,
  "date": "2025-06-14",
  "action": "unlocked",
  "description": "用户解锁设备"
}
```

**支持的动作类型：**
- `unlocked`: 设备解锁
- `locked`: 设备锁屏
- `screen_on`: 屏幕点亮
- `screen_off`: 屏幕熄灭

**响应格式：**
```json
{
  "returnCode": 1,
  "msg": "设备事件处理成功",
  "data": {
    "event_type": "lock_event",
    "processed_at": "2025-06-14 16:30:22",
    "processed_at_timezone": "Asia/Shanghai",
    "timestamp": 1749889822687,
    "device_id": "HW_20b539c032526f01a171b35884404a23",
    "signature_verified": true,
    "action": "unlocked",
    "description": "用户解锁设备",
    "summary": {
      "today_summary": "今日使用时间: 2小时34分钟, 解锁次数: 23次",
      "current_session_time": "15分钟32秒",
      "is_locked": false
    }
  }
}
```

### `/looking/keep-alive` - 保活心跳

维护设备与服务器的连接状态，支持自动离线检测。

**请求方式：** POST

**必需 Headers：**
```http
Content-Type: application/json
X-Device-Id: HW_20b539c032526f01a171b35884404a23
X-Device-Model: HUAWEI P40 Pro
X-Device-Brand: HUAWEI
X-Android-Version: 10
X-SDK-Int: 29
X-Event-Type: keep_alive
X-Signature: a1b2c3d4e5f6789012345678901234567
```

**请求体格式：**
```json
{
  "status": "active"
}
```

**特殊签名处理：**
保活请求的签名基于服务器当前时间计算，支持 ±3秒 的时间容差，以处理网络延迟和时钟偏差。

**响应格式：**
```json
{
  "returnCode": 1,
  "msg": "保活请求处理成功",
  "data": {
    "device_id": "HW_20b539c032526f01a171b35884404a23",
    "server_time": "2025-06-14 16:30:22",
    "server_timestamp_ms": 1749889822687,
    "timezone": "Asia/Shanghai",
    "signature_verified": true,
    "time_sync_info": {
      "server_timestamp_ms": 1749889822687,
      "client_estimated_timestamp_ms": 1749889821854,
      "time_offset_seconds": 1,
      "time_difference_ms": 833,
      "time_difference_seconds": 0.833,
      "tolerance_applied": "±3秒",
      "sync_status": "正常"
    }
  }
}
```

### `/looking/device-status` - 设备状态上报

收集设备的详细系统状态信息。

**请求方式：** POST

**必需 Headers：**
```http
Content-Type: application/json
X-Device-Id: HW_20b539c032526f01a171b35884404a23
X-Device-Model: HUAWEI P40 Pro
X-Device-Brand: HUAWEI
X-Android-Version: 10
X-SDK-Int: 29
X-Event-Type: device_status
X-Signature: b2c3d4e5f67890123456789012345678
```

**请求体格式：**
```json
{
  "uptime": {
    "total_milliseconds": 54218000,
    "days": 0,
    "hours": 15,
    "minutes": 3,
    "seconds": 38,
    "formatted_string": "0 days 15:03:38"
  },
  "network": {
    "full_status": "wifi(ssid:CU_sDfT_5G,signal:-38dBm,speed:1152Mbps)-internet-validated",
    "type": "wifi",
    "wifi_details": {
      "ssid": "CU_sDfT_5G",
      "signal_strength_dbm": -38,
      "link_speed_mbps": 1152
    },
    "has_internet": true,
    "is_validated": true
  },
  "cpu": {
    "full_info": "cores:8,arch:arm64-v8a,max_freq:2265MHz",
    "cores": 8,
    "architecture": "arm64-v8a",
    "max_frequency_mhz": 2265,
    "max_frequency_khz": 2265000
  },
  "thermal": {
    "full_info": "battery:33.0C",
    "battery_celsius": 33.0,
    "thermal_zones": []
  },
  "storage": {
    "full_info": "internal:total:933.0GB,used:563.3GB,free:369.7GB",
    "internal": {
      "total_formatted": "933.0GB",
      "total_bytes": 1001801121792,
      "used_formatted": "563.3GB",
      "used_bytes": 604838769459,
      "free_formatted": "369.7GB",
      "free_bytes": 396962352332
    },
    "external": {
      "total_formatted": "933.0GB",
      "total_bytes": 1001801121792,
      "used_formatted": "563.3GB",
      "used_bytes": 604838769459,
      "free_formatted": "369.7GB",
      "free_bytes": 396962352332
    }
  },
  "foreground_app": {
    "full_info": "package:com.tencent.mobileqq,pid:12843",
    "package_name": "com.tencent.mobileqq",
    "app_display_name": "QQ",
    "process_id": 12843
  },
  "battery": {
    "full_info": "level:92%,status:discharging,power:battery,health:good,temp:32.7°C,voltage:4178mV,tech:Li-ion",
    "level_percentage": 92,
    "is_charging": false,
    "status_string": "discharging",
    "power_source_string": "battery",
    "health_string": "good",
    "temperature_celsius": 32.7,
    "voltage_mv": 4178,
    "voltage_v": 4.178,
    "technology": "Li-ion"
  },
  "timestamp": 1749889822687,
  "device_id": "HW_20b539c032526f01a171b35884404a23"
}
```

**响应格式：**
```json
{
  "returnCode": 1,
  "msg": "设备状态处理成功",
  "data": {
    "device_id": "HW_20b539c032526f01a171b35884404a23",
    "processed_at": "2025-06-14 16:30:22",
    "processed_at_timezone": "Asia/Shanghai",
    "signature_verified": true,
    "status_summary": "设备运行正常: 电池92%, WiFi连接(-38dBm), 存储使用60.4%, CPU温度33°C"
  }
}
```

### `/looking/device-summary/{device_id}` - 设备使用摘要

获取指定设备的详细使用统计信息。

**请求方式：** GET

**URL 参数：**
- `device_id`: 设备唯一标识符

**响应格式：**
```json
{
  "returnCode": 1,
  "msg": "获取设备摘要成功",
  "data": {
    "device_id": "HW_20b539c032526f01a171b35884404a23",
    "today_summary": "今日使用时间: 4小时23分钟, 解锁次数: 67次, 平均会话: 3分52秒",
    "current_session_time": "17分钟45秒",
    "total_screen_time_today": "4小时23分钟16秒",
    "unlock_count_today": 67,
    "average_session_duration": "3分52秒",
    "longest_session_today": "1小时12分钟",
    "is_locked": false,
    "last_event_time": "2025-06-14 16:30:22",
    "last_event_action": "unlocked",
    "device_info": {
      "model": "HUAWEI P40 Pro",
      "brand": "HUAWEI",
      "android_version": "10",
      "sdk_int": 29
    },
    "weekly_trend": [
      {"date": "2025-06-08", "screen_time_minutes": 245},
      {"date": "2025-06-09", "screen_time_minutes": 312},
      {"date": "2025-06-10", "screen_time_minutes": 189},
      {"date": "2025-06-11", "screen_time_minutes": 278},
      {"date": "2025-06-12", "screen_time_minutes": 334},
      {"date": "2025-06-13", "screen_time_minutes": 298},
      {"date": "2025-06-14", "screen_time_minutes": 263}
    ],
    "usage_patterns": {
      "most_active_hour": "20:00-21:00",
      "peak_usage_time": "晚上8点-9点",
      "quiet_period": "凌晨2点-6点"
    },
    "current_beijing_time": "2025-06-14 16:30:22",
    "timezone": "Asia/Shanghai"
  }
}
```

### `/looking/device-list` - 设备列表

获取所有已注册监控设备的列表。

**请求方式：** GET

**响应格式：**
```json
{
  "returnCode": 1,
  "msg": "获取设备列表成功,请使用设备ID查询设备摘要，例如 /looking/device-summary/{device_id}，/looking/device-status/{device_id}",
  "data": {
    "device_count": 3,
    "device_list": [
      "HW_20b539c032526f01a171b35884404a23",
      "XM_9f8e7d6c5b4a3210fedcba0987654321",
      "OP_1a2b3c4d5e6f7890abcdef1234567890"
    ],
    "current_beijing_time": "2025-06-14 16:30:22",
    "timezone": "Asia/Shanghai"
  }
}
```

### `/looking/alive-manager/status` - 保活管理器状态

获取保活连接管理器的运行状态和统计信息。

**请求方式：** GET

**响应格式：**
```json
{
  "returnCode": 1,
  "msg": "获取保活管理器状态成功",
  "data": {
    "is_running": true,
    "check_interval_seconds": 60,
    "alive_timeout_seconds": 61,
    "alive_devices_count": 2,
    "alive_devices": [
      "HW_20b539c032526f01a171b35884404a23",
      "XM_9f8e7d6c5b4a3210fedcba0987654321"
    ],
    "current_beijing_time": "2025-06-14 16:30:22",
    "timezone": "Asia/Shanghai"
  }
}
```

## 🔐 签名验证机制

### 签名生成规则

所有需要签名的接口都使用 MD5 签名验证：

```
signature = MD5(device_id + event_type + timestamp)
```

**Java 客户端示例：**
```java
// 设备事件签名
String signature = DeviceUtils.md5(deviceId, "lock_event", String.valueOf(timestamp));

// 保活签名（使用当前时间戳）
String signature = DeviceUtils.md5(deviceId, "keep_alive", String.valueOf(System.currentTimeMillis()));

// 设备状态签名
String signature = DeviceUtils.md5(deviceId, "device_status", String.valueOf(timestamp));
```

### 时间容差处理

- **设备事件**：使用客户端提供的时间戳，严格验证
- **设备状态**：使用服务器当前时间戳进行验证
- **保活请求**：使用服务器当前时间 ±3秒 范围进行验证，以处理网络延迟

### 签名验证失败处理

当签名验证失败时，服务器会返回详细的调试信息：

```json
{
  "returnCode": 100,
  "msg": "签名验证失败",
  "data": {
    "debug_info": {
      "server_timestamp_ms": "1749889822687",
      "server_time_readable": "2025-06-14 16:30:22",
      "tested_range": "±3秒",
      "device_id": "HW_20b539c032526f01a171b35884404a23",
      "event_type": "keep_alive",
      "received_signature": "e6fd8d7547b51828991b1f010025515b",
      "expected_signature_format": "md5(device_id + event_type + timestamp)",
      "test_signatures": [
        {
          "offset_seconds": -2,
          "timestamp": "1749889820687",
          "expected_signature": "a1b2c3d4e5f6789012345678901234567"
        }
      ]
    }
  }
}
```

## 📊 数据存储结构

### 设备表结构

每个设备拥有独立的数据表：`device_{device_id}`

**主要字段：**
- `device_status`: 设备当前状态信息
- `latest_device_status`: 最新设备状态快照
- `daily_{date}`: 按日期存储的使用记录

### 记录类型

1. **锁屏事件记录**
   ```json
   {
     "timestamp": 1749889822687,
     "action": "unlocked",
     "beijing_time": "2025-06-14 16:30:22",
     "session_id": "session_20250614_163022"
   }
   ```

2. **设备状态记录**
   ```json
   {
     "timestamp": 1749889822687,
     "uptime": {...},
     "network": {...},
     "cpu": {...},
     "battery": {...},
     "server_processed_at": 1749889821854
   }
   ```

3. **保活记录**
   ```json
   {
     "last_keep_alive": 1749889822.687,
     "last_keep_alive_str": "2025-06-14 16:30:22",
     "keep_alive_count": 1247
   }
   ```

## 🔧 保活管理机制

### 自动检测机制

保活管理器每 60 秒检查一次所有设备：

1. **检查条件**：保活超时时间 > 61 秒
2. **触发动作**：如果设备当前为解锁状态，自动设置为锁定
3. **事件记录**：生成 `auto_locked_by_alive_timeout` 事件

### 管理器配置

```python
# 默认配置
check_interval = 60  # 检查间隔（秒）
alive_timeout = 61   # 保活超时阈值（秒）
```

### 手动管理接口

```bash
# 强制检查单个设备
curl -X POST "https://api.example.com/looking/alive-manager/check/HW_20b539c032526f01a171b35884404a23"

# 获取设备保活详情
curl "https://api.example.com/looking/alive-manager/device/HW_20b539c032526f01a171b35884404a23"
```

## 💻 客户端集成示例

### Android 客户端示例

```java
public class DeviceMonitor {
    private static final String BASE_URL = "https://api.example.com/looking";
    private String deviceId;
    
    // 发送锁屏事件
    public void sendLockEvent(String action) {
        long timestamp = System.currentTimeMillis();
        String signature = DeviceUtils.md5(deviceId, "lock_event", String.valueOf(timestamp));
        
        Map<String, String> headers = new HashMap<>();
        headers.put("X-Device-Id", deviceId);
        headers.put("X-Event-Type", "lock_event");
        headers.put("X-Timestamp", String.valueOf(timestamp));
        headers.put("X-Signature", signature);
        // ... 其他设备信息 headers
        
        JSONObject data = new JSONObject();
        data.put("event_type", "lock_event");
        data.put("timestamp", timestamp);
        data.put("date", new SimpleDateFormat("yyyy-MM-dd").format(new Date()));
        data.put("action", action);
        data.put("description", "设备" + action);
        
        // 发送 POST 请求到 /looking/device-event
        sendRequest(BASE_URL + "/device-event", headers, data);
    }
    
    // 发送保活心跳
    public void sendKeepAlive() {
        String signature = DeviceUtils.md5(deviceId, "keep_alive", String.valueOf(System.currentTimeMillis()));
        
        Map<String, String> headers = new HashMap<>();
        headers.put("X-Device-Id", deviceId);
        headers.put("X-Event-Type", "keep_alive");
        headers.put("X-Signature", signature);
        // ... 其他设备信息 headers
        
        JSONObject data = new JSONObject();
        data.put("status", "active");
        
        // 发送 POST 请求到 /looking/keep-alive
        sendRequest(BASE_URL + "/keep-alive", headers, data);
    }
    
    // 发送设备状态
    public void sendDeviceStatus() {
        long timestamp = System.currentTimeMillis();
        String signature = DeviceUtils.md5(deviceId, "device_status", String.valueOf(timestamp));
        
        Map<String, String> headers = new HashMap<>();
        headers.put("X-Device-Id", deviceId);
        headers.put("X-Event-Type", "device_status");
        headers.put("X-Signature", signature);
        // ... 其他设备信息 headers
        
        JSONObject statusData = collectDeviceStatus();
        statusData.put("timestamp", timestamp);
        statusData.put("device_id", deviceId);
        
        // 发送 POST 请求到 /looking/device-status
        sendRequest(BASE_URL + "/device-status", headers, statusData);
    }
}
```

### Python 客户端示例

```python
import hashlib
import time
import requests
from datetime import datetime

class DeviceMonitorClient:
    def __init__(self, base_url, device_id, device_info):
        self.base_url = base_url
        self.device_id = device_id
        self.device_info = device_info
    
    def _generate_signature(self, event_type, timestamp=None):
        """生成签名"""
        if timestamp is None:
            timestamp = str(int(time.time() * 1000))
        
        combined = f"{self.device_id}{event_type}{timestamp}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_headers(self, event_type, timestamp=None):
        """生成请求头"""
        if timestamp is None:
            timestamp = str(int(time.time() * 1000))
        
        return {
            "Content-Type": "application/json",
            "X-Device-Id": self.device_id,
            "X-Device-Model": self.device_info.get("model", "Unknown"),
            "X-Device-Brand": self.device_info.get("brand", "Unknown"),
            "X-Android-Version": self.device_info.get("android_version", "Unknown"),
            "X-SDK-Int": str(self.device_info.get("sdk_int", 0)),
            "X-Event-Type": event_type,
            "X-Timestamp": timestamp,
            "X-Signature": self._generate_signature(event_type, timestamp)
        }
    
    def send_lock_event(self, action, description=""):
        """发送锁屏事件"""
        timestamp = str(int(time.time() * 1000))
        headers = self._get_headers("lock_event", timestamp)
        
        data = {
            "event_type": "lock_event",
            "timestamp": int(timestamp),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "action": action,
            "description": description or f"设备{action}"
        }
        
        response = requests.post(
            f"{self.base_url}/device-event",
            headers=headers,
            json=data
        )
        return response.json()
    
    def send_keep_alive(self):
        """发送保活心跳"""
        headers = self._get_headers("keep_alive")
        # 移除保活请求不需要的时间戳头
        headers.pop("X-Timestamp", None)
        
        data = {"status": "active"}
        
        response = requests.post(
            f"{self.base_url}/keep-alive",
            headers=headers,
            json=data
        )
        return response.json()
    
    def get_device_summary(self):
        """获取设备摘要"""
        response = requests.get(f"{self.base_url}/device-summary/{self.device_id}")
        return response.json()

# 使用示例
client = DeviceMonitorClient(
    base_url="https://api.example.com/looking",
    device_id="TEST_DEVICE_001",
    device_info={
        "model": "Test Device",
        "brand": "TestBrand",
        "android_version": "11",
        "sdk_int": 30
    }
)

# 发送解锁事件
result = client.send_lock_event("unlocked", "用户解锁设备")
print(f"发送解锁事件: {result}")

# 发送保活
result = client.send_keep_alive()
print(f"发送保活: {result}")

# 获取设备摘要
summary = client.get_device_summary()
print(f"设备摘要: {summary}")
```