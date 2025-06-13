from datetime import datetime, date, timezone, timedelta
from loguru import logger as log
import hashlib
import time
from methods.globalvar import GlobalVars
from api.looking.Bases import DeviceStatus, DailyRecord, UsageSession, EventInfo

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now() -> datetime:
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

def get_beijing_date() -> date:
    """获取当前北京日期"""
    return get_beijing_now().date()

def format_beijing_time(timestamp_ms: int) -> str:
    """将时间戳转换为北京时间格式"""
    dt = datetime.fromtimestamp(timestamp_ms / 1000, BEIJING_TZ)
    return dt.strftime("%H:%M:%S")

def verify_signature(device_id: str, event_type: str, timestamp: str, signature: str) -> bool:
    """验证签名 - 实现与客户端相同的MD5签名逻辑"""
    try:
        expected_signature = hashlib.md5(f"{device_id}{event_type}{timestamp}".encode()).hexdigest()
        return expected_signature.lower() == signature.lower()
    except Exception as e:
        log.error(f"签名验证失败: {e}")
        return False

def get_device_table_name(device_id: str) -> str:
    """根据设备ID生成表名"""
    return f"device_{device_id}"

def get_daily_record_key(device_id: str, target_date: str = None) -> str:
    """生成每日记录的键名 - 使用北京时间"""
    if target_date is None:
        target_date = get_beijing_date().strftime("%Y%m%d")
    return f"daily_{target_date}"

def get_device_status_key(device_id: str) -> str:
    """生成设备状态的键名"""
    return "device_status"

def init_device_table(device_id: str) -> None:
    """初始化设备表和基础数据"""
    table_name = get_device_table_name(device_id)
    
    # 创建设备专用表
    if not GlobalVars.table_exists(table_name):
        GlobalVars.create_table(table_name)
        log.info(f"创建设备表: {table_name}")
    
    # 初始化设备状态
    status_key = get_device_status_key(device_id)
    current_status = GlobalVars.get_from_table(table_name, status_key)
    if current_status is None:
        beijing_now = get_beijing_now()
        default_status = {
            "is_locked": True,
            "last_unlock_time": None,
            "last_lock_time": beijing_now.timestamp() * 1000,
            "last_update": beijing_now.timestamp(),
            "last_event": "initialized",
            "created_time": beijing_now.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": "Asia/Shanghai"
        }
        GlobalVars.set_to_table(table_name, status_key, default_status)
        log.info(f"初始化设备状态: {device_id}")

def get_today_record(device_id: str) -> dict:
    """获取今日记录 - 基于北京时间"""
    table_name = get_device_table_name(device_id)
    record_key = get_daily_record_key(device_id)
    
    today_record = GlobalVars.get_from_table(table_name, record_key)
    if today_record is None:
        beijing_now = get_beijing_now()
        beijing_date = get_beijing_date()
        
        today_record = {
            "date": beijing_date.strftime("%Y-%m-%d"),
            "screen_on_time": 0,
            "lock_events": [],
            "unlock_events": [],
            "usage_sessions": [],
            "created_time": beijing_now.timestamp(),
            "created_time_str": beijing_now.strftime("%Y-%m-%d %H:%M:%S"),
            "last_update": beijing_now.timestamp(),
            "timezone": "Asia/Shanghai"
        }
        GlobalVars.set_to_table(table_name, record_key, today_record)
        log.info(f"创建今日记录: {device_id} - {today_record['date']} (北京时间)")
    
    return today_record

def create_event_info(timestamp: int, action: str) -> dict:
    """创建事件信息"""
    return {
        "timestamp": timestamp,
        "time": format_beijing_time(timestamp),
        "action": action,
        "beijing_time": datetime.fromtimestamp(timestamp / 1000, BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    }

def create_usage_session(unlock_time: int, lock_time: int) -> dict:
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

def update_device_status_and_record(device_id: str, action: str, timestamp: int) -> None:
    """更新设备状态并记录使用时间"""
    table_name = get_device_table_name(device_id)
    status_key = get_device_status_key(device_id)
    
    current_status = GlobalVars.get_from_table(table_name, status_key, {})
    today_record = get_today_record(device_id)
    beijing_now = get_beijing_now()
    
    event_info = create_event_info(timestamp, action)
    
    if is_lock_action(action):
        handle_lock_event(current_status, today_record, event_info, device_id)
    elif is_unlock_action(action):
        handle_unlock_event(current_status, today_record, event_info, device_id)
    else:
        log.warning(f"未识别的动作类型: {device_id} - 动作: {action}")
        return
    
    # 更新时间戳
    update_timestamps(current_status, today_record, action, beijing_now)
    
    # 保存更新
    save_device_data(table_name, status_key, current_status, device_id, today_record)

def handle_lock_event(current_status: dict, today_record: dict, event_info: dict, device_id: str) -> None:
    """处理锁屏事件"""
    if not current_status.get("is_locked", True):
        last_unlock_time = current_status.get("last_unlock_time")
        if last_unlock_time:
            session_info = create_usage_session(last_unlock_time, event_info["timestamp"])
            today_record["screen_on_time"] += session_info["duration"]
            today_record["usage_sessions"].append(session_info)
            
            log.info(f"记录使用会话: {device_id} - 使用时长: {session_info['duration']:.1f}秒 "
                    f"({session_info['unlock_time_str']} - {session_info['lock_time_str']})")
    
    current_status["is_locked"] = True
    current_status["last_lock_time"] = event_info["timestamp"]
    today_record["lock_events"].append(event_info)
    
    log.info(f"设备锁定: {device_id} - 动作: {event_info['action']}")

def handle_unlock_event(current_status: dict, today_record: dict, event_info: dict, device_id: str) -> None:
    """处理解锁事件"""
    current_status["is_locked"] = False
    current_status["last_unlock_time"] = event_info["timestamp"]
    today_record["unlock_events"].append(event_info)
    
    log.info(f"设备解锁: {device_id} - 动作: {event_info['action']}")

def update_timestamps(current_status: dict, today_record: dict, action: str, beijing_now: datetime) -> None:
    """更新时间戳"""
    current_status["last_update"] = beijing_now.timestamp()
    current_status["last_update_str"] = beijing_now.strftime("%Y-%m-%d %H:%M:%S")
    current_status["last_event"] = action
    current_status["timezone"] = "Asia/Shanghai"
    
    today_record["last_update"] = beijing_now.timestamp()
    today_record["last_update_str"] = beijing_now.strftime("%Y-%m-%d %H:%M:%S")

def save_device_data(table_name: str, status_key: str, current_status: dict, device_id: str, today_record: dict) -> None:
    """保存设备数据"""
    GlobalVars.set_to_table(table_name, status_key, current_status)
    record_key = get_daily_record_key(device_id)
    GlobalVars.set_to_table(table_name, record_key, today_record)
    
    log.info(f"更新设备状态: {device_id} - 锁定状态: {current_status.get('is_locked')} - "
            f"动作: {current_status['last_event']} (北京时间: {current_status['last_update_str']})")

def calculate_current_session_time(status: dict) -> float:
    """计算当前会话时间"""
    if not status.get("is_locked", True) and status.get("last_unlock_time"):
        current_time = get_beijing_now().timestamp() * 1000
        return (current_time - status["last_unlock_time"]) / 1000
    return 0

def format_screen_time(total_seconds: float) -> str:
    """格式化亮屏时间显示"""
    hours = total_seconds / 3600
    minutes = total_seconds / 60
    
    if hours >= 1:
        return f"{hours:.1f}小时"
    elif minutes >= 1:
        return f"{minutes:.1f}分钟"
    else:
        return f"{total_seconds:.1f}秒"

def get_device_summary(device_id: str) -> dict:
    """获取设备使用摘要 - 基于北京时间"""
    table_name = get_device_table_name(device_id)
    
    status = GlobalVars.get_from_table(table_name, get_device_status_key(device_id), {})
    today_record = get_today_record(device_id)
    
    current_session_time = calculate_current_session_time(status)
    total_screen_time = today_record['screen_on_time'] + current_session_time
    
    return {
        "device_id": device_id,
        "current_status": status,
        "current_session_time": f"{current_session_time:.1f}秒" if current_session_time > 0 else "0秒",
        "today_summary": {
            "date": today_record["date"],
            "beijing_date": get_beijing_date().strftime("%Y-%m-%d"),
            "total_screen_time": f"{total_screen_time:.1f}秒",
            "formatted_screen_time": format_screen_time(total_screen_time),
            "completed_screen_time": f"{today_record['screen_on_time']:.1f}秒",
            "lock_count": len(today_record["lock_events"]),
            "unlock_count": len(today_record["unlock_events"]),
            "usage_sessions": len(today_record["usage_sessions"]),
            "timezone": "Asia/Shanghai (北京时间)"
        }
    }

def update_keep_alive_status(device_id: str) -> None:
    """更新设备保活状态"""
    if device_id == 'Unknown':
        return
        
    table_name = get_device_table_name(device_id)
    if not GlobalVars.table_exists(table_name):
        return
        
    status_key = get_device_status_key(device_id)
    current_status = GlobalVars.get_from_table(table_name, status_key, {})
    beijing_now = get_beijing_now()
    
    current_status["last_keep_alive"] = beijing_now.timestamp()
    current_status["last_keep_alive_str"] = beijing_now.strftime("%Y-%m-%d %H:%M:%S")
    
    GlobalVars.set_to_table(table_name, status_key, current_status)
    log.info(f"更新设备保活时间: {device_id}")

def get_all_device_ids() -> list:
    """获取所有设备ID列表"""
    all_tables = GlobalVars.get_all_tables()
    device_tables = [table for table in all_tables if table.startswith("device_")]
    return [table.replace("device_", "") for table in device_tables]

def parse_storage_info(storage_part: str) -> dict:
    """解析存储信息部分"""
    storage_info = {}
    try:
        parts = storage_part.split(",")
        for part in parts:
            if "total:" in part:
                total_str = part.split("total:")[1].strip()
                storage_info["total_bytes"] = parse_size_to_bytes(total_str)
            elif "available:" in part:
                available_str = part.split("available:")[1].strip()
                storage_info["available_bytes"] = parse_size_to_bytes(available_str)
            elif "used:" in part:
                used_str = part.split("used:")[1].strip()
                storage_info["used_bytes"] = parse_size_to_bytes(used_str)
            elif "usage:" in part and "%" in part:
                usage_str = part.split("usage:")[1].replace("%", "").strip()
                storage_info["usage_percentage"] = float(usage_str)
    except Exception as e:
        log.warning(f"解析存储信息失败: {e}")
    
    return storage_info

def parse_size_to_bytes(size_str: str) -> int:
    """将大小字符串转换为字节数"""
    try:
        size_str = size_str.strip().upper()
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
    except:
        return 0

def store_device_status(device_id: str, status_data: dict) -> None:
    """存储设备状态数据"""
    try:
        table_name = get_device_table_name(device_id)
        beijing_now = get_beijing_now()
        
        # 创建设备状态记录键
        status_record_key = f"device_status_{beijing_now.strftime('%Y%m%d_%H%M%S')}"
        
        # 添加服务器处理时间
        status_data["server_processed_at"] = beijing_now.timestamp()
        status_data["server_processed_at_str"] = beijing_now.strftime("%Y-%m-%d %H:%M:%S")
        status_data["timezone"] = "Asia/Shanghai"
        
        # 存储详细状态数据
        GlobalVars.set_to_table(table_name, status_record_key, status_data)
        
        # 更新设备最新状态
        latest_status_key = "latest_device_status"
        GlobalVars.set_to_table(table_name, latest_status_key, status_data)
        
        log.info(f"存储设备状态数据: {device_id} - 记录键: {status_record_key}")
        
    except Exception as e:
        log.exception(f"存储设备状态失败: {e}")

def get_latest_device_status(device_id: str) -> dict:
    """获取设备最新状态"""
    try:
        table_name = get_device_table_name(device_id)
        latest_status = GlobalVars.get_from_table(table_name, "latest_device_status")
        return latest_status if latest_status else {}
    except Exception as e:
        log.exception(f"获取设备最新状态失败: {e}")
        return {}

def validate_device_status_data(status_data: dict) -> bool:
    """验证设备状态数据的完整性"""
    required_fields = ["timestamp", "device_id"]
    
    for field in required_fields:
        if field not in status_data:
            log.warning(f"设备状态数据缺少必要字段: {field}")
            return False
    
    return True

def format_device_status_summary(status_data: dict) -> dict:
    """格式化设备状态摘要"""
    try:
        summary = {
            "device_id": status_data.get("device_id"),
            "timestamp": status_data.get("timestamp"),
            "last_update": status_data.get("server_processed_at_str", "未知"),
            "network_type": None,
            "battery_level": None,
            "is_charging": None,
            "foreground_app": None,
            "uptime_formatted": None
        }
        
        # 网络信息
        if "network" in status_data and status_data["network"]:
            network = status_data["network"]
            summary["network_type"] = network.get("type", "unknown")
        
        # 电池信息
        if "battery" in status_data and status_data["battery"]:
            battery = status_data["battery"]
            summary["battery_level"] = battery.get("level_percentage")
            summary["is_charging"] = battery.get("is_charging")
        
        # 前台应用
        if "foreground_app" in status_data and status_data["foreground_app"]:
            foreground = status_data["foreground_app"]
            summary["foreground_app"] = foreground.get("package_name") or foreground.get("status")
        
        # 运行时间
        if "uptime" in status_data and status_data["uptime"]:
            uptime = status_data["uptime"]
            summary["uptime_formatted"] = uptime.get("formatted_string")
        
        return summary
        
    except Exception as e:
        log.exception(f"格式化设备状态摘要失败: {e}")
        return {"error": str(e)}

def parse_storage_part(storage_part: str) -> dict:
    """解析存储信息字符串部分 - 供Java客户端调用"""
    return parse_storage_info(storage_part)