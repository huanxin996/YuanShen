import math
import traceback
import httpx
import random
from io import BytesIO
from typing import Tuple, Union, overload

from loguru import logger as log
from PIL import Image, ImageDraw

from .config import *
from .image import DrawText
from .maimaidx_api_data import maiApi
from .maimaidx_error import *
from .maimaidx_model import ChartInfo, PlayInfoDefault, PlayInfoDev, UserInfo
from .maimaidx_music import mai


class Draw:

    basic = Image.open(maimaidir / 'b50_score_basic.png')
    advanced = Image.open(maimaidir / 'b50_score_advanced.png')
    expert = Image.open(maimaidir / 'b50_score_expert.png')
    master = Image.open(maimaidir / 'b50_score_master.png')
    remaster = Image.open(maimaidir / 'b50_score_remaster.png')
    title_bg = Image.open(maimaidir / 'title2.png').resize((600, 120))
    design_bg = Image.open(maimaidir / 'design.png').resize((1320, 120))
    _diff = [basic, advanced, expert, master, remaster]

    def __init__(self, image: Image.Image = None) -> None:
        self._im = image
        dr = ImageDraw.Draw(self._im)
        self._mr = DrawText(dr, MEIRYO)
        self._sy = DrawText(dr, SIYUAN)
        self._tb = DrawText(dr, TBFONT)
        self.use_abstract_cover = False  # 新增封面获取方式标志

    async def get_cover_image(self, song_id: int) -> Image.Image:
        """获取封面图片,优先使用本地文件"""
        if self.use_abstract_cover:
            cover_path = maimaidir / 'abstract' / f'{song_id}.png'
            if cover_path.exists():
                return Image.open(cover_path)
            
            try:
                # 下载并保存封面
                image_data = await maiApi.download_music_pictrue(song_id)
                cover_path.parent.mkdir(parents=True, exist_ok=True)
                
                if isinstance(image_data, BytesIO):
                    cover_bytes = image_data.getvalue()
                else:
                    cover_bytes = image_data
                
                with open(cover_path, 'wb') as f:
                    f.write(cover_bytes)
                
                return Image.open(cover_path)
            except Exception as e:
                log.error(f"Error downloading abstract cover image for song_id {song_id}: {e}")
                # 如果下载abstract封面失败,尝试下载原始封面
                try:
                    original_cover_path = await maiApi.download_music_pictrue(song_id)
                    return Image.open(original_cover_path)
                except Exception as e:
                    log.error(f"Error downloading original cover image for song_id {song_id}: {e}")
                    return Image.new('RGBA', (135, 135), (255, 255, 255, 0))  # 返回一个空白图片
        else:
            original_cover_path = await maiApi.download_music_pictrue(song_id)
            return Image.open(original_cover_path)

    async def whiledraw(self, data: Union[List[ChartInfo], List[PlayInfoDefault], List[PlayInfoDev]], best: bool, height: int = 0) -> None:
        TEXT_COLOR = [(235, 235, 235, 255), (235, 235, 235, 255), (255, 255, 255, 255), (235, 235, 235, 255), (85, 80, 120, 255)]
        dy = 170
        if data and isinstance(data[0], ChartInfo):
            y = 430 if best else 1700
        else:
            y = height

        x = 70
        for num, info in enumerate(data):
            if num % 5 == 0:
                x = 70
                y += dy if num != 0 else 0
            else:
                x += 416

            # 获取封面(使用修改后的方法)
            cover = (await self.get_cover_image(info.song_id)).resize((135, 135))
            version = Image.open(maimaidir / f'{info.type.upper()}.png').resize((55, 19))
            rate_img = f'UI_TTR_Rank_{score_Rank_l[info.rate]}.png' if info.rate.islower() else f'UI_TTR_Rank_{info.rate}.png'
            rate = Image.open(maimaidir / rate_img).resize((95, 44))

            self._im.alpha_composite(self._diff[info.level_index], (x, y))
            self._im.alpha_composite(cover, (x + 5, y + 5))
            self._im.alpha_composite(version, (x + 80, y + 140))
            self._im.alpha_composite(rate, (x + 150, y + 98))

            # 添加FC/FS图标
            if info.fc:
                fc = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fcl[info.fc]}.png').resize((45, 45))
                self._im.alpha_composite(fc, (x + 246, y + 99))
            if info.fs:
                fs = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fsl[info.fs]}.png').resize((45, 45))
                self._im.alpha_composite(fs, (x + 291, y + 99))

            # 添加DX分标识
            if hasattr(mai, 'total_list') and hasattr(mai.total_list, 'by_id'):
                dxscore = sum(mai.total_list.by_id(str(info.song_id)).charts[info.level_index].notes) * 3
            else:
                log.error(f"'mai' 对象没有 'total_list' 属性或 'by_id' 方法，无法计算 dxscore,尝试获取 dxscore")
                try:
                    await mai.get_music()
                    dxscore = sum(mai.total_list.by_id(str(info.song_id)).charts[info.level_index].notes) * 3
                except Exception as e:
                    log.error(f"获取 dxscore 失败: {e}")
                    dxscore = 0
            dxnum = dxScore(info.dxScore / dxscore * 100)
            if dxnum:
                self._im.alpha_composite(Image.open(maimaidir / f'UI_GAM_Gauge_DXScoreIcon_0{dxnum}.png'),
                                        (x + 335, y + 102))

            # 绘制文本信息
            self._tb.draw(x + 40, y + 146, 18, info.song_id, TEXT_COLOR[info.level_index], anchor='mm')
            title = info.title
            if coloumWidth(title) > 18:
                title = changeColumnWidth(title, 15) + '...'
            self._sy.draw(x + 163, y + 20, 20, title, TEXT_COLOR[info.level_index], anchor='lm')
            self._tb.draw(x + 163, y + 50, 32, f'{info.achievements:.4f}%', TEXT_COLOR[info.level_index], anchor='lm')
            self._tb.draw(x + 320, y + 82, 20, f'DX分:{info.dxScore}', TEXT_COLOR[info.level_index], anchor='mm')
            self._tb.draw(x + 163, y + 82, 22, f'{info.ds}({info.ra})', TEXT_COLOR[info.level_index], anchor='lm')


class DrawBest(Draw):

    def __init__(
        self,
        UserInfo: UserInfo,
        qqId: Optional[Union[int, str]] = None,
        modify: Optional[bool] = None,
        use_abstract_cover: bool = False
    ) -> None:
        random_bg = random.choice([f'b50_bg_{i}.png' for i in range(1, 4)])
        super().__init__(Image.open(maimaidir / random_bg).convert('RGBA'))
        self.userName = UserInfo.nickname
        self.plate = UserInfo.plate
        self.addRating = UserInfo.additional_rating
        self.Rating = UserInfo.rating
        self.sdBest = UserInfo.charts.sd
        self.dxBest = UserInfo.charts.dx
        self.modify = modify if modify is not None else False
        self.qqId = qqId
        self.use_abstract_cover = use_abstract_cover

    def _findRaPic(self) -> str:
        if self.Rating < 1000:
            num = '01'
        elif self.Rating < 2000:
            num = '02'
        elif self.Rating < 4000:
            num = '03'
        elif self.Rating < 7000:
            num = '04'
        elif self.Rating < 10000:
            num = '05'
        elif self.Rating < 12000:
            num = '06'
        elif self.Rating < 13000:
            num = '07'
        elif self.Rating < 14000:
            num = '08'
        elif self.Rating < 14500:
            num = '09'
        elif self.Rating < 15000:
            num = '10'
        else:
            num = '11'
        return f'UI_CMN_DXRating_{num}.png'

    def _findMatchLevel(self) -> str:
        if self.addRating <= 10:
            num = f'{self.addRating:02d}'
        else:
            num = f'{self.addRating + 1:02d}'
        return f'UI_DNM_DaniPlate_{num}.png'


    async def draw(self) -> Image.Image:
        dx_rating = Image.open(maimaidir / self._findRaPic()).resize((300, 59))
        Name = Image.open(maimaidir / 'Name.png')
        MatchLevel = Image.open(maimaidir / self._findMatchLevel()).resize((134, 55))
        ClassLevel = Image.open(maimaidir / 'UI_FBR_Class_00.png').resize((144, 87))
        rating = Image.open(maimaidir / 'UI_CMN_Shougou_Rainbow.png').resize((454, 50))
        if self.plate:
            plate = Image.open(platedir / f'{self.plate}.png').resize((1420, 230))
        else:
            #random_plate = random.choice([f'UI_Plate_{i}.png' for i in range(1, 1)])
            plate = Image.open(maimaidir / f'UI_Plate_1.png').resize((1420, 230))
        self._im.alpha_composite(plate, (390, 105))
        self._im.alpha_composite(dx_rating, (405, 122))
        Rating = f'{self.Rating:05d}'
        for n, i in enumerate(Rating):
            self._im.alpha_composite(Image.open(maimaidir / f'UI_NUM_Drating_{i}.png').resize((28, 34)), (545 + 23 * n, 137))
        self._im.alpha_composite(Name, (405, 198))
        self._im.alpha_composite(MatchLevel, (720, 205))
        self._im.alpha_composite(ClassLevel, (711, 105))
        self._im.alpha_composite(rating, (405, 275))

        self._sy.draw(420, 232, 40, self.userName, (0, 0, 0, 255), 'lm')
        sdrating, dxrating = sum([_.ra for _ in self.sdBest]), sum([_.ra for _ in self.dxBest])
        self._tb.draw(632, 295, 28, f'B35: {sdrating} + B15: {dxrating} = {self.Rating}', (0, 0, 0, 255), 'mm', 3, (235, 235, 235, 255))
        if self.modify:
            recommendation_text = await fetch_b50_recommendation(self.qqId)
        else:
            recommendation_text = "Powered BY @澪度 - MilkBOT\nAP/FC50计算方式:筛选出条件曲目后重新计算Rating 忽略新旧曲\n牛逼50/越级50则筛选出成绩在指定区间乐曲"
        self._mr.draw(80, 2300, 30, recommendation_text, (0, 0, 0, 255), 'lm', 3, (235, 235, 235, 255))

        await self.whiledraw(self.sdBest, True)
        await self.whiledraw(self.dxBest, False)

        return self._im.resize((1760, 1920))


def dxScore(dx: int) -> int:
    """
    返回值为 `Tuple`: `(星星种类,数量)`
    """
    if dx <= 85:
        result = 0
    elif dx <= 90:
        result = 1
    elif dx <= 93:
        result = 2
    elif dx <= 95:
        result = 3
    elif dx <= 97:
        result = 4
    else:
        result = 5
    return result


def getCharWidth(o) -> int:
    widths = [
        (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
        (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), (8426, 0), (9000, 1), (9002, 2), (11021, 1),
        (12350, 2), (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1),
        (64106, 2), (65039, 1), (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
        (120831, 1), (262141, 2), (1114109, 1),
    ]
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1


def coloumWidth(s: str) -> int:
    res = 0
    for ch in s:
        res += getCharWidth(ord(ch))
    return res


def changeColumnWidth(s: str, len: int) -> str:
    res = 0
    sList = []
    for ch in s:
        res += getCharWidth(ord(ch))
        if res <= len:
            sList.append(ch)
    return ''.join(sList)


@overload
def computeRa(ds: float, achievement: float) -> int:
    """
    - `ds`: 定数
    - `achievement`: 成绩
    """
@overload
def computeRa(ds: float, achievement: float, *, onlyrate: bool = False) -> str:
    """
    - `ds`: 定数
    - `achievement`: 成绩
    - `onlyrate`: 返回评价
    """
@overload
def computeRa(ds: float, achievement: float, *, israte: bool = False) -> Tuple[int, str]:
    """
    - `ds`: 定数
    - `achievement`: 成绩
    - `israte`: 返回元组 (底分, 评价)
    """
def computeRa(ds: float, achievement: float, *, onlyrate: bool = False, israte: bool = False) -> Union[int, Tuple[int, str]]:
    if achievement < 50:
        baseRa = 7.0
        rate = 'd'
    elif achievement < 60:
        baseRa = 8.0
        rate = 'c'
    elif achievement < 70:
        baseRa = 9.6
        rate = 'b'
    elif achievement < 75:
        baseRa = 11.2
        rate = 'bb'
    elif achievement < 80:
        baseRa = 12.0
        rate = 'bbb'
    elif achievement < 90:
        baseRa = 13.6
        rate = 'a'
    elif achievement < 94:
        baseRa = 15.2
        rate = 'aa'
    elif achievement < 97:
        baseRa = 16.8
        rate = 'aaa'
    elif achievement < 98:
        baseRa = 20.0
        rate = 's'
    elif achievement < 99:
        baseRa = 20.3
        rate = 'sp'
    elif achievement < 99.5:
        baseRa = 20.8
        rate = 'ss'
    elif achievement < 100:
        baseRa = 21.1
        rate = 'ssp'
    elif achievement < 100.5:
        baseRa = 21.6
        rate = 'sss'
    else:
        baseRa = 22.4
        rate = 'sssp'

    if israte:
        data = (math.floor(ds * (min(100.5, achievement) / 100) * baseRa), rate)
    elif onlyrate:
        data = rate
    else:
        data = math.floor(ds * (min(100.5, achievement) / 100) * baseRa)

    return data

def generateAchievementList(ds: float):
    _achievementList = []
    for index, acc in enumerate(achievementList):
        if index == len(achievementList) - 1:
            continue
        _achievementList.append(acc)
        c_acc = (computeRa(ds, achievementList[index]) + 1) / ds / BaseRaSpp[index + 1] * 100
        c_acc = math.ceil(c_acc * 10000) / 10000
        while c_acc < achievementList[index + 1]:
            _achievementList.append(c_acc)
            c_acc = (computeRa(ds, c_acc + 0.0001) + 1) / ds / BaseRaSpp[index + 1] * 100
            c_acc = math.ceil(c_acc * 10000) / 10000
    _achievementList.append(100.5)
    return _achievementList

async def generate_abstract(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[str,Image.Image]:
    try:
        if (username):
            qqid = None
        obj = await maiApi.query_user('player', qqid=qqid, username=username)
        mai_info = UserInfo(**obj)
        # 创建DrawBest实例时启用abstract封面模式
        draw_best = DrawBest(mai_info, qqid, True, use_abstract_cover=True)
        
        pic = await draw_best.draw()
        return pic
    except UserNotFoundError as e:
        raise UserNotFoundError(f"用户未找到: {e}")
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f"用户查询被禁用: {e}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise RuntimeError(f"遇到了无法处理的错误... {type(e)}") from e

async def generate(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[str,Image.Image]:
    try:
        if username:
            qqid = None
        obj = await maiApi.query_user('player', qqid=qqid, username=username)
        mai_info = UserInfo(**obj)
        draw_best = DrawBest(mai_info, qqid, True)
        pic = await draw_best.draw()
        return pic
    except UserNotFoundError as e:
        raise UserNotFoundError(f"用户未找到: {e}")
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f"用户查询被禁用: {e}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise RuntimeError(f"遇到了无法处理的错误... {type(e)}") from e

async def generate_cum(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[str,Image.Image]:
    try:
        if (username):
            qqid = None
        obj = await maiApi.query_user_cum(qqid=qqid, username=username)
        mai_info = UserInfo(**obj)
        draw_best = DrawBest(mai_info, qqid)
        
        pic = await draw_best.draw()
        return pic
    except UserNotFoundError as e:
        raise UserNotFoundError(f"用户未找到: {e}")
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f"用户查询被禁用: {e}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise RuntimeError(f"遇到了无法处理的错误... {type(e)}") from e


async def generate_ap(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[str,Image.Image]:
    try:
        if (username):
            qqid = None
        obj = await maiApi.query_user_ap(qqid=qqid, username=username)
        mai_info = UserInfo(**obj)
        draw_best = DrawBest(mai_info, qqid)
        
        pic = await draw_best.draw()
        return pic
    except UserNotFoundError as e:
        raise UserNotFoundError(f"用户未找到: {e}")
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f"用户查询被禁用: {e}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise RuntimeError(f"遇到了无法处理的错误... {type(e)}") from e

async def generate_fc(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[str,Image.Image]:
    try:
        if (username):
            qqid = None
        obj = await maiApi.query_user_fc(qqid=qqid, username=username)
        mai_info = UserInfo(**obj)
        draw_best = DrawBest(mai_info, qqid)
        
        pic = await draw_best.draw()
        return pic
    except UserNotFoundError as e:
        raise UserNotFoundError(f"用户未找到: {e}")
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f"用户查询被禁用: {e}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise RuntimeError(f"遇到了无法处理的错误... {type(e)}") from e

async def generate_bypass(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[str,Image.Image]:
    try:
        if (username):
            qqid = None
        obj = await maiApi.query_user_bypass(qqid=qqid, username=username)
        mai_info = UserInfo(**obj)
        draw_best = DrawBest(mai_info, qqid)
        
        pic = await draw_best.draw()
        return pic
    except UserNotFoundError as e:
        raise UserNotFoundError(f"用户未找到: {e}")
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f"用户查询被禁用: {e}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise RuntimeError(f"遇到了无法处理的错误... {type(e)}") from e


async def generate_high(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[str,Image.Image]:
    try:
        if (username):
            qqid = None
        obj = await maiApi.query_user_high(qqid=qqid, username=username)
        mai_info = UserInfo(**obj)
        draw_best = DrawBest(mai_info, qqid)
        
        pic = await draw_best.draw()
        return pic
    except UserNotFoundError as e:
        raise UserNotFoundError(f"用户未找到: {e}")
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f"用户查询被禁用: {e}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise RuntimeError(f"遇到了无法处理的错误... {type(e)}") from e

async def generate_theoretical(qqid: Optional[int] = None, username: Optional[str] = None) -> Union[str,Image.Image]:
    try:
        if (username):
            qqid = None
        obj = await maiApi.query_user_theoretical(qqid=qqid, username=username)
        mai_info = UserInfo(**obj)
        draw_best = DrawBest(mai_info, qqid)
        
        pic = await draw_best.draw()
        return pic
    except UserNotFoundError as e:
        raise UserNotFoundError(f"用户未找到: {e}")
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f"用户查询被禁用: {e}")
    except Exception as e:
        log.error(traceback.format_exc())
        raise RuntimeError(f"遇到了无法处理的错误... {type(e)}") from e



async def fetch_b50_recommendation(qqid: int) -> str:
    try:
        # 创建httpx客户端
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://www.diving-fish.com/api/maimaidxprober/query/player',
                json={
                    'qq': qqid,
                    'b50': True
                },
                headers={
                    'Content-Type': 'application/json',
                    'Developer-Token': '9lYvOLzHZwu5BTAyeVhNbFgn4psMSXcC'
                }
            )

            data = response.json()  # 解析JSON响应
            dx = data['charts']['dx'][-1]
            sd = data['charts']['sd'][-1]

            if not dx or not sd:
                return "B50数据不完整(水鱼查分器中没有B35/B15数据)无法计算推分建议"

            lastradx = dx['ra']
            lastrasd = sd['ra']

            # 计算b35和b15的最后定数
            b35_last = round(((lastrasd + 1) / 22.512) * 10) / 10
            b15_last = round(((lastradx + 1) / 22.512) * 10) / 10

            # 生成推分建议文本(简化版)
            msg = f"""
Rating 推分建议:
B35: SSS+ {'' if (b35_last + 0.1) > 15 else (b35_last + 0.1):.1f} -- SSS {'' if (b35_last + 0.6) > 15 else (b35_last + 0.6):.1f} -- SS+ {'' if (b35_last + 1.1) > 15 else (b35_last + 1.1):.1f}
B15: SSS+ {'' if (b15_last + 0.1) > 15 else (b15_last + 0.1):.1f} -- SSS {'' if (b15_last + 0.6) > 15 else (b15_last + 0.6):.1f} -- SS+ {'' if (b15_last + 1.1) > 15 else (b15_last + 1.1):.1f}
Powered BY @澪度 - MilkBOT
            """.strip()

            return msg

    except Exception as e:
        return f"获取推分建议数据时出现问题 无法计算Rating推分建议"
