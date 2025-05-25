from pydantic import BaseModel,Field
from typing import Optional,Union,Dict, Any

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

class Music_infoBase(BaseModel):
    music_id: Optional[str] = Field(None, description="歌曲id")
    qq: Optional[int] = Field(None, description="玩家QQ号")
    name: Optional[str] = Field(None, description="玩家名称")
    class Config:
        extra = "forbid"

class Rating_tableBase(BaseModel):
    qq: Optional[int] = Field(None, description="玩家QQ号")
    rating: Optional[str] = Field(None, description="rating")
    isfc: Optional[bool] = Field(False, description="是否FC")

    class Config:
        extra = "forbid"

class Plate_tableBase(BaseModel):
    qq: Optional[int] = Field(None, description="玩家QQ号")
    version: Optional[str] = Field(None, description="version")
    plan: Optional[str] = Field(None, description="plan")

    class Config:
        extra = "forbid"

class Rise_scoreBase(BaseModel):
    qq: Optional[int] = Field(None, description="玩家QQ号")
    name: Optional[str] = Field(None, description="玩家名称")
    nickname: Optional[str] = Field(None, description="玩家昵称")
    rating: Optional[str] = Field(None, description="rating")
    score: Optional[str] = Field(None, description="分数")

    class Config:
        extra = "forbid"

class Music_globalBase(BaseModel):
    music_data: Dict[str, Any] = Field(..., description="歌曲原始数据")
    level_index: Optional[int] = Field(None, description="level_index")
    
    class Config:
        extra = "forbid"

class Level_processBase(BaseModel):
    qq: Optional[int] = Field(None, description="玩家QQ号")
    name: Optional[str] = Field(None, description="玩家名称")
    level: Optional[str] = Field(None, description="定数")
    plan: Optional[str] = Field(None, description="评价等级")
    category: Optional[str] = Field("default", description="category")
    page: Optional[int] = Field(1, description="page")

    class Config:
        extra = "forbid"

class Level_achievement_listBase(BaseModel):
    qq: Optional[int] = Field(None, description="玩家QQ号")
    name: Optional[str] = Field(None, description="玩家名称")
    rating: Optional[Union[str, float]] = Field(None, description="定数")
    page: Optional[int] = Field(1, description="page")

    class Config:
        extra = "forbid"

class Rating_rankingBase(BaseModel):
    name: Optional[str] = Field(None, description="玩家名称")
    page: Optional[int] = Field(1, description="page")

    class Config:
        extra = "forbid"