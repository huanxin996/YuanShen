from pydantic import BaseModel,Field
from typing import Optional,Union


class B50Base(BaseModel):
    qq: Optional[int] = Field(None, description="玩家QQ号")
    name: Optional[str] = Field(None, description="玩家名称")
    class Config:
        extra = "forbid"

class MinfoBase(BaseModel):
    qq: int = Field(..., description="玩家QQ号")
    songid: Union[str, int] = Field(..., description="歌曲ID或名称")
    
    class Config:
        extra = "forbid"