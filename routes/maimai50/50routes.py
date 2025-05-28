from typing import Callable,Awaitable
from loguru import logger as log
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from api.maimai50.maimaidx_music import *
from api.maimai50.maimaidx_best_50 import (
    generate, generate_bypass, generate_cum, generate_theoretical,
    generate_abstract, generate_high, generate_ap, generate_fc
)
from api.maimai50.maimaidx_music_info import (
    music_play_data,draw_music_info,
    draw_rating_table,draw_plate_table
    )
from api.maimai50.maimaidx_player_score import (
    music_global_data, rise_score_data, 
    level_process_data,level_achievement_list_data,
    rating_ranking_data
    )
from api.maimai50.Bases import (
    B50Base, MinfoBase,Music_infoBase,
    Rating_tableBase,Plate_tableBase,
    Music_globalBase,Rise_scoreBase,
    Level_processBase,Level_achievement_listBase,
    Rating_rankingBase
    )
from api.maimai50.maimaidx_error import *
from methods.image_manner import image_manager


router = APIRouter(prefix="/maimai", tags=["maimai50"])

async def process_image_result(image, endpoint_name: str) -> JSONResponse:
    """处理图片结果并返回JSON响应"""
    if not image:
        log.error(f"{endpoint_name}: 图片生成失败")
        return JSONResponse(status_code=500, content={"returnCode": 101, "msg": "图片生成失败"})
    if not hasattr(image, 'save') or not callable(getattr(image, 'save', None)):
        return JSONResponse(status_code=500, content={"returnCode": 101, "msg": f"{image}"})
    base64_image = image_manager.image_to_base64(image)
    return JSONResponse(
        status_code=200, 
        content={"returnCode": 1, "base64": base64_image}
    )

async def process_image_request(
    item: B50Base, 
    generator_func: Callable, 
    endpoint_name: str
) -> JSONResponse:
    try:
        if not item.qq and not item.name:
            log.error(f"{endpoint_name}: 缺少必要参数：qq 和 name")
            return JSONResponse(
                status_code=400, 
                content={"returnCode": 100, "msg": "缺少必要参数：qq 和 name，请至少提供一个"}
            )
        log.info(f"{endpoint_name} 请求: {item}，qq: {item.qq}, name: {item.name}")
        try:
            image = await generator_func(qqid=item.qq, username=item.name)
        except UserNotFoundError as e:
            log.error(f"{endpoint_name}: 找不到用户: {e}")
            return JSONResponse(status_code=400, content={"returnCode": 100, "msg": str(e)})
        except UserDisabledQueryError as e:
            log.error(f"{endpoint_name}: 用户查询被禁用: {e}")
            return JSONResponse(status_code=400, content={"returnCode": 100, "msg": str(e)})
        except Exception as e:
            log.error(f"{endpoint_name}: 制图失败: {e}")
            return JSONResponse(status_code=500, content={"returnCode": 101, "msg": str(e)})

        return await process_image_result(image, endpoint_name)
    except Exception as e:
        log.exception(f"{endpoint_name} 请求处理错误: {e}")
        return JSONResponse(status_code=500, content={"returnCode": 101, "msg": str(e)})

async def safe_image_call(awaitable: Awaitable, endpoint_name: str):
    try:
        pic = await awaitable
    except (UserNotFoundError, UserDisabledQueryError) as e:
        log.error(f"{endpoint_name}: {e}")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": str(e)})
    except Exception as e:
        log.exception(f"{endpoint_name} 发生未知错误: {e}")
        return JSONResponse(status_code=500, content={"returnCode": 101, "msg": str(e)})
    return await process_image_result(pic, endpoint_name)


@router.post("/b50")
async def create_b50(item: B50Base):
    """生成标准B50图片"""
    return await process_image_request(item, generate, "B50")

@router.post("/bypass50")
async def create_bypass50(item: B50Base):
    """生成Bypass B50图片"""
    return await process_image_request(item, generate_bypass, "BypassB50")

@router.post("/theoretical50")
async def create_theoretical50(item: B50Base):
    """生成理论值B50图片"""
    return await process_image_request(item, generate_theoretical, "TheoreticalB50")

@router.post("/cum50")
async def create_cum50(item: B50Base):
    """生成积分B50图片"""
    return await process_image_request(item, generate_cum, "CumB50")

@router.post("/abstract50")
async def create_abstract50(item: B50Base):
    """生成简洁版B50图片"""
    return await process_image_request(item, generate_abstract, "AbstractB50")

@router.post("/high50")
async def create_high50(item: B50Base):
    """生成高分B50图片"""
    return await process_image_request(item, generate_high, "HighB50")

@router.post("/ap50")
async def create_ap50(item: B50Base):
    """生成AP成绩B50图片"""
    return await process_image_request(item, generate_ap, "APB50")

@router.post("/fc50")
async def create_fc50(item: B50Base):
    """生成FC成绩B50图片"""
    return await process_image_request(item, generate_fc, "FCB50")


@router.post("/minfo")
async def create_minfo(item: MinfoBase):
    try:
        endpoint_name = "MInfo"
        log.info(f"Received request: {item}，qq: {item.qq}, songid: {item.music_id}")
        if not item.qq or not item.music_id:
            log.error("缺少必要参数：qq 和 songid")
            return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：qq 和 songid，请提供所有参数"})
        if mai.total_list.by_id(item.music_id):
            songs = item.music_id
        elif by_t := mai.total_list.by_title(item.music_id):
            songs = by_t.id
        else:
            aliases = mai.total_alias_list.by_alias(item.music_id)
            if not aliases:
                return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "未找到曲目，请检查曲名或ID是否正确"})
            elif len(aliases) != 1:
                msg = '找到相同别名的曲目,请使用以下ID查询:\n'
                for songs in aliases:
                    msg += f'{songs.SongID}:{songs.Name}\n'
                return JSONResponse(status_code=400, content={"returnCode": 100, "msg": msg.strip()})
            else:
                songs = str(aliases[0].SongID)
        return await safe_image_call(music_play_data(qqid=item.qq, music_id=songs), endpoint_name)
    except Exception as e:
        return JSONResponse(status_code=500, content={"returnCode": 101, "msg": str(e)})

@router.post("/music_info")
async def create_music_info(item: Music_infoBase):
    endpoint_name = "MusicInfo"
    log.info(f"Received request: {item}，qq: {item.qq}, music: {item.music_id}")
    if not (item.qq or item.name) or not item.music_id:
        log.error("缺少必要参数：qq 和 music_data")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：qq 和 music_data，请提供所有参数"})
    music = mai.total_list.by_id(item.music_id)
    if not music:
        log.error("未找到曲目，请检查曲名或ID是否正确")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "未找到曲目，请检查曲名或ID是否正确"})
    return await safe_image_call(draw_music_info(qqid=item.qq, music=music), endpoint_name)

@router.post("/rating_table")
async def create_rating_table(item: Rating_tableBase):
    endpoint_name = "RatingTable"
    log.info(f"Received request: {item}，qq: {item.qq}, rating: {item.rating}")
    if not item.qq or not item.rating:
        log.error("缺少必要参数：qq 和 rating")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：qq 和 rating，请提供所有参数"})
    return await safe_image_call(draw_rating_table(qqid=item.qq, rating=item.rating, isfc=item.isfc), endpoint_name)

@router.post("/plate_table")
async def create_plate_table(item: Plate_tableBase):
    endpoint_name = "PlateTable"
    log.info(f"Received request: {item}，qq: {item.qq}, version: {item.version}, plan: {item.plan}")
    if not item.qq or not item.version or not item.plan:
        log.error("缺少必要参数：qq 和 version 和 plan")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：qq 和 version 和 plan，请提供所有参数"})
    return await safe_image_call(draw_plate_table(qqid=item.qq, version=item.version, plan=item.plan), endpoint_name)

@router.post("/music_global")
async def create_music_global(item: Music_globalBase):
    endpoint_name = "MusicGlobal"
    log.info(f"Received request: {item}，qq: {item.qq}, music_data: {item.music_data}")
    if not item.music_data or not item.level_index:
        log.error("缺少必要参数：music_data 和 level_index")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：music_data 和 level_index，请提供所有参数"})
    return await safe_image_call(music_global_data(music=item.music_data, level_index=item.level_index), endpoint_name)

@router.post("/rise_score")
async def create_rise_score(item: Rise_scoreBase):
    endpoint_name = "RiseScore"
    log.info(f"Received request: {item}，qq: {item.qq}, name: {item.name}, nickname: {item.nickname}, rating: {item.rating}, score: {item.score}")
    if not item.qq or not item.rating or not item.score:
        log.error("缺少必要参数：qq 和 name 和 rating 和 score")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：qq 和 rating 和 score，请提供所有参数"})
    return await safe_image_call(rise_score_data(qqid=item.qq, username=item.name, nickname=item.nickname, rating=item.rating, score=item.score), endpoint_name)


@router.post("/level_process")
async def create_level_process(item: Level_processBase):
    endpoint_name = "LevelProcess"
    log.info(f"Received request: {item}，qq: {item.qq}, name: {item.name}, level: {item.level}, plan: {item.plan}")
    if not item.qq or not item.level or not item.plan:
        log.error("缺少必要参数：qq 和 level 和 plan")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：qq 和 level 和 plan，请提供所有参数"})
    return await safe_image_call(level_process_data(qqid=item.qq, username=item.name, level=item.level, plan=item.plan, category=item.category, page=item.page), endpoint_name)


@router.post("/level_achievement_list")
async def create_level_achievement_list(item: Level_achievement_listBase):
    endpoint_name = "LevelAchievementList"
    log.info(f"Received request: {item}，qq: {item.qq}, name: {item.name}, rating: {item.rating}")
    if not item.qq or not item.rating:
        log.error("缺少必要参数：qq 和 rating")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：qq 和 name 和 rating，请提供所有参数"})
    return await safe_image_call(level_achievement_list_data(qqid=item.qq, username=item.name, rating=item.rating, page=item.page), endpoint_name)

@router.post("/rating_ranking")
async def create_rating_ranking(item: Rating_rankingBase):
    endpoint_name = "RatingRanking"
    log.info(f"Received request: {item}， name: {item.name}, page: {item.page}")
    if not item.name or not item.page:
        log.error("缺少必要参数：name 和 page")
        return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：page 和 name ，请提供所有参数"})
    return await safe_image_call(rating_ranking_data(name=item.name, rating=item.page), endpoint_name)



def register_routes(app: FastAPI):
    log.info(f"注册maimai50路由，前缀：{router.prefix}")
    #for route in router.routes:
    #    if hasattr(route, "path"):
    #        log.info(f"路由：{route.path}，方法：{route.methods if hasattr(route, 'methods') else '未知'}")
    
    app.include_router(router)


