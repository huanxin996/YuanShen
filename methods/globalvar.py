import json, os, time, sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from config import project_root
import threading
import atexit


cache_config_dir = project_root / "data"
if not os.path.exists(cache_config_dir):
    os.makedirs(cache_config_dir)


@dataclass
class GlobalVars:
    _instance = None
    _is_loaded: bool = False
    _conn = None
    _lock = threading.RLock()  # 使用可重入锁确保线程安全
    _storage_path: Path = cache_config_dir / "global_vars.db"
    _default_table: str = "global_vars"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalVars, cls).__new__(cls)
            cls._instance._is_loaded = False
        return cls._instance
    
    def ensure_loaded(self) -> None:
        """确保数据库已加载和初始化"""
        with self._lock:
            if not self._is_loaded:
                self._init_db()
                self._is_loaded = True
    
    def _get_connection(self):
        """获取数据库连接（如果未打开则创建）"""
        with self._lock:
            if self._conn is None:
                self._conn = sqlite3.connect(str(self._storage_path), check_same_thread=False)
                # 启用外键约束
                self._conn.execute("PRAGMA foreign_keys = ON")
                # 启用递归触发器
                self._conn.execute("PRAGMA recursive_triggers = ON")
                # 使用行工厂
                self._conn.row_factory = sqlite3.Row
            return self._conn
    
    def _init_db(self) -> None:
        """初始化数据库，创建必要的表"""
        conn = self._get_connection()
        # 创建默认键值表
        self._ensure_table_exists(self._default_table)
        
    def _ensure_table_exists(self, table_name: str) -> None:
        """确保指定的表存在，如不存在则创建"""
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expire_time REAL DEFAULT NULL,
            last_update REAL NOT NULL
        )
        ''')
        
        conn.commit()
    
    def _serialize_value(self, value: Any) -> str:
        """将Python对象序列化为JSON存储"""
        return json.dumps(value, ensure_ascii=False)
    
    def _deserialize_value(self, value_json: str) -> Any:
        """将JSON序列化的值还原为Python对象"""
        if value_json is None:
            return None
        try:
            return json.loads(value_json)
        except json.JSONDecodeError:
            return value_json
    
    @classmethod
    def set(cls, key: str, value: Any, expire: Optional[int] = None) -> None:
        """设置默认表中的值，可选过期时间(秒)"""
        instance = cls()
        instance.ensure_loaded()
        cls.set_to_table(instance._default_table, key, value, expire)
    
    @classmethod
    def set_to_table(cls, table_name: str, key: str, value: Any, expire: Optional[int] = None) -> None:
        """设置指定表中的值，可选过期时间(秒)"""
        instance = cls()
        instance.ensure_loaded()
        instance._ensure_table_exists(table_name)
        
        conn = instance._get_connection()
        cursor = conn.cursor()
        
        # 序列化值
        value_json = instance._serialize_value(value)
        current_time = time.time()
        expire_time = current_time + expire if expire else None
        
        # 使用参数化查询防止SQL注入
        cursor.execute(
            f"REPLACE INTO {table_name} (key, value, expire_time, last_update) VALUES (?, ?, ?, ?)",
            (key, value_json, expire_time, current_time)
        )
        
        conn.commit()
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """从默认表获取值，自动处理过期"""
        return cls.get_from_table(cls()._default_table, key, default)
    
    @classmethod
    def get_from_table(cls, table_name: str, key: str, default: Any = None) -> Any:
        """从指定表获取值，自动处理过期"""
        instance = cls()
        instance.ensure_loaded()
        
        # 检查表是否存在
        if not cls.table_exists(table_name):
            return default
        
        conn = instance._get_connection()
        cursor = conn.cursor()
        
        # 查询数据
        cursor.execute(
            f"SELECT value, expire_time FROM {table_name} WHERE key = ?",
            (key,)
        )
        
        row = cursor.fetchone()
        if not row:
            return default
        
        value_json, expire_time = row
        
        # 检查是否过期
        if expire_time and time.time() > expire_time:
            cls.delete_from_table(table_name, key)  # 删除过期数据
            return default
        
        return instance._deserialize_value(value_json)

    @classmethod
    def delete(cls, key: str) -> None:
        """从默认表删除键值对"""
        cls.delete_from_table(cls()._default_table, key)
    
    @classmethod
    def delete_from_table(cls, table_name: str, key: str) -> None:
        """从指定表删除键值对"""
        instance = cls()
        instance.ensure_loaded()
        
        if not cls.table_exists(table_name):
            return
        
        conn = instance._get_connection()
        cursor = conn.cursor()
        
        # 删除数据
        cursor.execute(f"DELETE FROM {table_name} WHERE key = ?", (key,))
        conn.commit()
    
    @classmethod
    def clear_expired(cls, table_name: Optional[str] = None) -> None:
        """清理指定表或所有表中的过期数据"""
        instance = cls()
        instance.ensure_loaded()
        
        if table_name:
            # 清理指定表
            if cls.table_exists(table_name):
                cls._clear_expired_in_table(table_name)
        else:
            # 清理所有表
            tables = cls.get_all_tables()
            for table in tables:
                cls._clear_expired_in_table(table)
    
    @classmethod
    def _clear_expired_in_table(cls, table_name: str) -> None:
        """清理指定表中的过期数据（内部方法）"""
        instance = cls()
        conn = instance._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            f"DELETE FROM {table_name} WHERE expire_time IS NOT NULL AND expire_time < ?",
            (time.time(),)
        )
        
        conn.commit()

    @classmethod
    def get_all_keys(cls) -> List[str]:
        """获取默认表中的所有键名"""
        return cls.get_all_keys_from_table(cls()._default_table)
    
    @classmethod
    def get_all_keys_from_table(cls, table_name: str) -> List[str]:
        """获取指定表中的所有键名"""
        instance = cls()
        instance.ensure_loaded()
        
        if not cls.table_exists(table_name):
            return []
        
        conn = instance._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT key FROM {table_name}")
        return [row[0] for row in cursor.fetchall()]
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """获取默认表中所有数据的副本"""
        return cls.get_all_from_table(cls()._default_table)
    
    @classmethod
    def get_all_from_table(cls, table_name: str) -> Dict[str, Any]:
        """获取指定表中所有数据的副本"""
        instance = cls()
        instance.ensure_loaded()
        
        if not cls.table_exists(table_name):
            return {}
        
        conn = instance._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT key, value FROM {table_name}")
        
        result = {}
        for key, value_json in cursor.fetchall():
            result[key] = instance._deserialize_value(value_json)
        
        return result
    
    @classmethod
    def table_exists(cls, table_name: str) -> bool:
        """检查指定的表是否存在"""
        instance = cls()
        instance.ensure_loaded()
        
        conn = instance._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        
        return cursor.fetchone() is not None
    
    @classmethod
    def get_all_tables(cls) -> List[str]:
        """获取数据库中的所有表名"""
        instance = cls()
        instance.ensure_loaded()
        
        conn = instance._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]
    
    @classmethod
    def close(cls) -> None:
        """关闭数据库连接"""
        instance = cls()
        with instance._lock:
            if instance._conn:
                instance._conn.close()
                instance._conn = None
                instance._is_loaded = False
    
    @classmethod
    def backup(cls, backup_path: Optional[str] = None) -> str:
        """备份数据库到指定路径"""
        instance = cls()
        instance.ensure_loaded()
        
        if not backup_path:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = str(cache_config_dir / f"global_vars_backup_{timestamp}.db")
        
        if not os.path.exists(instance._storage_path):
            raise FileNotFoundError(f"数据库文件不存在: {instance._storage_path}")
        
        source_conn = instance._get_connection()
        dest_conn = sqlite3.connect(backup_path)
        
        with instance._lock:
            source_conn.backup(dest_conn)
        
        dest_conn.close()
        return backup_path
    
    @classmethod
    def vacuum(cls) -> None:
        """执行VACUUM操作压缩数据库文件"""
        instance = cls()
        instance.ensure_loaded()
        
        conn = instance._get_connection()
        conn.execute("VACUUM")
        conn.commit()
        
    @classmethod
    def initialize(cls) -> None:
        """主动初始化全局变量管理器"""
        instance = cls()
        instance.ensure_loaded()
        # 设置应用启动时间，如果不存在
        if not cls.get("server_start_time"):
            cls.set("server_start_time", time.time())
        # 清理可能存在的过期数据
        cls.clear_expired()
        
    @classmethod
    def create_table(cls, table_name: str) -> bool:
        """创建新表，如果表已存在则返回False"""
        instance = cls()
        instance.ensure_loaded()
        
        if cls.table_exists(table_name):
            return False
            
        instance._ensure_table_exists(table_name)
        return True
    
    @classmethod
    def drop_table(cls, table_name: str) -> bool:
        """删除指定表，如果表不存在则返回False"""
        if table_name == cls()._default_table:
            raise ValueError("不能删除默认表")
            
        instance = cls()
        instance.ensure_loaded()
        
        if not cls.table_exists(table_name):
            return False
            
        conn = instance._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"DROP TABLE {table_name}")
        conn.commit()
        
        return True
        
    @classmethod
    def shutdown(cls) -> None:
        """安全关闭全局变量管理器，确保数据刷新到磁盘"""
        cls.close()
        
    class Context:
        """提供上下文管理器支持，确保在特定上下文中安全操作"""
        def __enter__(self):
            GlobalVars.initialize()
            return GlobalVars
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            GlobalVars.shutdown()
            

atexit.register(GlobalVars.shutdown)

GlobalVars.initialize()