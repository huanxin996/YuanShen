import os, logging, datetime, copy
from config import log_level, project_root
from uvicorn.config import LOGGING_CONFIG

class DailyFileHandler(logging.Handler):
    def __init__(self, log_dir):
        super().__init__()
        self.log_dir = log_dir
        self.current_file = None
        self.current_date = None
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        self.setFormatter(logging.Formatter(fmt))
        self._update_file_if_needed()
    
    def _get_log_file(self):
        """获取日期的路径"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"{today}.log")
    
    def _update_file_if_needed(self):
        """更新文件句柄用的"""
        today = datetime.datetime.now().date()
        if today != self.current_date:
            if self.current_file:
                self.current_file.close()
            
            log_file = self._get_log_file()
            self.current_file = open(log_file, "a", encoding="utf-8")
            self.current_date = today
    
    def emit(self, record):
        """发送记录，还有检查日期变化"""
        self._update_file_if_needed()
        try:
            msg = self.format(record)
            self.current_file.write(msg + "\n")
            self.current_file.flush()
        except Exception:
            self.handleError(record)

def get_log_config():
    """获取自定义日志配置"""
    log_config = copy.deepcopy(LOGGING_CONFIG)
    
    log_dir = os.path.join(project_root, "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_config["handlers"]["file"] = {
        "()": lambda: DailyFileHandler(log_dir),
        "level": log_level.upper(),
    }
    
    for logger_name, logger in log_config["loggers"].items():
        if "handlers" in logger:
            if "file" not in logger["handlers"]:
                logger["handlers"].append("file")
        else:
            logger["handlers"] = ["file"]
        
        logger["level"] = log_level.upper()
    
    log_config["loggers"]["app"] = {
        "handlers": ["default", "file"],
        "level": log_level.upper(),
        "propagate": False
    }
    
    return log_config