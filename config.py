import os
from pathlib import Path

maimaitoken = "9lYvOLzHZwu5BTAyeVhNbFgn4psMSXcC"
admin_token = "你的管理员token"
api_default_token = "你的API默认token"
api_default_token_expire = 3600  # 默认API token过期时间，单位为毫秒
favicon_path = None # "static/favicon.ico"路由图片
log_level = "info"
project_root: Path = Path(os.getcwd())

