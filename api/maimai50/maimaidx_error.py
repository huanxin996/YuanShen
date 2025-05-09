class UserNotFoundError(Exception):
    
    def __str__(self) -> str:
        return '''由于官方QQBOT限制 无法获取真实QQ\n导致无法使用部分查分功能(如查询B50)\n请发送:@MilkBOT 获取频道ID  \n获取绑定教程 绑定成功后皆可使用查分功能~'''


class UserDisabledQueryError(Exception):
    
    def __str__(self) -> str:
        return '你在水鱼中似乎设置了不允许他人查询你的成绩 Milk也无法看到的说'
    

class ServerError(Exception):
    
    def __str__(self) -> str:
        return '别名服务器 坏!'


class EnterError(Exception):
    
    def __str__(self) -> str:
        return '输入错误了哦 Milk看不懂捏'


class CoverError(Exception):
    """图片错误"""


class UnknownError(Exception):
    """未知错误"""