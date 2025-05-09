from io import BytesIO
from pathlib import Path
from typing import Any, List, Optional, Union

import httpx

from .config import coverdir,maimaitoken
from .maimaidx_error import *


class MaimaiAPI:

    MaiAPI = 'https://www.diving-fish.com/api/maimaidxprober'
    MaiCover = 'https://www.diving-fish.com/covers'
    MaiAliasAPI = 'https://api.yuzuchan.moe/maimaidx'
    QQAPI = 'http://q1.qlogo.cn/g'
    
    def __init__(self) -> None:
        """封装Api"""
        self.headers = None
        self.token = None

    def load_token(self) -> None:
        self.token = maimaitoken
        self.headers = {'developer-token': self.token}
    
    async def _request(self, method: str, url: str, **kwargs) -> Any:
        session = httpx.AsyncClient(timeout=30)
        res = await session.request(method, url, **kwargs)

        data = None
        
        if self.MaiAPI in url:
            if res.status_code == 200:
                data = res.json()
            elif res.status_code == 400:
                raise UserNotFoundError
            elif res.status_code == 403:
                raise UserDisabledQueryError
            else:
                raise UnknownError
        elif self.MaiAliasAPI in url:
            if res.status_code == 200:
                data = res.json()['content']
            elif res.status_code == 400:
                raise EnterError
            elif res.status_code == 500:
                raise ServerError
            else:
                raise UnknownError
        elif self.QQAPI in url:
            if res.status_code == 200:
                data = res.content
            else:
                raise
        await session.aclose()
        return data
    
    async def music_data(self):
        """获取曲目数据"""
        return await self._request('GET', self.MaiAPI + '/music_data')
    
    async def chart_stats(self):
        """获取单曲数据"""
        return await self._request('GET', self.MaiAPI + '/chart_stats')
    
    async def query_user(self, project: str, *, qqid: Optional[int] = None, username: Optional[str] = None, version: Optional[List[str]] = None):
        """
        请求用户数据
        
        - `project`: 查询的功能
            - `player`: 查询用户b50
            - `plate`: 按版本查询用户游玩成绩
        - `qqid`: 用户QQ
        - `username`: 查分器用户名
        """
        json = {}
        if qqid:
            json['qq'] = qqid
        if username:
            json['username'] = username
        if version:
            json['version'] = version
        if project == 'player':
            json['b50'] = True
        return await self._request('POST', self.MaiAPI + f'/query/{project}', json=json)
    
    async def query_user_dev(self, *, qqid: Optional[int] = None, username: Optional[str] = None):
        """
        使用开发者接口获取用户数据,请确保拥有和输入了开发者 `token`
        
        - `qqid`: 用户QQ
        - `username`: 查分器用户名
        """
        params = {}
        if qqid:
            params['qq'] = qqid
        if username:
            params['username'] = username
        return await self._request('GET', self.MaiAPI + f'/dev/player/records', headers=self.headers, params=params)
    async def query_user_fc(self, *, qqid: Optional[int] = None, username: Optional[str] = None):
        """
        使用开发者接口获取用户AP数据, 并按照指定格式返回.
        - `qqid`: 用户QQ
        - `username`: 查分器用户名
        """
        params = {}
        if qqid:
            params['qq'] = qqid
        if username:
            params['username'] = username

        # 获取用户的记录数据
        fish_data = await self._request('GET', self.MaiAPI + '/dev/player/records', headers=self.headers, params=params)

    # 删除 records 中 fc 不等于 "ap" 和 "app" 的数据
        if "records" in fish_data:
            filtered_records = [
                record for record in fish_data["records"]
                if record.get("fc") in {"fc", "fcp"}
            ]
        else:
            filtered_records = []

    # 分类 records 数据为 dx 和 sd
        charts = {"dx": [], "sd": []}
        for record in filtered_records:
            chart_type = record.get("type", "").lower()
            if chart_type in charts:
                charts[chart_type].append(record)

    # 将 dx 和 sd 合并为一个数组，并按 ra 排序
        combined_charts = charts["dx"] + charts["sd"]
        sorted_charts = sorted(combined_charts, key=lambda x: x.get("ra", 0), reverse=True)

    # 确保 sd 占前 35 首, dx 占后 15 首
        sd_charts = sorted_charts[:35]
        dx_charts = sorted_charts[35:50]  # dx 是后15首，即从第36到第50首

    # 更新 charts 字典
        charts["sd"] = sd_charts
        charts["dx"] = dx_charts

    # 计算新的 rating 值 (sd 和 dx 的 ra 总和)
        sd_rating_sum = sum(chart.get("ra", 0) for chart in charts["sd"])
        dx_rating_sum = sum(chart.get("ra", 0) for chart in charts["dx"])
        total_rating = sd_rating_sum + dx_rating_sum

    # 确保 username 为字符串
        username_str = str(username) if username else "AP50"

    # 组织返回的数据格式
        result = {
            "additional_rating": fish_data.get("additional_rating"),
            "charts": charts,
            "nickname": fish_data.get("nickname"),
            "plate": fish_data.get("plate"),
            "rating": total_rating,  # 使用新的总分
            "user_general_data": None,  # 默认值为 None
            "username": username_str,  # 确保 username 为字符串
        }

    # 如果需要, 调用 query_user 填充 user_general_data
        if result["user_general_data"] is None:
            user_data = await self.query_user(project="player", qqid=qqid, username=username_str)
            result["user_general_data"] = user_data

        return result

    async def query_user_high(self, *, qqid: Optional[int] = None, username: Optional[str] = None):
        """
        使用开发者接口获取用户高分曲数据, 并按照指定格式返回.
        - `qqid`: 用户QQ
        - `username`: 查分器用户名
        """
        params = {}
        if qqid:
            params['qq'] = qqid
        if username:
            params['username'] = username

        # 获取用户的记录数据
        fish_data = await self._request('GET', self.MaiAPI + '/dev/player/records', headers=self.headers, params=params)

        # 仅筛选 achievements 在指定区间内的数据
        if "records" in fish_data:
            filtered_records = [
                record for record in fish_data["records"]
                if record.get("achievements", 0) > 100.8
            ]
        else:
            filtered_records = []

        # 分类 records 数据为 dx 和 sd
        charts = {"dx": [], "sd": []}
        for record in filtered_records:
            chart_type = record.get("type", "").lower()
            if chart_type in charts:
                charts[chart_type].append(record)

    # 将 dx 和 sd 合并为一个数组，并按 ra 排序
        combined_charts = charts["dx"] + charts["sd"]
        sorted_charts = sorted(combined_charts, key=lambda x: x.get("ra", 0), reverse=True)

    # 确保 sd 占前 35 首, dx 占后 15 首
        sd_charts = sorted_charts[:35]
        dx_charts = sorted_charts[35:50]  # dx 是后15首，即从第36到第50首

    # 更新 charts 字典
        charts["sd"] = sd_charts
        charts["dx"] = dx_charts

    # 计算新的 rating 值 (sd 和 dx 的 ra 总和)
        sd_rating_sum = sum(chart.get("ra", 0) for chart in charts["sd"])
        dx_rating_sum = sum(chart.get("ra", 0) for chart in charts["dx"])
        total_rating = sd_rating_sum + dx_rating_sum

    # 确保 username 为字符串
        username_str = str(username) if username else "寸50"

    # 组织返回的数据格式
        result = {
            "additional_rating": fish_data.get("additional_rating"),
            "charts": charts,
            "nickname": fish_data.get("nickname"),
            "plate": fish_data.get("plate"),
            "rating": total_rating,  # 使用新的总分
            "user_general_data": None,  # 默认值为 None
            "username": username_str,  # 确保 username 为字符串
        }

    # 如果需要, 调用 query_user 填充 user_general_data
        if result["user_general_data"] is None:
            user_data = await self.query_user(project="player", qqid=qqid, username=username_str)
            result["user_general_data"] = user_data

        return result

    async def query_user_theoretical(self, *, qqid: Optional[int] = None, username: Optional[str] = None):
        """
    使用开发者接口获取用户理论值数据, 并按照指定格式返回.
    - `qqid`: 用户QQ
    - `username`: 查分器用户名
    """
        params = {}
        if qqid:
            params['qq'] = qqid
        if username:
            params['username'] = username

    # 获取用户的记录数据
        fish_data = await self._request('GET', self.MaiAPI + '/dev/player/records', headers=self.headers, params=params)

    # 删除 records 中 fc 不等于 "ap" 和 "app" 的数据
        if "records" in fish_data:
            filtered_records = [
                record for record in fish_data["records"]
                if record.get("fc") in {"app"}
            ]
        else:
            filtered_records = []

    # 分类 records 数据为 dx 和 sd
        charts = {"dx": [], "sd": []}
        for record in filtered_records:
            chart_type = record.get("type", "").lower()
            if chart_type in charts:
                charts[chart_type].append(record)

    # 将 dx 和 sd 合并为一个数组，并按 ra 排序
        combined_charts = charts["dx"] + charts["sd"]
        sorted_charts = sorted(combined_charts, key=lambda x: x.get("ra", 0), reverse=True)

    # 确保 sd 占前 35 首, dx 占后 15 首
        sd_charts = sorted_charts[:35]
        dx_charts = sorted_charts[35:50]  # dx 是后15首，即从第36到第50首

    # 更新 charts 字典
        charts["sd"] = sd_charts
        charts["dx"] = dx_charts

    # 计算新的 rating 值 (sd 和 dx 的 ra 总和)
        sd_rating_sum = sum(chart.get("ra", 0) for chart in charts["sd"])
        dx_rating_sum = sum(chart.get("ra", 0) for chart in charts["dx"])
        total_rating = sd_rating_sum + dx_rating_sum

    # 确保 username 为字符串
        username_str = str(username) if username else "AP50"

    # 组织返回的数据格式
        result = {
            "additional_rating": fish_data.get("additional_rating"),
            "charts": charts,
            "nickname": fish_data.get("nickname"),
            "plate": fish_data.get("plate"),
            "rating": total_rating,  # 使用新的总分
            "user_general_data": None,  # 默认值为 None
            "username": username_str,  # 确保 username 为字符串
        }

    # 如果需要, 调用 query_user 填充 user_general_data
        if result["user_general_data"] is None:
            user_data = await self.query_user(project="player", qqid=qqid, username=username_str)
            result["user_general_data"] = user_data

        return result
    async def query_user_ap(self, *, qqid: Optional[int] = None, username: Optional[str] = None):
        """
    使用开发者接口获取用户AP数据, 并按照指定格式返回.
    - `qqid`: 用户QQ
    - `username`: 查分器用户名
    """
        params = {}
        if qqid:
            params['qq'] = qqid
        if username:
            params['username'] = username

    # 获取用户的记录数据
        fish_data = await self._request('GET', self.MaiAPI + '/dev/player/records', headers=self.headers, params=params)

    # 删除 records 中 fc 不等于 "ap" 和 "app" 的数据
        if "records" in fish_data:
            filtered_records = [
                record for record in fish_data["records"]
                if record.get("fc") in {"ap", "app"}
            ]
        else:
            filtered_records = []

    # 分类 records 数据为 dx 和 sd
        charts = {"dx": [], "sd": []}
        for record in filtered_records:
            chart_type = record.get("type", "").lower()
            if chart_type in charts:
                charts[chart_type].append(record)

    # 将 dx 和 sd 合并为一个数组，并按 ra 排序
        combined_charts = charts["dx"] + charts["sd"]
        sorted_charts = sorted(combined_charts, key=lambda x: x.get("ra", 0), reverse=True)

    # 确保 sd 占前 35 首, dx 占后 15 首
        sd_charts = sorted_charts[:35]
        dx_charts = sorted_charts[35:50]  # dx 是后15首，即从第36到第50首

    # 更新 charts 字典
        charts["sd"] = sd_charts
        charts["dx"] = dx_charts

    # 计算新的 rating 值 (sd 和 dx 的 ra 总和)
        sd_rating_sum = sum(chart.get("ra", 0) for chart in charts["sd"])
        dx_rating_sum = sum(chart.get("ra", 0) for chart in charts["dx"])
        total_rating = sd_rating_sum + dx_rating_sum

    # 确保 username 为字符串
        username_str = str(username) if username else "AP50"

    # 组织返回的数据格式
        result = {
            "additional_rating": fish_data.get("additional_rating"),
            "charts": charts,
            "nickname": fish_data.get("nickname"),
            "plate": fish_data.get("plate"),
            "rating": total_rating,  # 使用新的总分
            "user_general_data": None,  # 默认值为 None
            "username": username_str,  # 确保 username 为字符串
        }

    # 如果需要, 调用 query_user 填充 user_general_data
        if result["user_general_data"] is None:
            user_data = await self.query_user(project="player", qqid=qqid, username=username_str)
            result["user_general_data"] = user_data

        return result
    async def query_user_cum(self, *, qqid: Optional[int] = None, username: Optional[str] = None):
        """
    使用开发者接口获取用户寸歌数据, 并按照指定格式返回.
    - `qqid`: 用户QQ
    - `username`: 查分器用户名
    """
        params = {}
        if qqid:
            params['qq'] = qqid
        if username:
            params['username'] = username

    # 获取用户的记录数据
        fish_data = await self._request('GET', self.MaiAPI + '/dev/player/records', headers=self.headers, params=params)

    # 仅筛选 achievements 在指定区间内的数据
        if "records" in fish_data:
            filtered_records = [
                record for record in fish_data["records"]
                if (99.9 < record.get("achievements", 0) < 100)  # 筛选 achievements 在 99.8 到 99.9 区间的记录
                or (100.49 < record.get("achievements", 0) < 100.5)  # 筛选 achievements 在 100.45 到 100.49 区间的记录
            ]
        else:
            filtered_records = []

    # 分类 records 数据为 dx 和 sd
        charts = {"dx": [], "sd": []}
        for record in filtered_records:
            chart_type = record.get("type", "").lower()
            if chart_type in charts:
                charts[chart_type].append(record)

    # 将 dx 和 sd 合并为一个数组，并按 ra 排序
        combined_charts = charts["dx"] + charts["sd"]
        sorted_charts = sorted(combined_charts, key=lambda x: x.get("ra", 0), reverse=True)

    # 确保 sd 占前 35 首, dx 占后 15 首
        sd_charts = sorted_charts[:35]
        dx_charts = sorted_charts[35:50]  # dx 是后15首，即从第36到第50首

    # 更新 charts 字典
        charts["sd"] = sd_charts
        charts["dx"] = dx_charts

    # 计算新的 rating 值 (sd 和 dx 的 ra 总和)
        sd_rating_sum = sum(chart.get("ra", 0) for chart in charts["sd"])
        dx_rating_sum = sum(chart.get("ra", 0) for chart in charts["dx"])
        total_rating = sd_rating_sum + dx_rating_sum

    # 确保 username 为字符串
        username_str = str(username) if username else "寸50"

    # 组织返回的数据格式
        result = {
            "additional_rating": fish_data.get("additional_rating"),
            "charts": charts,
            "nickname": fish_data.get("nickname"),
            "plate": fish_data.get("plate"),
            "rating": total_rating,  # 使用新的总分
            "user_general_data": None,  # 默认值为 None
            "username": username_str,  # 确保 username 为字符串
        }

    # 如果需要, 调用 query_user 填充 user_general_data
        if result["user_general_data"] is None:
            user_data = await self.query_user(project="player", qqid=qqid, username=username_str)
            result["user_general_data"] = user_data

        return result
    async def query_user_bypass(self, *, qqid: Optional[int] = None, username: Optional[str] = None):
        """
    使用开发者接口获取用户寸歌数据, 并按照指定格式返回.
    - `qqid`: 用户QQ
    - `username`: 查分器用户名
    """
        params = {}
        if qqid:
            params['qq'] = qqid
        if username:
            params['username'] = username

    # 获取用户的记录数据
        fish_data = await self._request('GET', self.MaiAPI + '/dev/player/records', headers=self.headers, params=params)

    # 仅筛选 achievements 在指定区间内的数据
        if "records" in fish_data:
            filtered_records = [
                record for record in fish_data["records"]
                if (79 <= record.get("achievements", 0) <= 96)  # 筛选 achievements 在 99.8 到 99.9 区间的记录
            ]
        else:
            filtered_records = []

    # 分类 records 数据为 dx 和 sd
        charts = {"dx": [], "sd": []}
        for record in filtered_records:
            chart_type = record.get("type", "").lower()
            if chart_type in charts:
                charts[chart_type].append(record)

    # 将 dx 和 sd 合并为一个数组，并按 ra 排序
        combined_charts = charts["dx"] + charts["sd"]
        sorted_charts = sorted(combined_charts, key=lambda x: x.get("ra", 0), reverse=True)

    # 确保 sd 占前 35 首, dx 占后 15 首
        sd_charts = sorted_charts[:35]
        dx_charts = sorted_charts[35:50]  # dx 是后15首，即从第36到第50首

    # 更新 charts 字典
        charts["sd"] = sd_charts
        charts["dx"] = dx_charts

    # 计算新的 rating 值 (sd 和 dx 的 ra 总和)
        sd_rating_sum = sum(chart.get("ra", 0) for chart in charts["sd"])
        dx_rating_sum = sum(chart.get("ra", 0) for chart in charts["dx"])
        total_rating = sd_rating_sum + dx_rating_sum

    # 确保 username 为字符串
        username_str = str(username) if username else "寸50"

    # 组织返回的数据格式
        result = {
            "additional_rating": fish_data.get("additional_rating"),
            "charts": charts,
            "nickname": fish_data.get("nickname"),
            "plate": fish_data.get("plate"),
            "rating": total_rating,  # 使用新的总分
            "user_general_data": None,  # 默认值为 None
            "username": username_str,  # 确保 username 为字符串
        }

    # 如果需要, 调用 query_user 填充 user_general_data
        if result["user_general_data"] is None:
            user_data = await self.query_user(project="player", qqid=qqid, username=username_str)
            result["user_general_data"] = user_data

        return result

    async def query_user_dev2(self, *, qqid: Optional[int] = None, username: Optional[str] = None, music_id: Union[str, List[Union[int, str]]]):
        """
        使用开发者接口获取用户指定曲目数据,请确保拥有和输入了开发者 `token`

        - `qqid`: 用户QQ
        - `username`: 查分器用户名
        - `music_id`: 曲目id,可以为单个ID或者列表
        """
        json = {}
        if qqid:
            json['qq'] = qqid
        if username:
            json['username'] = username
        json['music_id'] = music_id
        print(f"请求api:{self.MaiAPI},header头:{self.headers}，原始数据:{json}")
        return await self._request('POST', self.MaiAPI + f'/dev/player/record', headers=self.headers, json=json)

    async def rating_ranking(self):
        """获取查分器排行榜"""
        return await self._request('GET', self.MaiAPI + f'/rating_ranking')
        
    async def get_alias(self):
        """获取所有别名"""
        return await self._request('GET', self.MaiAliasAPI + '/maimaidxalias')
    
    async def get_songs(self, name: str):
        """使用别名查询曲目"""
        return await self._request('GET', self.MaiAliasAPI + '/getsongs', params={'name': name})
    
    async def get_songs_alias(self, song_id: int):
        """使用曲目 `id` 查询别名"""
        return await self._request('GET', self.MaiAliasAPI + '/getsongsalias', params={'song_id': song_id})
    
    async def get_alias_status(self):
        """获取当前正在进行的别名投票"""
        return await self._request('GET', self.MaiAliasAPI + '/getaliasstatus')
    
    async def get_alias_end(self):
        """获取五分钟内结束的别名投票"""
        return await self._request('GET', self.MaiAliasAPI + '/getaliasend')
    
    async def transfer_music(self):
        """中转查分器曲目数据"""
        return await self._request('GET', self.MaiAliasAPI + '/maimaidxmusic')
    
    async def transfer_chart(self):
        """中转查分器单曲数据"""
        return await self._request('GET', self.MaiAliasAPI + '/maimaidxchartstats')
    
    async def post_alias(self, id: int, aliasname: str, user_id: int):
        """
        提交别名申请
        
        - `id`: 曲目 `id`
        - `aliasname`: 别名
        - `user_id`: 提交的用户
        """
        json = {
            'SongID': id,
            'ApplyAlias': aliasname,
            'ApplyUID': user_id
        }
        return await self._request('POST', self.MaiAliasAPI + '/applyalias', json=json)
    
    async def post_agree_user(self, tag: str, user_id: int):
        """
        提交同意投票
        
        - `tag`: 标签
        - `user_id`: 同意投票的用户
        """
        json = {
            'Tag': tag,
            'AgreeUser': user_id
        }
        return await self._request('POST', self.MaiAliasAPI + '/agreeuser', json=json)

    async def download_music_pictrue(self, song_id: Union[int, str]) -> Union[Path, BytesIO]:
        try:
            if (file := coverdir / f'{song_id}.png').exists():
                return file
            song_id = int(song_id)
            if song_id > 100000:
                song_id -= 100000
                if (file := coverdir / f'{song_id}.png').exists():
                    return file
            if 1000 < song_id < 10000 or 10000 < song_id <= 11000:
                for _id in [song_id + 10000, song_id - 10000]:
                    if (file := coverdir / f'{_id}.png').exists():
                        return file
            pic = await self._request('GET', self.MaiCover + f'/{song_id:05d}.png')
            return BytesIO(pic)
        except CoverError:
            return coverdir / '11000.png'
        except Exception:
            return coverdir / '11000.png'

    async def qqlogo(self, qqid: int) -> bytes:
        params = {
            'b': 'qq',
            'nk': qqid,
            's': 100
        }
        return await self._request('GET', self.QQAPI, params=params)


maiApi = MaimaiAPI()
maiApi.load_token()