from pydantic import BaseModel, Field
from typing import Optional, List, Union

class DeviceEventBase(BaseModel):
    """设备事件基础模型"""
    event_type: str = Field(..., description="事件类型")
    timestamp: int = Field(..., description="时间戳(毫秒)")
    date: str = Field(..., description="日期")
    action: str = Field(..., description="动作")
    description: str = Field(..., description="描述")

class KeepAliveData(BaseModel):
    """保活数据模型"""
    live: int = Field(default=0, description="保活标识")

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
    thermal_zones: List[ThermalZone] = Field(default_factory=list)

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
    cpu: Optional[CPUData] = None
    thermal: Optional[ThermalData] = None
    storage: Optional[StorageData] = None
    foreground_app: Optional[ForegroundAppData] = None
    battery: Optional[BatteryData] = None
    timestamp: int
    device_id: str

class ApiResponse(BaseModel):
    """API响应统一模型"""
    returnCode: int = Field(..., description="返回码: 1=成功, 100=客户端错误, 101=服务器错误")
    msg: str = Field(..., description="返回消息")
    data: Optional[dict] = Field(None, description="返回数据")

class HeaderValidationResult(BaseModel):
    """Header验证结果模型"""
    headers: dict
    is_valid: bool
    error_message: Optional[str] = None