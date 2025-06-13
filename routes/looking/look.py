from typing import Optional
from loguru import logger as log
from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse
import time

from methods.globalvar import GlobalVars
from api.looking.Bases import DeviceEventBase, KeepAliveData, DeviceStatusData
from api.looking.utils import (
    get_beijing_now, verify_signature, init_device_table,
    update_device_status_and_record, get_device_summary,
    update_keep_alive_status, get_all_device_ids,
    get_device_table_name, store_device_status,
    get_latest_device_status, validate_device_status_data,
    format_device_status_summary, parse_storage_info
)

router = APIRouter(prefix="/looking", tags=["device_monitor"])

async def validate_device_status_headers(request: Request) -> dict:
    """验证并提取设备状态请求的header信息"""
    headers = {}
    required_headers = [
        "x-device-id", "x-device-model", "x-device-brand", 
        "x-android-version", "x-sdk-int", "x-event-type"
    ]
    
    for header in required_headers:
        value = request.headers.get(header)
        if value:
            headers[header] = value
        else:
            log.warning(f"设备状态请求缺少必要的header: {header}")
    
    return validate_device_status_signature(request, headers)

def validate_device_status_signature(request: Request, headers: dict) -> dict:
    """验证设备状态请求签名"""
    signature = request.headers.get("x-signature")
    if not signature:
        log.warning("设备状态请求未提供签名")
        headers["signature_verified"] = "false"
        return headers
    
    headers["x-signature"] = signature
    device_id = request.headers.get("x-device-id")
    event_type = request.headers.get("x-event-type")
    
    if not all([device_id, event_type]):
        log.warning("设备状态请求签名验证所需的header字段不完整")
        headers["signature_verified"] = "false"
        return headers
    
    current_timestamp = str(int(time.time() * 1000))
    
    if verify_signature(device_id, event_type, current_timestamp, signature):
        headers["signature_verified"] = "true"
    else:
        log.warning(f"设备状态请求签名验证失败: {signature}")
        headers["signature_verified"] = "false"
    
    return headers

async def validate_headers(request: Request) -> dict:
    """验证并提取header信息"""
    headers = {}
    required_headers = [
        "x-device-id", "x-device-model", "x-device-brand", 
        "x-android-version", "x-sdk-int", "x-app-version",
        "x-event-type", "x-timestamp"
    ]
    
    for header in required_headers:
        value = request.headers.get(header)
        if value:
            headers[header] = value
        else:
            log.warning(f"缺少必要的header: {header}")
    
    return validate_signature_in_headers(request, headers)

def validate_signature_in_headers(request: Request, headers: dict) -> dict:
    """验证请求中的签名"""
    signature = request.headers.get("x-signature")
    if not signature:
        log.warning("未提供签名")
        headers["signature_verified"] = "false"
        return headers
    
    headers["x-signature"] = signature
    device_id = request.headers.get("x-device-id")
    event_type = request.headers.get("x-event-type")
    timestamp = request.headers.get("x-timestamp")
    
    if not all([device_id, event_type, timestamp]):
        log.warning("签名验证所需的header字段不完整")
        headers["signature_verified"] = "false"
        return headers
    
    if verify_signature(device_id, event_type, timestamp, signature):
        headers["signature_verified"] = "true"
    else:
        log.warning(f"签名验证失败: {signature}")
        headers["signature_verified"] = "false"
    
    return headers

async def validate_keep_alive_headers(request: Request) -> dict:
    """验证并提取保活请求的header信息"""
    headers = {}
    required_headers = [
        "x-device-id", "x-device-model", "x-device-brand", 
        "x-android-version", "x-sdk-int", "x-event-type"
    ]
    
    for header in required_headers:
        value = request.headers.get(header)
        if value:
            headers[header] = value
        else:
            log.warning(f"保活请求缺少必要的header: {header}")
    
    return validate_keep_alive_signature(request, headers)

def validate_keep_alive_signature(request: Request, headers: dict) -> dict:
    """验证保活请求签名"""
    signature = request.headers.get("x-signature")
    if not signature:
        log.warning("保活请求未提供签名")
        headers["signature_verified"] = "false"
        return headers
    
    headers["x-signature"] = signature
    device_id = request.headers.get("x-device-id")
    event_type = request.headers.get("x-event-type")
    
    if not all([device_id, event_type]):
        log.warning("保活请求签名验证所需的header字段不完整")
        headers["signature_verified"] = "false"
        return headers
    
    current_timestamp = str(int(time.time() * 1000))
    
    if verify_signature(device_id, event_type, current_timestamp, signature):
        headers["signature_verified"] = "true"
    else:
        log.warning(f"保活请求签名验证失败: {signature}")
        headers["signature_verified"] = "false"
    
    return headers

async def process_device_status(status_data: dict, headers: dict) -> JSONResponse:
    """处理设备状态数据"""
    try:
        device_id = headers.get('x-device-id', 'Unknown')
        beijing_now = get_beijing_now()
        
        log.info(f"收到设备状态请求 - 设备ID: {device_id}, 时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 验证数据完整性
        if not validate_device_status_data(status_data):
            return JSONResponse(
                status_code=400,
                content={"returnCode": 100, "msg": "设备状态数据不完整"}
            )
        
        # 确保设备表存在
        if device_id != 'Unknown':
            init_device_table(device_id)
            
            # 存储设备状态数据
            store_device_status(device_id, status_data)
            
            # 生成状态摘要
            summary = format_device_status_summary(status_data)
            log.info(f"设备状态摘要: {summary}")
        
        # 记录设备信息
        log_device_info(headers)

        return JSONResponse(
            status_code=200,
            content={
                "returnCode": 1,
                "msg": "设备状态处理成功",
                "data": {
                    "device_id": device_id,
                    "processed_at": beijing_now.strftime("%Y-%m-%d %H:%M:%S"),
                    "processed_at_timezone": "Asia/Shanghai",
                    "signature_verified": headers.get('signature_verified') == 'true',
                    "status_summary": summary if device_id != 'Unknown' else None
                }
            }
        )
        
    except Exception as e:
        log.exception(f"处理设备状态失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"returnCode": 101, "msg": f"处理设备状态失败: {str(e)}"}
        )

async def process_device_event(event_data: DeviceEventBase, headers: dict) -> JSONResponse:
    """处理设备事件数据 - 使用北京时间"""
    try:
        device_id = headers.get('x-device-id', 'Unknown')
        beijing_now = get_beijing_now()
        
        if device_id != 'Unknown':
            init_device_table(device_id)
        
        if event_data.event_type != "lock_event":
            log.warning(f"未知事件类型: {event_data.event_type}")
            return JSONResponse(
                status_code=400, 
                content={"returnCode": 100, "msg": f"未知事件类型: {event_data.event_type}"}
            )
        
        if device_id != 'Unknown':
            update_device_status_and_record(device_id, event_data.action, event_data.timestamp)
        
        summary = None
        if device_id != 'Unknown':
            summary = get_device_summary(device_id)
            log.info(f"设备摘要: {summary['today_summary']}")
        
        log_device_info(headers)
        
        return JSONResponse(
            status_code=200,
            content={
                "returnCode": 1, 
                "msg": "设备事件处理成功",
                "data": {
                    "event_type": event_data.event_type,
                    "processed_at": beijing_now.strftime("%Y-%m-%d %H:%M:%S"),
                    "processed_at_timezone": "Asia/Shanghai",
                    "timestamp": event_data.timestamp,
                    "device_id": device_id,
                    "signature_verified": headers.get('signature_verified') == 'true',
                    "action": event_data.action,
                    "description": event_data.description,
                    "summary": summary
                }
            }
        )
        
    except Exception as e:
        log.exception(f"处理设备事件失败: {e}")
        return JSONResponse(
            status_code=500, 
            content={"returnCode": 101, "msg": f"处理设备事件失败: {str(e)}"}
        )

def log_device_info(headers: dict) -> None:
    """记录设备信息"""
    log.info(f"设备信息 - 型号: {headers.get('x-device-model', 'Unknown')}, "
            f"品牌: {headers.get('x-device-brand', 'Unknown')}, "
            f"Android版本: {headers.get('x-android-version', 'Unknown')}, "
            f"SDK版本: {headers.get('x-sdk-int', 'Unknown')}, "
            f"应用版本: {headers.get('x-app-version', 'Unknown')}")

async def process_keep_alive(headers: dict) -> JSONResponse:
    """处理保活请求"""
    try:
        device_id = headers.get('x-device-id', 'Unknown')
        beijing_now = get_beijing_now()
        
        log.info(f"收到保活请求 - 设备ID: {device_id}, 时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        update_keep_alive_status(device_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "returnCode": 1,
                "msg": "保活请求处理成功",
                "data": {
                    "device_id": device_id,
                    "server_time": beijing_now.strftime("%Y-%m-%d %H:%M:%S"),
                    "timezone": "Asia/Shanghai",
                    "signature_verified": headers.get('signature_verified') == 'true'
                }
            }
        )
        
    except Exception as e:
        log.exception(f"处理保活请求失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"returnCode": 101, "msg": f"处理保活请求失败: {str(e)}"}
        )

@router.post("/device-event")
async def receive_device_event(
    request: Request,
    event: DeviceEventBase,
    content_type: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
    x_device_id: Optional[str] = Header(None),
    x_event_type: Optional[str] = Header(None),
    x_timestamp: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None)
):
    """
    接收设备锁屏事件
    
    支持的事件类型：
    - lock_event: 锁屏/解锁事件
    
    自动记录功能（基于北京时间）：
    - 每个设备ID创建独立的数据表
    - 基于锁屏/解锁事件计算亮屏时间
    - 记录使用会话（解锁到锁屏的时间段）
    - 维护设备当前状态（是否锁定）
    - 按北京时间日期自动切换记录
    """
    
    if content_type and "application/json" not in content_type:
        return JSONResponse(
            status_code=400,
            content={"returnCode": 100, "msg": "Content-Type必须为application/json"}
        )
    
    headers = await validate_headers(request)
    
    if x_event_type and x_event_type != event.event_type:
        log.warning(f"Header中的事件类型({x_event_type})与Body中的事件类型({event.event_type})不一致")
    
    if x_timestamp and int(x_timestamp) != event.timestamp:
        log.warning(f"Header中的时间戳({x_timestamp})与Body中的时间戳({event.timestamp})不一致")
    
    return await process_device_event(event, headers)

@router.post("/keep-alive")
async def receive_keep_alive(
    request: Request,
    keep_alive_data: KeepAliveData,
    content_type: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
    x_device_id: Optional[str] = Header(None),
    x_event_type: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None)
):
    """
    接收设备保活请求
    
    功能：
    - 记录设备最后活跃时间
    - 验证设备签名
    - 返回服务器时间
    """
    
    if content_type and "application/json" not in content_type:
        return JSONResponse(
            status_code=400,
            content={"returnCode": 100, "msg": "Content-Type必须为application/json"}
        )
    
    if x_event_type != "keep_alive":
        return JSONResponse(
            status_code=400,
            content={"returnCode": 100, "msg": "保活请求事件类型必须为keep_alive"}
        )
    
    headers = await validate_keep_alive_headers(request)
    
    log.info(f"保活请求设备信息 - 型号: {headers.get('x-device-model', 'Unknown')}, "
            f"品牌: {headers.get('x-device-brand', 'Unknown')}, "
            f"Android版本: {headers.get('x-android-version', 'Unknown')}, "
            f"SDK版本: {headers.get('x-sdk-int', 'Unknown')}")
    
    return await process_keep_alive(headers)

@router.get("/device-summary/{device_id}")
async def get_device_usage_summary(device_id: str):
    """获取指定设备的使用摘要（基于北京时间）"""
    try:
        if not GlobalVars.table_exists(get_device_table_name(device_id)):
            return JSONResponse(
                status_code=404,
                content={"returnCode": 100, "msg": f"设备 {device_id} 未找到记录"}
            )
        
        summary = get_device_summary(device_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "returnCode": 1,
                "msg": "获取设备摘要成功",
                "data": summary,
                "current_beijing_time": get_beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": "Asia/Shanghai"
            }
        )
        
    except Exception as e:
        log.exception(f"获取设备摘要失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"returnCode": 101, "msg": f"获取设备摘要失败: {str(e)}"}
        )

@router.get("/device-list")
async def get_device_list():
    """获取所有设备列表"""
    try:
        device_ids = get_all_device_ids()
        if not device_ids:
            return JSONResponse(
                status_code=404,
                content={"returnCode": 100, "msg": "没有找到任何设备记录"}
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "returnCode": 1,
                "msg": "获取设备列表成功,请使用设备ID查询设备摘要，例如 /looking/device-summary/{device_id}",
                "data": {
                    "device_count": len(device_ids),
                    "device_list": device_ids,
                    "current_beijing_time": get_beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
                    "timezone": "Asia/Shanghai"
                }
            }
        )
        
    except Exception as e:
        log.exception(f"获取设备列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"returnCode": 101, "msg": f"获取设备列表失败: {str(e)}"}
        )

@router.post("/device-status")
async def receive_device_status(
    request: Request,
    content_type: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
    x_device_id: Optional[str] = Header(None),
    x_event_type: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None)
):
    """
    接收设备状态信息
    
    功能：
    - 记录详细的设备状态信息
    - 包括系统运行时间、网络状态、CPU信息、温度、存储、
     - 验证设备签名
    - 存储状态历史记录
    """
    
    # 验证Content-Type
    if content_type and "application/json" not in content_type:
        return JSONResponse(
            status_code=400,
            content={"returnCode": 100, "msg": "Content-Type必须为application/json"}
        )
    
    # 验证事件类型
    if x_event_type != "device_status":
        return JSONResponse(
            status_code=400,
            content={"returnCode": 100, "msg": "设备状态请求事件类型必须为device_status"}
        )
    
    # 获取请求体数据
    try:
        request_body = await request.json()
    except Exception as e:
        log.error(f"解析请求体失败: {e}")
        return JSONResponse(
            status_code=400,
            content={"returnCode": 100, "msg": "请求体JSON格式错误"}
        )
    
    # 提取并验证headers
    headers = await validate_device_status_headers(request)
    
    # 记录设备状态信息
    log.info(f"设备状态请求设备信息 - 型号: {headers.get('x-device-model', 'Unknown')}, "
            f"品牌: {headers.get('x-device-brand', 'Unknown')}, "
            f"Android版本: {headers.get('x-android-version', 'Unknown')}, "
            f"SDK版本: {headers.get('x-sdk-int', 'Unknown')}")
    
    return await process_device_status(request_body, headers)

@router.get("/device-status/{device_id}")
async def get_device_status(device_id: str):
    """获取指定设备的最新状态信息"""
    try:
        if not GlobalVars.table_exists(get_device_table_name(device_id)):
            return JSONResponse(
                status_code=404,
                content={"returnCode": 100, "msg": f"设备 {device_id} 未找到记录"}
            )
        
        latest_status = get_latest_device_status(device_id)
        if not latest_status:
            return JSONResponse(
                status_code=404,
                content={"returnCode": 100, "msg": f"设备 {device_id} 未找到状态记录"}
            )
        # 格式化状态摘要
        summary = format_device_status_summary(latest_status)
        
        return JSONResponse(
            status_code=200,
            content={
                "returnCode": 1,
                "msg": "获取设备状态成功",
                "data": {
                    "device_id": device_id,
                    "latest_status": latest_status,
                    "status_summary": summary,
                    "current_beijing_time": get_beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
                    "timezone": "Asia/Shanghai"
                }
            }
        )
        
    except Exception as e:
        log.exception(f"获取设备状态失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"returnCode": 101, "msg": f"获取设备状态失败: {str(e)}"}
        )

def register_routes(app):
    log.info(f"注册looking路由，前缀：{router.prefix} (基于锁屏事件计算亮屏时间，使用北京时间)")
    app.include_router(router)