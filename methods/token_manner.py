import time
import hashlib
import secrets
from typing import Dict, Optional, Set, Tuple, Any
from loguru import logger as log
from methods.globalvar import GlobalVars
from config import api_default_token, api_default_token_expire,log_level

class TokenManager:
    """API Token 管理器"""
    
    def __init__(self):
        self.enabled_apis: Set[str] = set()
        self.api_tokens: Dict[str, str] = {}
        self.api_token_expires: Dict[str, int] = {}
        self.default_token = api_default_token
        self.default_expire = api_default_token_expire
        
        # 初始化数据表
        self._init_token_tables()
        
        # 加载已保存的配置
        self._load_token_config()
        
        log.info(f"Token管理器初始化完成，默认过期时间: {self.default_expire}毫秒")
    
    def _init_token_tables(self) -> None:
        """初始化token相关数据表"""
        if not GlobalVars.table_exists("api_tokens"):
            GlobalVars.create_table("api_tokens")
            log.info("创建API token配置表")
        
        if not GlobalVars.table_exists("token_usage"):
            GlobalVars.create_table("token_usage")
            log.info("创建token使用记录表")
    
    def _load_token_config(self) -> None:
        """加载已保存的token配置"""
        try:
            # 加载启用token验证的API列表
            enabled_apis = GlobalVars.get_from_table("api_tokens", "enabled_apis", [])
            self.enabled_apis = set(enabled_apis)
            
            # 加载API自定义token
            api_tokens = GlobalVars.get_from_table("api_tokens", "api_tokens", {})
            self.api_tokens = api_tokens
            
            # 加载API自定义过期时间
            api_expires = GlobalVars.get_from_table("api_tokens", "api_token_expires", {})
            self.api_token_expires = api_expires
            
            log.info(f"加载token配置: 启用验证的API {len(self.enabled_apis)} 个，"
                    f"自定义token {len(self.api_tokens)} 个")
            
        except Exception as e:
            log.error(f"加载token配置失败: {e}")
    
    def _save_token_config(self) -> None:
        """保存token配置到数据库"""
        try:
            GlobalVars.set_to_table("api_tokens", "enabled_apis", list(self.enabled_apis))
            GlobalVars.set_to_table("api_tokens", "api_tokens", self.api_tokens)
            GlobalVars.set_to_table("api_tokens", "api_token_expires", self.api_token_expires)
            log.debug("token配置已保存")
        except Exception as e:
            log.error(f"保存token配置失败: {e}")
    
    def enable_token_for_api(self, api_path: str) -> None:
        """为指定API启用token验证"""
        self.enabled_apis.add(api_path)
        self._save_token_config()
        log.info(f"已为API启用token验证: {api_path}")
    
    def disable_token_for_api(self, api_path: str) -> None:
        """为指定API禁用token验证"""
        if api_path in self.enabled_apis:
            self.enabled_apis.remove(api_path)
            self._save_token_config()
            log.info(f"已为API禁用token验证: {api_path}")
    
    def is_token_enabled(self, api_path: str) -> bool:
        """检查指定API是否启用了token验证"""
        return api_path in self.enabled_apis
    
    def set_api_token(self, api_path: str, token: str, expire_ms: Optional[int] = None) -> None:
        """为指定API设置自定义token"""
        self.api_tokens[api_path] = token
        if expire_ms is not None:
            self.api_token_expires[api_path] = expire_ms
        self._save_token_config()
        log.info(f"已为API设置自定义token: {api_path}")
    
    def remove_api_token(self, api_path: str) -> None:
        """移除指定API的自定义token"""
        if api_path in self.api_tokens:
            del self.api_tokens[api_path]
        if api_path in self.api_token_expires:
            del self.api_token_expires[api_path]
        self._save_token_config()
        log.info(f"已移除API的自定义token: {api_path}")
    
    def generate_token(self, api_path: str, length: int = 32) -> str:
        """为指定API生成新的随机token"""
        token = secrets.token_urlsafe(length)
        self.set_api_token(api_path, token)
        return token
    
    def get_api_token(self, api_path: str) -> str:
        """获取指定API的token（自定义或默认）"""
        return self.api_tokens.get(api_path, self.default_token)
    
    def get_api_expire_time(self, api_path: str) -> int:
        """获取指定API的token过期时间（毫秒）"""
        return self.api_token_expires.get(api_path, self.default_expire)
    
    def verify_token(self, api_path: str, provided_token: str, timestamp_ms: Optional[int] = None) -> Tuple[bool, str]:
        """
        验证API token
        
        Args:
            api_path: API路径
            provided_token: 客户端提供的token
            timestamp_ms: 时间戳（毫秒），如果为None则使用当前时间
        
        Returns:
            (is_valid, message)
        """
        # 如果API未启用token验证，直接通过
        if not self.is_token_enabled(api_path):
            return True, "API未启用token验证"
        
        # 获取当前时间戳（毫秒）
        current_time_ms = int(time.time() * 1000)
        
        # 如果没有提供时间戳，使用当前时间
        if timestamp_ms is None:
            timestamp_ms = current_time_ms
        
        # 获取API的token和过期时间
        expected_token = self.get_api_token(api_path)
        expire_time_ms = self.get_api_expire_time(api_path)
        
        # 检查时间戳是否在有效范围内
        time_diff_ms = abs(current_time_ms - timestamp_ms)
        if time_diff_ms > expire_time_ms:
            self._record_token_usage(api_path, provided_token, False, "token已过期")
            return False, f"token已过期，时间差: {time_diff_ms}毫秒，允许范围: {expire_time_ms}毫秒"
        
        # 验证token
        if provided_token == expected_token:
            self._record_token_usage(api_path, provided_token, True, "验证成功")
            return True, "token验证成功"
        else:
            self._record_token_usage(api_path, provided_token, False, "token不匹配")
            return False, "token不匹配"
    
    def verify_signed_token(self, api_path: str, provided_token: str, timestamp_ms: int, 
                           signature: str, additional_data: str = "") -> Tuple[bool, str]:
        """
        验证带签名的token
        
        Args:
            api_path: API路径
            provided_token: 客户端提供的token
            timestamp_ms: 时间戳（毫秒）
            signature: 客户端提供的签名
            additional_data: 额外的签名数据
        
        Returns:
            (is_valid, message)
        """
        # 如果API未启用token验证，直接通过
        if not self.is_token_enabled(api_path):
            return True, "API未启用token验证"
        
        # 基础token验证
        token_valid, token_message = self.verify_token(api_path, provided_token, timestamp_ms)
        if not token_valid:
            return False, token_message
        
        # 生成期望的签名
        expected_signature = self._generate_signature(provided_token, timestamp_ms, api_path, additional_data)
        
        # 验证签名
        if signature.lower() == expected_signature.lower():
            self._record_token_usage(api_path, provided_token, True, "签名验证成功")
            return True, "token和签名验证成功"
        else:
            self._record_token_usage(api_path, provided_token, False, "签名验证失败")
            return False, f"签名验证失败，期望: {expected_signature}，收到: {signature}"
    
    def _generate_signature(self, token: str, timestamp_ms: int, api_path: str, additional_data: str = "") -> str:
        """生成签名"""
        combined_string = f"{token}{timestamp_ms}{api_path}{additional_data}"
        return hashlib.md5(combined_string.encode()).hexdigest()
    
    def _record_token_usage(self, api_path: str, token: str, success: bool, message: str) -> None:
        """记录token使用情况"""
        try:
            current_time = time.time()
            today_str = time.strftime("%Y-%m-%d")
            
            usage_key = f"token_usage:{api_path}:{today_str}"
            usage_data = GlobalVars.get_from_table("token_usage", usage_key, {
                "success_count": 0,
                "failure_count": 0,
                "last_success": None,
                "last_failure": None
            })
            
            if success:
                usage_data["success_count"] += 1
                usage_data["last_success"] = current_time
            else:
                usage_data["failure_count"] += 1
                usage_data["last_failure"] = current_time
            
            GlobalVars.set_to_table("token_usage", usage_key, usage_data)
            
            if not success or log_level == "debug":
                log.debug(f"Token使用记录: API={api_path}, 成功={success}, 消息={message}, "
                         f"Token前缀={token[:8] if token else 'None'}...")
                
        except Exception as e:
            log.error(f"记录token使用情况失败: {e}")
    
    def get_token_usage_stats(self, api_path: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """获取token使用统计"""
        try:
            stats = {}
            
            date_range = []
            for i in range(days):
                date_str = time.strftime("%Y-%m-%d", time.localtime(time.time() - i * 86400))
                date_range.append(date_str)
            
            if api_path:
                api_stats = {"dates": {}, "total_success": 0, "total_failure": 0}
                
                for date_str in date_range:
                    usage_key = f"token_usage:{api_path}:{date_str}"
                    usage_data = GlobalVars.get_from_table("token_usage", usage_key, {})
                    
                    success_count = usage_data.get("success_count", 0)
                    failure_count = usage_data.get("failure_count", 0)
                    
                    api_stats["dates"][date_str] = {
                        "success": success_count,
                        "failure": failure_count,
                        "total": success_count + failure_count
                    }
                    
                    api_stats["total_success"] += success_count
                    api_stats["total_failure"] += failure_count
                
                stats[api_path] = api_stats
            else:
                for enabled_api in self.enabled_apis:
                    api_stats = {"dates": {}, "total_success": 0, "total_failure": 0}
                    
                    for date_str in date_range:
                        usage_key = f"token_usage:{enabled_api}:{date_str}"
                        usage_data = GlobalVars.get_from_table("token_usage", usage_key, {})
                        
                        success_count = usage_data.get("success_count", 0)
                        failure_count = usage_data.get("failure_count", 0)
                        
                        api_stats["dates"][date_str] = {
                            "success": success_count,
                            "failure": failure_count,
                            "total": success_count + failure_count
                        }
                        
                        api_stats["total_success"] += success_count
                        api_stats["total_failure"] += failure_count
                    
                    stats[enabled_api] = api_stats
            
            return {
                "stats": stats,
                "summary": {
                    "enabled_apis_count": len(self.enabled_apis),
                    "custom_tokens_count": len(self.api_tokens),
                    "date_range": date_range,
                    "query_time": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
        except Exception as e:
            log.error(f"获取token使用统计失败: {e}")
            return {"error": str(e)}
    
    def get_api_config(self, api_path: str) -> Dict[str, Any]:
        """获取指定API的token配置"""
        return {
            "api_path": api_path,
            "token_enabled": self.is_token_enabled(api_path),
            "has_custom_token": api_path in self.api_tokens,
            "custom_token": self.api_tokens.get(api_path, ""),
            "expire_time_ms": self.get_api_expire_time(api_path),
            "is_using_default": api_path not in self.api_token_expires
        }
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有API的token配置"""
        return {
            "default_token": self.default_token,
            "default_expire_ms": self.default_expire,
            "enabled_apis": list(self.enabled_apis),
            "api_configs": {
                api_path: self.get_api_config(api_path) 
                for api_path in self.enabled_apis
            },
            "custom_tokens": dict(self.api_tokens),
            "custom_expires": dict(self.api_token_expires)
        }

token_manager = TokenManager()

def extract_token_from_request(request) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """
    从请求中提取token信息
    
    Args:
        request: FastAPI Request对象
    
    Returns:
        (token, timestamp_ms, signature)
    """
    token = request.headers.get("x-api-token") or request.headers.get("authorization")
    if token and token.startswith("Bearer "):
        token = token[7:]
    
    # 获取时间戳
    timestamp_str = request.headers.get("x-timestamp")
    timestamp_ms = None
    if timestamp_str:
        try:
            timestamp_ms = int(timestamp_str)
        except ValueError:
            log.warning(f"无效的时间戳格式: {timestamp_str}")
    
    # 获取签名
    signature = request.headers.get("x-signature")
    
    if not token:
        token = request.query_params.get("token")
    
    if not timestamp_ms:
        timestamp_str = request.query_params.get("timestamp")
        if timestamp_str:
            try:
                timestamp_ms = int(timestamp_str)
            except ValueError:
                pass
    
    if not signature:
        signature = request.query_params.get("signature")
    
    return token, timestamp_ms, signature

def verify_api_token(api_path: str, request, use_signature: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
    """
    验证API token的便捷函数
    
    Args:
        api_path: API路径
        request: FastAPI Request对象
        use_signature: 是否使用签名验证
    
    Returns:
        (is_valid, message, debug_info)
    """
    token, timestamp_ms, signature = extract_token_from_request(request)
    
    debug_info = {
        "api_path": api_path,
        "token_provided": token is not None,
        "timestamp_provided": timestamp_ms is not None,
        "signature_provided": signature is not None,
        "use_signature": use_signature,
        "token_enabled": token_manager.is_token_enabled(api_path)
    }
    
    if not token_manager.is_token_enabled(api_path):
        return True, "API未启用token验证", debug_info
    
    if not token:
        return False, "缺少API token", debug_info
    
    if use_signature:
        if not signature:
            return False, "缺少签名", debug_info
        if timestamp_ms is None:
            return False, "缺少时间戳", debug_info
        
        is_valid, message = token_manager.verify_signed_token(
            api_path, token, timestamp_ms, signature
        )
    else:
        is_valid, message = token_manager.verify_token(api_path, token, timestamp_ms)
    
    debug_info["verification_result"] = is_valid
    debug_info["verification_message"] = message
    
    return is_valid, message, debug_info

# 导出主要函数和类
__all__ = [
    "TokenManager",
    "token_manager", 
    "extract_token_from_request",
    "verify_api_token"
]