import json,os,time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from config import project_root
from pathlib import Path


cache_config_dir = project_root / "data"
if not os.path.exists(cache_config_dir):
    os.makedirs(cache_config_dir)


@dataclass
class GlobalVars:
    _instance = None
    _is_loaded: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    _storage_path: Path = cache_config_dir / "global_vars.json"
    _last_update: Dict[str, float] = field(default_factory=dict)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalVars, cls).__new__(cls)
            cls._instance.data = {}
            cls._instance._last_update = {}
            cls._instance._is_loaded = False
        return cls._instance
    
    def ensure_loaded(self) -> None:
        """确保数据已加载"""
        if not self._is_loaded:
            self._load_data()
            self._is_loaded = True
            
    def _load_data(self) -> None:
        """从文件加载数据"""
        try:
            if self._storage_path.exists():
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                    return self.data
        except Exception as e:
            print(f"加载数据失败: {e}")
            
    def _save_data(self) -> None:
        """保存数据到文件"""
        try:
            self._storage_path.parent.mkdir(exist_ok=True)
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    @classmethod
    def set(cls, key: str, value: Any, expire: Optional[int] = None) -> None:
        """设置值,可选过期时间(秒)"""
        instance = cls()
        instance.ensure_loaded()
        instance.data[key] = value
        instance._last_update[key] = time.time()
        if expire:
            instance.data[f"{key}_expire"] = time.time() + expire
        instance._save_data()
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """获取值,自动处理过期"""
        instance = cls() if cls._instance is None else cls._instance
        instance.ensure_loaded()
        expire_time = instance.data.get(f"{key}_expire")
        
        if expire_time and time.time() > expire_time:
            instance.delete(key)
            return default
            
        return instance.data.get(key, default)

    @classmethod
    def delete(cls, key: str) -> None:
        """删除键值对"""
        instance = cls() if cls._instance is None else cls._instance
        instance.ensure_loaded()
        instance.data.pop(key, None)
        instance.data.pop(f"{key}_expire", None)
        instance._last_update.pop(key, None)
        instance._save_data()
    
    @classmethod
    def clear_expired(cls) -> None:
        """清理所有过期数据"""
        instance = cls() if cls._instance is None else cls._instance
        instance.ensure_loaded()
        current_time = time.time()
        expired_keys = [
            key for key, expire_time in instance.data.items()
            if key.endswith('_expire') and current_time > expire_time
        ]
        for key in expired_keys:
            original_key = key[:-7]  # 移除_expire后缀
            instance.delete(original_key)

    @classmethod
    def get_all_keys(cls) -> list:
        """获取所有键名（不包括过期时间键）"""
        instance = cls() if cls._instance is None else cls._instance
        instance.ensure_loaded()
        return [key for key in instance.data.keys() if not key.endswith('_expire')]
    
    @classmethod
    def get_all(cls) -> dict:
        """获取所有数据的副本（不包括过期时间相关数据）"""
        instance = cls() if cls._instance is None else cls._instance
        instance.ensure_loaded()
        return {k: v for k, v in instance.data.items() if not k.endswith('_expire')}