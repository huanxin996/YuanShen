from typing import Callable
from loguru import logger as log
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from api.maimai50.maimaidx_music import *
from api.maimai50.maimaidx_best_50 import (
    generate, generate_bypass, generate_cum, generate_theoretical,
    generate_abstract, generate_high, generate_ap, generate_fc
)
from api.maimai50.maimaidx_music_info import music_play_data
from api.maimai50.Bases import B50Base, MinfoBase
from api.maimai50.maimaidx_error import *
from methods.image_manner import image_manager

router = APIRouter(prefix="/maimai", tags=["maimai50"])


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

        if not image:
            log.error(f"{endpoint_name}: 图片生成失败")
            return JSONResponse(status_code=500, content={"returnCode": 101, "msg": "图片生成失败"})
        if not hasattr(image, 'save') or not callable(getattr(image, 'save', None)):
            log.error(f"返回值不是有效图片对象: {type(image)}")
            return JSONResponse(status_code=500, content={"returnCode": 101, "msg": f"{image}"})
        base64_image = image_manager.image_to_base64(image)
        return JSONResponse(
            status_code=200, 
            content={"returnCode": 1, "base64": base64_image}
        )
    except Exception as e:
        log.exception(f"{endpoint_name} 请求处理错误: {e}")
        return JSONResponse(status_code=500, content={"returnCode": 101, "msg": str(e)})


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
        log.info(f"Received request: {item}，qq: {item.qq}, songid: {item.songid}")
        if not item.qq or not item.songid:
            log.error("缺少必要参数：qq 和 songid")
            return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "缺少必要参数：qq 和 songid，请提供所有参数"})
        if mai.total_list.by_id(item.songid):
            songs = item.songid
        elif by_t := mai.total_list.by_title(item.songid):
            songs = by_t.id
        else:
            aliases = mai.total_alias_list.by_alias(item.songid)
            if not aliases:
                return JSONResponse(status_code=400, content={"returnCode": 100, "msg": "未找到曲目，请检查曲名或ID是否正确"})
            elif len(aliases) != 1:
                msg = '找到相同别名的曲目,请使用以下ID查询:\n'
                for songs in aliases:
                    msg += f'{songs.SongID}:{songs.Name}\n'
                return JSONResponse(status_code=400, content={"returnCode": 100, "msg": msg.strip()})
            else:
                songs = str(aliases[0].SongID)
        try:
            pic = await music_play_data(qqid=item.qq, songs=songs)
        except (UserNotFoundError, UserDisabledQueryError) as e:
            log.error(f"找不到用户: {e}")
            return JSONResponse(status_code=400, content={"returnCode": 100, "msg": str(e)})
        except Exception as e:
            log.error(f"制图失败: {e}")
            return JSONResponse(status_code=500, content={"returnCode": 101, "msg": str(e)})

        if pic is None:
            log.error(f"曲目数据图片生成失败: qq={item.qq}, songid={songs}")
            return JSONResponse(status_code=500, content={"returnCode": 101, "msg": "曲目数据图片生成失败"})
        if not hasattr(pic, 'save') or not callable(getattr(pic, 'save', None)):
            log.error(f"返回值不是有效图片对象: {type(pic)}")
            return JSONResponse(status_code=500, content={"returnCode": 101, "msg": f"{pic}"})
        base64_image = image_manager.image_to_base64(pic)
        return JSONResponse(status_code=200, content={
            "returnCode": 1, 
            "base64": base64_image,
            "songid": songs
        })
    except Exception as e:
        log.exception(f"处理曲目信息请求时出错: {e}")
        return JSONResponse(status_code=500, content={"returnCode": 101, "msg": str(e)})


def register_routes(app: FastAPI):
    log.info(f"注册maimai50路由，前缀：{router.prefix}")
    #for route in router.routes:
    #    if hasattr(route, "path"):
    #        log.info(f"路由：{route.path}，方法：{route.methods if hasattr(route, 'methods') else '未知'}")
    
    app.include_router(router)


