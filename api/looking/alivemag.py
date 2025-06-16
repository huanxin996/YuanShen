import asyncio
import time
from datetime import datetime
from loguru import logger as log
from typing import Dict, List, Optional, Set
from threading import Thread, Lock

from api.looking.utils import (
    get_beijing_now, get_all_device_ids, get_device_table_name,
    get_device_status_key, update_device_status_and_record,
    get_device_summary, BEIJING_TZ
)
from methods.globalvar import GlobalVars

class AliveManager:
    """保活连接管理器"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 60  # 检查间隔：60秒（1分钟）
        self.alive_timeout = 301   # 保活超时：61秒
        self.worker_thread: Optional[Thread] = None
        self.alive_devices: Set[str] = set()  # 活跃设备集合
        self.lock = Lock()  # 线程锁
        
        log.info("保活管理器初始化完成")
    
    def start(self) -> None:
        """启动保活检查服务"""
        if self.is_running:
            log.warning("保活管理器已经在运行中")
            return
        
        self.is_running = True
        self.worker_thread = Thread(target=self._run_check_loop, daemon=True)
        self.worker_thread.start()
        log.info(f"保活管理器启动成功 - 检查间隔: {self.check_interval}秒, 超时阈值: {self.alive_timeout}秒")
    
    def stop(self) -> None:
        """停止保活检查服务"""
        if not self.is_running:
            log.warning("保活管理器未在运行")
            return
        
        self.is_running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        log.info("保活管理器已停止")
    
    def register_alive_device(self, device_id: str) -> None:
        """注册活跃设备"""
        if not device_id or device_id == 'Unknown':
            return
        
        with self.lock:
            self.alive_devices.add(device_id)
        log.debug(f"注册活跃设备: {device_id}")
    
    def _run_check_loop(self) -> None:
        """运行检查循环"""
        log.info("保活检查循环开始运行")
        
        while self.is_running:
            try:
                self._perform_alive_check()
                
                # 等待下一次检查，支持提前退出
                for _ in range(self.check_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                log.exception(f"保活检查循环异常: {e}")
                time.sleep(5)  # 异常时短暂等待后继续
        
        log.info("保活检查循环结束")
    
    def _perform_alive_check(self) -> None:
        """执行保活检查"""
        current_time = get_beijing_now()
        current_timestamp = current_time.timestamp()
        
        log.debug(f"开始执行保活检查 - 当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取所有设备ID
        all_device_ids = get_all_device_ids()
        if not all_device_ids:
            log.debug("未找到任何设备记录")
            return
        
        checked_devices = 0
        timeout_devices = 0
        auto_locked_devices = 0
        
        for device_id in all_device_ids:
            try:
                result = self._check_single_device(device_id, current_timestamp)
                checked_devices += 1
                
                if result['is_timeout']:
                    timeout_devices += 1
                if result['auto_locked']:
                    auto_locked_devices += 1
                    
            except Exception as e:
                log.error(f"检查设备 {device_id} 时发生异常: {e}")
        
        # 记录检查结果摘要
        if timeout_devices > 0 or auto_locked_devices > 0:
            log.info(f"保活检查完成 - 总检查: {checked_devices}, "
                    f"超时设备: {timeout_devices}, 自动锁定: {auto_locked_devices}")
        else:
            log.debug(f"保活检查完成 - 总检查: {checked_devices}, 所有设备状态正常")
    
    def _check_single_device(self, device_id: str, current_timestamp: float) -> Dict[str, bool]:
        """检查单个设备的保活状态"""
        result = {
            'is_timeout': False,
            'auto_locked': False
        }
        
        try:
            # 获取设备状态
            table_name = get_device_table_name(device_id)
            if not GlobalVars.table_exists(table_name):
                return result
            
            status_key = get_device_status_key(device_id)
            device_status = GlobalVars.get_from_table(table_name, status_key)
            
            if not device_status:
                return result
            
            # 检查保活时间
            last_keep_alive = device_status.get('last_keep_alive')
            if not last_keep_alive:
                log.debug(f"设备 {device_id} 无保活记录")
                return result
            
            # 计算保活超时
            time_since_alive = current_timestamp - last_keep_alive
            
            if time_since_alive > self.alive_timeout:
                result['is_timeout'] = True
                log.debug(f"设备 {device_id} 保活超时: {time_since_alive:.1f}秒 > {self.alive_timeout}秒")
                
                # 检查当前是否为解锁状态
                is_locked = device_status.get('is_locked', True)
                if not is_locked:
                    # 设备当前为解锁状态且保活超时，自动锁定
                    self._auto_lock_device(device_id, current_timestamp, time_since_alive)
                    result['auto_locked'] = True
                else:
                    log.debug(f"设备 {device_id} 已为锁定状态，跳过自动锁定")
            else:
                log.debug(f"设备 {device_id} 保活正常: 距离上次保活 {time_since_alive:.1f}秒")
        
        except Exception as e:
            log.error(f"检查设备 {device_id} 状态时异常: {e}")
        
        return result
    
    def _auto_lock_device(self, device_id: str, current_timestamp: float, timeout_duration: float) -> None:
        """自动锁定设备"""
        try:
            # 生成自动锁定事件的时间戳（毫秒）
            lock_timestamp = int(current_timestamp * 1000)
            
            # 更新设备状态为锁定
            update_device_status_and_record(
                device_id=device_id,
                action="auto_locked_by_alive_timeout",
                timestamp=lock_timestamp
            )
            
            # 从活跃设备列表中移除
            with self.lock:
                self.alive_devices.discard(device_id)
            
            # 获取设备摘要用于日志
            summary = get_device_summary(device_id)
            current_session = summary.get('current_session_time', '0秒')
            
            log.warning(f"自动锁定设备: {device_id} - 保活超时 {timeout_duration:.1f}秒 > {self.alive_timeout}秒, "
                       f"当前会话时间: {current_session}")
            
        except Exception as e:
            log.error(f"自动锁定设备 {device_id} 时发生异常: {e}")
    
    def get_status(self) -> Dict[str, any]:
        """获取保活管理器状态"""
        with self.lock:
            alive_count = len(self.alive_devices)
            alive_list = list(self.alive_devices.copy())
        
        return {
            "is_running": self.is_running,
            "check_interval_seconds": self.check_interval,
            "alive_timeout_seconds": self.alive_timeout,
            "alive_devices_count": alive_count,
            "alive_devices": alive_list,
            "current_beijing_time": get_beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": "Asia/Shanghai"
        }
    
    def set_check_interval(self, interval_seconds: int) -> bool:
        """设置检查间隔"""
        if interval_seconds < 10:
            log.warning(f"检查间隔不能小于10秒，当前设置: {interval_seconds}秒")
            return False
        
        self.check_interval = interval_seconds
        log.info(f"检查间隔已更新为: {interval_seconds}秒")
        return True
    
    def set_alive_timeout(self, timeout_seconds: int) -> bool:
        """设置保活超时时间"""
        if timeout_seconds < 30:
            log.warning(f"保活超时时间不能小于30秒，当前设置: {timeout_seconds}秒")
            return False
        
        self.alive_timeout = timeout_seconds
        log.info(f"保活超时时间已更新为: {timeout_seconds}秒")
        return True
    
    def force_check_device(self, device_id: str) -> Dict[str, any]:
        """强制检查指定设备"""
        if not device_id or device_id == 'Unknown':
            return {"error": "无效的设备ID"}
        
        current_timestamp = get_beijing_now().timestamp()
        
        try:
            result = self._check_single_device(device_id, current_timestamp)
            summary = get_device_summary(device_id)
            
            return {
                "device_id": device_id,
                "check_time": get_beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_timeout": result['is_timeout'],
                "auto_locked": result['auto_locked'],
                "device_summary": summary,
                "timezone": "Asia/Shanghai"
            }
        except Exception as e:
            log.error(f"强制检查设备 {device_id} 时异常: {e}")
            return {"error": str(e)}
    
    def get_device_alive_info(self, device_id: str) -> Dict[str, any]:
        """获取设备保活信息"""
        try:
            table_name = get_device_table_name(device_id)
            if not GlobalVars.table_exists(table_name):
                return {"error": f"设备 {device_id} 未找到记录"}
            
            status_key = get_device_status_key(device_id)
            device_status = GlobalVars.get_from_table(table_name, status_key)
            
            if not device_status:
                return {"error": f"设备 {device_id} 状态记录不存在"}
            
            current_time = get_beijing_now()
            current_timestamp = current_time.timestamp()
            
            last_keep_alive = device_status.get('last_keep_alive')
            last_keep_alive_str = device_status.get('last_keep_alive_str', '未知')
            
            if last_keep_alive:
                time_since_alive = current_timestamp - last_keep_alive
                is_timeout = time_since_alive > self.alive_timeout
                last_alive_time = datetime.fromtimestamp(last_keep_alive, BEIJING_TZ)
            else:
                time_since_alive = None
                is_timeout = True
                last_alive_time = None
            
            with self.lock:
                is_registered = device_id in self.alive_devices
            
            return {
                "device_id": device_id,
                "is_registered": is_registered,
                "last_keep_alive_timestamp": last_keep_alive,
                "last_keep_alive_str": last_keep_alive_str,
                "last_alive_time": last_alive_time.strftime("%Y-%m-%d %H:%M:%S") if last_alive_time else None,
                "time_since_alive_seconds": round(time_since_alive, 2) if time_since_alive is not None else None,
                "is_timeout": is_timeout,
                "timeout_threshold_seconds": self.alive_timeout,
                "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "is_locked": device_status.get('is_locked', True),
                "timezone": "Asia/Shanghai"
            }
            
        except Exception as e:
            log.error(f"获取设备 {device_id} 保活信息时异常: {e}")
            return {"error": str(e)}

# 全局保活管理器实例
alive_manager = AliveManager()

def start_alive_manager() -> None:
    """启动保活管理器"""
    alive_manager.start()

def stop_alive_manager() -> None:
    """停止保活管理器"""
    alive_manager.stop()

def register_device_alive(device_id: str) -> None:
    """注册设备保活"""
    alive_manager.register_alive_device(device_id)

def get_alive_manager_status() -> Dict[str, any]:
    """获取保活管理器状态"""
    return alive_manager.get_status()

def force_check_device_alive(device_id: str) -> Dict[str, any]:
    """强制检查设备保活状态"""
    return alive_manager.force_check_device(device_id)

def get_device_alive_info(device_id: str) -> Dict[str, any]:
    """获取设备保活详细信息"""
    return alive_manager.get_device_alive_info(device_id)

def configure_alive_manager(check_interval: Optional[int] = None, alive_timeout: Optional[int] = None) -> Dict[str, bool]:
    """配置保活管理器参数"""
    results = {}
    
    if check_interval is not None:
        results['interval_updated'] = alive_manager.set_check_interval(check_interval)
    
    if alive_timeout is not None:
        results['timeout_updated'] = alive_manager.set_alive_timeout(alive_timeout)
    
    return results

# 应用启动时自动启动保活管理器
def init_alive_manager() -> None:
    """初始化保活管理器"""
    try:
        start_alive_manager()
        log.info("保活管理器自动启动完成")
    except Exception as e:
        log.error(f"保活管理器启动失败: {e}")