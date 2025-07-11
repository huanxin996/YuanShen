import copy
import time

import aiofiles

from .maimaidx_best_50 import *
from .maimaidx_music import Music, RaMusic, mai


def image_scale(height: int) -> Tuple[Image.Image, int, int]:
    """
    - `height`: 图片高度

    返回元组 `(缩放图片, 坐标x, 坐标y)`
    """
    bg = Image.open(maimaidir / ('buddies_bg_2.png' if height > 1800 else 'buddies_bg.png')).convert('RGBA')
    bg_w, bg_h = bg.size

    if height > bg_h:
        percent = (height - bg_h) / bg_h
        new_w, new_h = int(bg_w + bg_w * percent), int(bg_h + bg_h * percent)
        newbg = bg.resize((new_w, new_h))
        bg_x = int((1500 - new_w) / 2)
        bg_y = 0
    elif height < bg_h:
        newbg = bg
        bg_x = int((1500 - bg_w) / 2)
        bg_y = int(height - bg_h)
    else:
        newbg = bg
        bg_x, bg_y = 0, 0

    return newbg, bg_x, bg_y


async def update_rating_table() -> str:
    """更新定数表"""
    try:
        bg_color = [(111, 212, 61, 255), (248, 183, 9, 255), (255, 129, 141, 255), (159, 81, 220, 255), (219, 170, 255, 255)]
        dx = Image.open(maimaidir / 'DX.png').convert('RGBA').resize((44, 16))
        diff = [Image.new('RGBA', (75, 75), color) for color in bg_color]
        atime = 0
        for ra in levelList[5:]:
            _otime = time.time()
            musiclist = mai.total_list.lvList(rating=True)

            if ra in levelList[-3:]:
                bg = ratingdir / '14.png'
                ralist = levelList[-3:]
            else:
                bg = ratingdir / f'{ra}.png'
                ralist = [ra]

            lvlist: Dict[str, List[RaMusic]] = {}
            if len(ralist) != 1:
                for lv in list(reversed(ralist)):
                    lvlist.update(musiclist[lv])
            else:
                lvlist = musiclist[ralist[0]]

            if ra in ['14', '14+', '15']:
                lvtext = 'Level.14 - 15   定数表'
            else:
                lvtext = f'Level.{ra}   定数表'

            lines = 0
            for _ in lvlist:
                musicnum = len(lvlist[_])
                if musicnum == 0:
                    r = 1
                else:
                    remainder = musicnum % 14
                    r = (musicnum // 14) + (1 if remainder else 0)
                lines += r

            if '+' in ra:
                f = 3
            elif ra in ['6', '14', '14+', '15']:
                f = 10
            else:
                f = 7

            linesheight = 85 * lines
            width, height = 1500, 400 + (85 + f * 20) + linesheight
            newbg, bg_x, bg_y = image_scale(height)

            im = Image.new('RGBA', (width, height))
            im.alpha_composite(newbg, (bg_x, bg_y))
            dr = ImageDraw.Draw(im)
            hy = DrawText(dr, HANYI)
            ts = DrawText(dr, TBFONT)
            hy.draw(750, 100, 65, lvtext, (5, 51, 101, 255), 'mm')
            im.alpha_composite(Image.new('RGBA', (1400, 85 + f * 20 + linesheight), (247, 246, 238, 234)), (50, 200))
            dr.rounded_rectangle((50, 200, 1450, 280 + f * 20 + linesheight), 10, outline=(255, 186, 66, 255), width=5)
            dr.rounded_rectangle((50 - 5, 200 - 5, 1450 + 5, 280 + f * 20 + linesheight + 5), 15, outline=(255, 255, 255, 255), width=5)
            dr.rounded_rectangle((50 - 10, 200 - 10, 1450 + 10, 280 + f * 20 + linesheight + 10), 20, outline=(255, 255, 255, 255), width=5)
            im.alpha_composite(Image.open(maimaidir / 'design.png'), (200, height - 165))
            hy.draw(750, height - 115, 28, f'BY @澪度 - MilkBOT', (5, 51, 101, 255), 'mm')
            y = 150
            for lv in lvlist:
                x = 200
                y += 20
                im.alpha_composite(Image.open(maimaidir / 'UI_Chara_Level_S #4824.png').resize((80, 80)), (90, y + 80))
                ts.draw(128, y + 120, 35, lv, anchor='mm')
                for num, music in enumerate(lvlist[lv]):
                    if num % 14 == 0:
                        x = 200
                        y += 85
                    else:
                        x += 85
                    cover = await maiApi.download_music_pictrue(music.id)
                    if int(music.lv) != 3:
                        cover_bg = diff[int(music.lv)]
                        cover_bg.alpha_composite(Image.open(cover).convert('RGBA').resize((65, 65)), (5, 5))
                    else:
                        cover_bg = Image.open(cover).convert('RGBA').resize((75, 75))
                    im.alpha_composite(cover_bg, (x, y))
                    if music.type == 'DX':
                        im.alpha_composite(dx, (x + 31, y))
                if not lvlist[lv]:
                    y += 85

            by = BytesIO()
            im.save(by, 'PNG')
            async with aiofiles.open(bg, 'wb') as f:
                await f.write(by.getbuffer())
            _ntime = int(time.time() - _otime)
            atime += _ntime
            log.info(f'lv.{ra} 定数表更新完成，耗时：{_ntime}s')
        log.info(f'定数表更新完成，共耗时{atime}s')
        return f'定数表更新完成，共耗时{atime}s'
    except Exception as e:
        log.error(traceback.format_exc())
        return f'定数表更新失败，Error: {e}'


async def update_plate_table() -> str:
    """更新完成表"""
    try:
        version = list(_ for _ in plate_to_version.keys())[-1]
        rlv: Dict[str, List[Music]] = {}
        for _ in list(reversed(levelList)):
            rlv[_] = []
        for _v in version:
            _w = 1500
            _n = 10

            if _v == '真':
                ver = list(set(_v for _v in list(plate_to_version.values())[0:2]))
            elif _v == '华' or _v == '華':
                ver = [plate_to_version['熊']]
            elif _v == '星':
                ver = [plate_to_version['宙']]
            elif _v == '祝':
                ver = [plate_to_version['祭']]
            elif _v == '煌':
                ver = [plate_to_version['爽']]
            else:
                ver = [plate_to_version[_v]]

            music = mai.total_list.by_version(ver)
            ralv = copy.deepcopy(rlv)

            for m in music:
                ralv[m.level[3]].append(m)

            lines = 0
            for _ in ralv:
                musicnum = len(ralv[_])
                if musicnum == 0:
                    continue
                else:
                    remainder = musicnum % _n
                    lines += (musicnum // _n) + (1 if remainder else 0)
            linesheight = 115 * lines
            width, height = _w, 850 + linesheight

            newbg, bg_x, bg_y = image_scale(height)

            im = Image.new('RGBA', (width, height))
            im.alpha_composite(newbg, (bg_x, bg_y))
            dr = ImageDraw.Draw(im)
            ts = DrawText(dr, TBFONT)
            im.alpha_composite(Image.new('RGBA', (1400, 230 + linesheight), (247, 246, 238, 234)), (50, 400))
            im.alpha_composite(Image.open(maimaidir / 'progress.png'), (299, 91))
            dr.rounded_rectangle((50, 400, 1450, 630 + linesheight), 10, outline=(255, 186, 66, 255), width=5)
            dr.rounded_rectangle((50 - 5, 400 - 5, 1450 + 5, 630 + linesheight + 5), 15, outline=(255, 255, 255, 255), width=5)
            dr.rounded_rectangle((50 - 10, 400 - 10, 1450 + 10, 630 + linesheight + 10), 20, outline=(255, 255, 255, 255), width=5)
            im.alpha_composite(Image.open(maimaidir / 'design.png'), (200, height - 165))
            y = 350
            for r in ralv:
                if _v in ['霸', '舞']:
                    ralv[r].sort(key=lambda x: x.ds[-1], reverse=True)
                else:
                    ralv[r].sort(key=lambda x: x.ds[3], reverse=True)
                if ralv[r]:
                    y += 15
                    im.alpha_composite(Image.open(maimaidir / 'UI_Chara_Level_S #4824.png'), (80, y + 115))
                    ts.draw(128, y + 164, 35, r, anchor='mm')
                x = 210
                for num, music in enumerate(ralv[r]):
                    if num % _n == 0:
                        x = 210
                        y += 115
                    else:
                        x += 115
                    cover = await maiApi.download_music_pictrue(music.id)
                    im.alpha_composite(Image.open(cover).convert('RGBA').resize((100, 100)), (x, y))

            by = BytesIO()
            im.save(by, 'PNG')
            async with aiofiles.open(platedir / f'{_v}.png', 'wb') as f:
                await f.write(by.getbuffer())
            log.info(f'{_v}代牌子更新完成')
        return f'完成表更新完成'
    except Exception as e:
        log.error(traceback.format_exc())
        return f'完成表更新失败，Error: {e}'