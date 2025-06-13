from datetime import datetime, date, timezone, timedelta
from loguru import logger as log
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import time
import re
from methods.globalvar import GlobalVars

# 常量定义
BEIJING_TZ = timezone(timedelta(hours=8))
DEVICE_TABLE_PREFIX = "device_"
DAILY_RECORD_PREFIX = "daily_"
DEVICE_STATUS_KEY = "device_status"
LATEST_STATUS_KEY = "latest_device_status"

# 时间相关工具函数
def get_beijing_now() -> datetime:
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

def get_beijing_date() -> date:
    """获取当前北京日期"""
    return get_beijing_now().date()

def format_beijing_time(timestamp_ms: int) -> str:
    """将时间戳转换为北京时间格式"""
    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000, BEIJING_TZ)
        return dt.strftime("%H:%M:%S")
    except (ValueError, OSError) as e:
        log.warning(f"时间戳格式化失败: {timestamp_ms}, 错误: {e}")
        return "00:00:00"

def get_beijing_datetime_str(timestamp: Optional[float] = None) -> str:
    """获取北京时间字符串"""
    if timestamp:
        dt = datetime.fromtimestamp(timestamp, BEIJING_TZ)
    else:
        dt = get_beijing_now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# 签名验证
def verify_signature(device_id: str, event_type: str, timestamp: str, signature: str) -> bool:
    """验证MD5签名"""
    try:
        if not all([device_id, event_type, timestamp, signature]):
            return False
        
        expected_signature = hashlib.md5(f"{device_id}{event_type}{timestamp}".encode()).hexdigest()
        return expected_signature.lower() == signature.lower()
    except Exception as e:
        log.error(f"签名验证异常: {e}")
        return False

# 数据库键名生成
def get_device_table_name(device_id: str) -> str:
    """根据设备ID生成表名"""
    return f"{DEVICE_TABLE_PREFIX}{device_id}"

def get_daily_record_key(device_id: str, target_date: Optional[str] = None) -> str:
    """生成每日记录的键名"""
    if target_date is None:
        target_date = get_beijing_date().strftime("%Y%m%d")
    return f"{DAILY_RECORD_PREFIX}{target_date}"

def get_device_status_key(device_id: str) -> str:
    """生成设备状态的键名"""
    return DEVICE_STATUS_KEY

# 设备表初始化
def init_device_table(device_id: str) -> None:
    """初始化设备表和基础数据"""
    if not device_id or device_id == 'Unknown':
        return
    
    table_name = get_device_table_name(device_id)
    
    # 创建设备专用表
    if not GlobalVars.table_exists(table_name):
        GlobalVars.create_table(table_name)
        log.info(f"创建设备表: {table_name}")
    
    # 初始化设备状态
    status_key = get_device_status_key(device_id)
    if not GlobalVars.get_from_table(table_name, status_key):
        _create_default_device_status(table_name, status_key, device_id)

def _create_default_device_status(table_name: str, status_key: str, device_id: str) -> None:
    """创建默认设备状态"""
    beijing_now = get_beijing_now()
    default_status = {
        "is_locked": True,
        "last_unlock_time": None,
        "last_lock_time": beijing_now.timestamp() * 1000,
        "last_update": beijing_now.timestamp(),
        "last_event": "initialized",
        "created_time": get_beijing_datetime_str(),
        "timezone": "Asia/Shanghai"
    }
    GlobalVars.set_to_table(table_name, status_key, default_status)
    log.info(f"初始化设备状态: {device_id}")

# 每日记录管理
def get_today_record(device_id: str) -> Dict[str, Any]:
    """获取今日记录"""
    table_name = get_device_table_name(device_id)
    record_key = get_daily_record_key(device_id)
    
    today_record = GlobalVars.get_from_table(table_name, record_key)
    if not today_record:
        today_record = _create_today_record(table_name, record_key, device_id)
    
    return today_record

def _create_today_record(table_name: str, record_key: str, device_id: str) -> Dict[str, Any]:
    """创建今日记录"""
    beijing_now = get_beijing_now()
    beijing_date = get_beijing_date()
    
    today_record = {
        "date": beijing_date.strftime("%Y-%m-%d"),
        "screen_on_time": 0.0,
        "lock_events": [],
        "unlock_events": [],
        "usage_sessions": [],
        "created_time": beijing_now.timestamp(),
        "created_time_str": get_beijing_datetime_str(),
        "last_update": beijing_now.timestamp(),
        "timezone": "Asia/Shanghai"
    }
    
    GlobalVars.set_to_table(table_name, record_key, today_record)
    log.info(f"创建今日记录: {device_id} - {today_record['date']} (北京时间)")
    return today_record

# 事件处理相关
def create_event_info(timestamp: int, action: str) -> Dict[str, Any]:
    """创建事件信息"""
    return {
        "timestamp": timestamp,
        "time": format_beijing_time(timestamp),
        "action": action,
        "beijing_time": datetime.fromtimestamp(timestamp / 1000, BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    }

def create_usage_session(unlock_time: int, lock_time: int) -> Dict[str, Any]:
    """创建使用会话信息"""
    duration = (lock_time - unlock_time) / 1000
    return {
        "unlock_time": unlock_time,
        "lock_time": lock_time,
        "duration": duration,
        "unlock_time_str": format_beijing_time(unlock_time),
        "lock_time_str": format_beijing_time(lock_time),
        "duration_str": f"{duration:.1f}秒"
    }

def is_lock_action(action: str) -> bool:
    """判断是否为锁定动作"""
    action_lower = action.lower()
    return "locked" in action_lower and "unlocked" not in action_lower

def is_unlock_action(action: str) -> bool:
    """判断是否为解锁动作"""
    action_lower = action.lower()
    return "unlocked" in action_lower or "authenticated" in action_lower

# 设备状态更新的核心逻辑
def update_device_status_and_record(device_id: str, action: str, timestamp: int) -> None:
    """更新设备状态并记录使用时间"""
    table_name = get_device_table_name(device_id)
    status_key = get_device_status_key(device_id)
    
    current_status = GlobalVars.get_from_table(table_name, status_key, {})
    today_record = get_today_record(device_id)
    beijing_now = get_beijing_now()
    
    event_info = create_event_info(timestamp, action)
    
    # 处理不同类型的事件
    if is_lock_action(action):
        _handle_lock_event(current_status, today_record, event_info, device_id)
    elif is_unlock_action(action):
        _handle_unlock_event(current_status, today_record, event_info, device_id)
    else:
        log.warning(f"未识别的动作类型: {device_id} - 动作: {action}")
        return
    
    # 更新时间戳和保存数据
    _update_timestamps(current_status, today_record, action, beijing_now)
    _save_device_data(table_name, status_key, current_status, device_id, today_record)

def _handle_lock_event(current_status: Dict, today_record: Dict, event_info: Dict, device_id: str) -> None:
    """处理锁屏事件"""
    # 如果之前是解锁状态，计算使用时长
    if not current_status.get("is_locked", True):
        last_unlock_time = current_status.get("last_unlock_time")
        if last_unlock_time:
            session_info = create_usage_session(last_unlock_time, event_info["timestamp"])
            today_record["screen_on_time"] += session_info["duration"]
            today_record["usage_sessions"].append(session_info)
            
            log.info(f"记录使用会话: {device_id} - 使用时长: {session_info['duration']:.1f}秒 "
                    f"({session_info['unlock_time_str']} - {session_info['lock_time_str']})")
    
    # 更新为锁定状态
    current_status["is_locked"] = True
    current_status["last_lock_time"] = event_info["timestamp"]
    today_record["lock_events"].append(event_info)
    
    log.info(f"设备锁定: {device_id} - 动作: {event_info['action']}")

def _handle_unlock_event(current_status: Dict, today_record: Dict, event_info: Dict, device_id: str) -> None:
    """处理解锁事件"""
    current_status["is_locked"] = False
    current_status["last_unlock_time"] = event_info["timestamp"]
    today_record["unlock_events"].append(event_info)
    
    log.info(f"设备解锁: {device_id} - 动作: {event_info['action']}")

def _update_timestamps(current_status: Dict, today_record: Dict, action: str, beijing_now: datetime) -> None:
    """更新时间戳"""
    timestamp_str = get_beijing_datetime_str()
    timestamp_float = beijing_now.timestamp()
    
    # 更新设备状态时间戳
    current_status.update({
        "last_update": timestamp_float,
        "last_update_str": timestamp_str,
        "last_event": action,
        "timezone": "Asia/Shanghai"
    })
    
    # 更新记录时间戳
    today_record.update({
        "last_update": timestamp_float,
        "last_update_str": timestamp_str
    })

def _save_device_data(table_name: str, status_key: str, current_status: Dict, device_id: str, today_record: Dict) -> None:
    """保存设备数据"""
    # 保存设备状态
    GlobalVars.set_to_table(table_name, status_key, current_status)
    
    # 保存今日记录
    record_key = get_daily_record_key(device_id)
    GlobalVars.set_to_table(table_name, record_key, today_record)
    
    log.info(f"更新设备状态: {device_id} - 锁定状态: {current_status.get('is_locked')} - "
            f"动作: {current_status['last_event']} (北京时间: {current_status['last_update_str']})")

# 设备摘要和统计
def calculate_current_session_time(status: Dict) -> float:
    """计算当前会话时间"""
    if not status.get("is_locked", True) and status.get("last_unlock_time"):
        current_time = get_beijing_now().timestamp() * 1000
        return (current_time - status["last_unlock_time"]) / 1000
    return 0.0

def format_screen_time(total_seconds: float) -> str:
    """格式化亮屏时间显示"""
    if total_seconds < 60:
        return f"{total_seconds:.1f}秒"
    elif total_seconds < 3600:
        return f"{total_seconds / 60:.1f}分钟"
    else:
        return f"{total_seconds / 3600:.1f}小时"

def get_device_summary(device_id: str) -> Dict[str, Any]:
    """获取设备使用摘要"""
    table_name = get_device_table_name(device_id)
    
    status = GlobalVars.get_from_table(table_name, get_device_status_key(device_id), {})
    today_record = get_today_record(device_id)
    
    current_session_time = calculate_current_session_time(status)
    total_screen_time = today_record.get('screen_on_time', 0) + current_session_time
    
    return {
        "device_id": device_id,
        "current_status": status,
        "current_session_time": f"{current_session_time:.1f}秒" if current_session_time > 0 else "0秒",
        "today_summary": {
            "date": today_record.get("date", ""),
            "beijing_date": get_beijing_date().strftime("%Y-%m-%d"),
            "total_screen_time": f"{total_screen_time:.1f}秒",
            "formatted_screen_time": format_screen_time(total_screen_time),
            "completed_screen_time": f"{today_record.get('screen_on_time', 0):.1f}秒",
            "lock_count": len(today_record.get("lock_events", [])),
            "unlock_count": len(today_record.get("unlock_events", [])),
            "usage_sessions": len(today_record.get("usage_sessions", [])),
            "timezone": "Asia/Shanghai (北京时间)"
        }
    }

# 保活状态管理
def update_keep_alive_status(device_id: str) -> None:
    """更新设备保活状态"""
    if not device_id or device_id == 'Unknown':
        return
        
    table_name = get_device_table_name(device_id)
    if not GlobalVars.table_exists(table_name):
        return
        
    status_key = get_device_status_key(device_id)
    current_status = GlobalVars.get_from_table(table_name, status_key, {})
    beijing_now = get_beijing_now()
    
    current_status.update({
        "last_keep_alive": beijing_now.timestamp(),
        "last_keep_alive_str": get_beijing_datetime_str()
    })
    
    GlobalVars.set_to_table(table_name, status_key, current_status)
    log.info(f"更新设备保活时间: {device_id}")

def get_all_device_ids() -> List[str]:
    """获取所有设备ID列表"""
    all_tables = GlobalVars.get_all_tables()
    device_tables = [table for table in all_tables if table.startswith(DEVICE_TABLE_PREFIX)]
    return [table.replace(DEVICE_TABLE_PREFIX, "") for table in device_tables]

# 设备状态相关
def store_device_status(device_id: str, status_data: Dict[str, Any]) -> None:
    """存储设备状态数据"""
    try:
        table_name = get_device_table_name(device_id)
        beijing_now = get_beijing_now()
        
        # 添加服务器处理时间
        status_data.update({
            "server_processed_at": beijing_now.timestamp(),
            "server_processed_at_str": get_beijing_datetime_str(),
            "timezone": "Asia/Shanghai"
        })
        
        # 创建带时间戳的状态记录键
        status_record_key = f"device_status_{beijing_now.strftime('%Y%m%d_%H%M%S')}"
        
        # 存储详细状态数据
        GlobalVars.set_to_table(table_name, status_record_key, status_data)
        
        # 更新最新状态
        GlobalVars.set_to_table(table_name, LATEST_STATUS_KEY, status_data)
        
        log.info(f"存储设备状态数据: {device_id} - 记录键: {status_record_key}")
        
    except Exception as e:
        log.exception(f"存储设备状态失败: {e}")

def get_latest_device_status(device_id: str) -> Dict[str, Any]:
    """获取设备最新状态"""
    try:
        table_name = get_device_table_name(device_id)
        return GlobalVars.get_from_table(table_name, LATEST_STATUS_KEY) or {}
    except Exception as e:
        log.exception(f"获取设备最新状态失败: {e}")
        return {}

def validate_device_status_data(status_data: Dict[str, Any]) -> bool:
    """验证设备状态数据完整性"""
    required_fields = ["timestamp", "device_id"]
    
    for field in required_fields:
        if field not in status_data:
            log.warning(f"设备状态数据缺少必要字段: {field}")
            return False
    
    return True

def format_device_status_summary(status_data: Dict[str, Any]) -> Dict[str, Any]:
    """格式化设备状态摘要"""
    try:
        summary = {
            "device_id": status_data.get("device_id"),
            "timestamp": status_data.get("timestamp"),
            "last_update": status_data.get("server_processed_at_str", "未知"),
            "network_type": _extract_network_type(status_data),
            "battery_level": _extract_battery_level(status_data),
            "is_charging": _extract_charging_status(status_data),
            "foreground_app": _extract_foreground_app(status_data),
            "uptime_formatted": _extract_uptime_formatted(status_data)
        }
        
        return summary
        
    except Exception as e:
        log.exception(f"格式化设备状态摘要失败: {e}")
        return {"error": str(e)}

def _extract_network_type(status_data: Dict) -> Optional[str]:
    """提取网络类型"""
    network = status_data.get("network")
    return network.get("type", "unknown") if network else None

def _extract_battery_level(status_data: Dict) -> Optional[int]:
    """提取电池电量"""
    battery = status_data.get("battery")
    return battery.get("level_percentage") if battery else None

def _extract_charging_status(status_data: Dict) -> Optional[bool]:
    """提取充电状态"""
    battery = status_data.get("battery")
    return battery.get("is_charging") if battery else None

def _extract_foreground_app(status_data: Dict) -> Optional[str]:
    """提取前台应用"""
    foreground = status_data.get("foreground_app")
    if foreground:
        return foreground.get("package_name") or foreground.get("status")
    return None

def _extract_uptime_formatted(status_data: Dict) -> Optional[str]:
    """提取格式化运行时间"""
    uptime = status_data.get("uptime")
    return uptime.get("formatted_string") if uptime else None

# 存储信息解析
def parse_storage_info(storage_part: str) -> Dict[str, Any]:
    """解析存储信息部分"""
    storage_info = {}
    try:
        parts = storage_part.split(",")
        for part in parts:
            part = part.strip()
            if "total:" in part:
                storage_info["total_bytes"] = _parse_size_to_bytes(part.split("total:")[1].strip())
            elif "available:" in part:
                storage_info["available_bytes"] = _parse_size_to_bytes(part.split("available:")[1].strip())
            elif "used:" in part:
                storage_info["used_bytes"] = _parse_size_to_bytes(part.split("used:")[1].strip())
            elif "usage:" in part and "%" in part:
                usage_str = part.split("usage:")[1].replace("%", "").strip()
                storage_info["usage_percentage"] = float(usage_str)
    except Exception as e:
        log.warning(f"解析存储信息失败: {e}")
    
    return storage_info

def _parse_size_to_bytes(size_str: str) -> int:
    """将大小字符串转换为字节数"""
    try:
        size_str = size_str.strip().upper()
        
        # 移除所有空格和特殊字符，只保留数字和单位
        size_str = re.sub(r'[^\d.KMGTB]', '', size_str)
        
        if "GB" in size_str:
            return int(float(size_str.replace("GB", "")) * 1024 * 1024 * 1024)
        elif "MB" in size_str:
            return int(float(size_str.replace("MB", "")) * 1024 * 1024)
        elif "KB" in size_str:
            return int(float(size_str.replace("KB", "")) * 1024)
        elif "B" in size_str:
            return int(size_str.replace("B", ""))
        else:
            return int(float(size_str))
    except (ValueError, TypeError) as e:
        log.warning(f"大小字符串转换失败: {size_str}, 错误: {e}")
        return 0

# 向后兼容的别名
parse_storage_part = parse_storage_info