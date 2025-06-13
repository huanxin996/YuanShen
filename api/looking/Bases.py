from pydantic import BaseModel
from typing import Optional

class DeviceEventBase(BaseModel):
    """设备事件基础模型"""
    event_type: str
    timestamp: int
    date: str
    action: str
    description: str

class KeepAliveData(BaseModel):
    """保活数据模型"""
    live: int

class DeviceStatus(BaseModel):
    """设备状态模型"""
    is_locked: bool
    last_unlock_time: Optional[int] = None
    last_lock_time: Optional[int] = None
    last_update: float
    last_update_str: str
    last_event: str
    timezone: str = "Asia/Shanghai"
    created_time: Optional[str] = None
    last_keep_alive: Optional[float] = None
    last_keep_alive_str: Optional[str] = None

class DailyRecord(BaseModel):
    """每日记录模型"""
    date: str
    screen_on_time: float = 0.0
    lock_events: list = []
    unlock_events: list = []
    usage_sessions: list = []
    created_time: float
    created_time_str: str
    last_update: float
    timezone: str = "Asia/Shanghai"

class UsageSession(BaseModel):
    """使用会话模型"""
    unlock_time: int
    lock_time: int
    duration: float
    unlock_time_str: str
    lock_time_str: str
    duration_str: str

class EventInfo(BaseModel):
    """事件信息模型"""
    timestamp: int
    time: str
    action: str
    beijing_time: str

class ApiResponse(BaseModel):
    """API响应基础模型"""
    returnCode: int
    msg: str
    data: Optional[dict] = None

class DeviceSummary(BaseModel):
    """设备摘要模型"""
    device_id: str
    current_status: dict
    current_session_time: str
    today_summary: dict


class UptimeData(BaseModel):
    """系统运行时间模型"""
    total_milliseconds: int
    days: int
    hours: int
    minutes: int
    seconds: int
    formatted_string: str

class WiFiDetails(BaseModel):
    """WiFi详细信息模型"""
    ssid: Optional[str] = None
    signal_strength_dbm: Optional[int] = None
    link_speed_mbps: Optional[int] = None

class NetworkData(BaseModel):
    """网络状态模型"""
    full_status: str
    type: str
    has_internet: bool
    is_validated: bool
    wifi_details: Optional[WiFiDetails] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

class CPUData(BaseModel):
    """CPU信息模型"""
    full_info: str
    cores: int
    architecture: str
    max_frequency_mhz: Optional[int] = None
    max_frequency_khz: Optional[int] = None

class ThermalZone(BaseModel):
    """温度区域模型"""
    zone_index: int
    celsius: float

class ThermalData(BaseModel):
    """温度信息模型"""
    full_info: str
    battery_celsius: Optional[float] = None
    thermal_zones: list[ThermalZone] = []

class StorageInfo(BaseModel):
    """存储信息模型"""
    total_bytes: Optional[int] = None
    available_bytes: Optional[int] = None
    used_bytes: Optional[int] = None
    usage_percentage: Optional[float] = None

class StorageData(BaseModel):
    """存储数据模型"""
    full_info: str
    internal: Optional[StorageInfo] = None
    external: Optional[StorageInfo] = None

class ForegroundAppData(BaseModel):
    """前台应用信息模型"""
    full_info: str
    package_name: Optional[str] = None
    app_display_name: Optional[str] = None
    process_id: Optional[int] = None
    last_used_timestamp: Optional[int] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

class BatteryData(BaseModel):
    """电池信息模型"""
    full_info: str
    level_percentage: int
    is_charging: bool
    status_string: Optional[str] = None
    power_source_string: Optional[str] = None
    health_string: Optional[str] = None
    temperature_celsius: Optional[float] = None
    voltage_mv: Optional[int] = None
    voltage_v: Optional[float] = None
    technology: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

class DeviceStatusData(BaseModel):
    """设备状态数据模型"""
    uptime: Optional[UptimeData] = None
    network: Optional[NetworkData] = None
    cpu: CPUData
    thermal: ThermalData
    storage: StorageData
    foreground_app: Optional[ForegroundAppData] = None
    battery: Optional[BatteryData] = None
    timestamp: int
    device_id: str