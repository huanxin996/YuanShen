import copy
from .config import maimaitoken
from .maimaidx_best_50 import *
from .maimaidx_model import *
from .maimaidx_music import mai


def newbestscore(song_id: str, lv: int, value: int, bestlist: List[ChartInfo]) -> int:
    for v in bestlist:
        if song_id == str(v.song_id) and lv == v.level_index:
            if value >= v.ra:
                return value - v.ra
            else:
                return 0
    return value - bestlist[-1].ra


async def draw_music_info(music: Music, qqid: Optional[int] = None, user: Optional[UserInfo] = None) -> Image.Image:
    """查看谱面"""
    calc = True
    isfull = True
    bestlist: List[ChartInfo] = []
    try:
        if qqid:
            if user == None:
                obj = await maiApi.query_user('player', qqid=qqid)
                player = UserInfo(**obj)
            else:
                player = user
            if music.basic_info.version == list(plate_to_version.values())[-1]:
                bestlist = player.charts.dx
                isfull = bool(len(bestlist) == 15)
            else:
                bestlist = player.charts.sd
                isfull = bool(len(bestlist) == 35)
        else:
            calc = False
    except UserNotFoundError:
        calc = False
    except UserDisabledQueryError:
        calc = False
    except Exception:
        calc = False

    im = Image.open(maimaidir / 'song_bg.png').convert('RGBA')
    dr = ImageDraw.Draw(im)
    hy = DrawText(dr, HANYI)
    tb = DrawText(dr, TBFONT)
    sy = DrawText(dr, SIYUAN)

    default_color = (5, 51, 101, 255)

    if music.basic_info.is_new:
        im.alpha_composite(Image.open(maimaidir / 'UI_CMN_TabTitle_NewSong.png'), (1400, 200))
    im.alpha_composite(Image.open(await maiApi.download_music_pictrue(music.id)), (205, 325))
    im.alpha_composite(Image.open(maimaidir / f'{music.basic_info.version}.png').resize((250, 120)), (1340, 610))
    im.alpha_composite(Image.open(maimaidir / f'{music.type}.png'), ((1150, 663)))

    title = music.title
    if coloumWidth(title) > 42:
        title = changeColumnWidth(title, 41) + '...'
    sy.draw(640, 370, 40, title, default_color, 'lm')
    artist = music.basic_info.artist
    if coloumWidth(artist) > 50:
        artist = changeColumnWidth(artist, 49) + '...'
    sy.draw(640, 445, 30, artist, default_color, 'lm')
    tb.draw(705, 568, 40, music.basic_info.bpm, default_color, 'lm')
    tb.draw(640, 685, 40, f'ID {music.id}', default_color, 'lm')
    sy.draw(970, 685, 30, music.basic_info.genre, default_color, 'mm')

    for num, _ in enumerate(music.level):
        if num == 4:
            color = (140, 44, 213, 255)
        else:
            color = (255, 255, 255, 255)
        tb.draw(280, 965 + 110 * num, 30, f'{music.level[num]}({music.ds[num]})', color, 'mm')
        tb.draw(475, 955 + 110 * num, 45, f'{round(music.stats[num].fit_diff, 2):.2f}' if music.stats and music.stats[num] else '-', default_color, anchor='mm')
        notes = list(music.charts[num].notes)
        tb.draw(658, 955 + 110 * num, 45, sum(notes), default_color, 'mm')
        if len(notes) == 4:
            notes.insert(3, '-')
        for n, c in enumerate(notes):
            tb.draw(834 + 175 * n, 955 + 110 * num, 45, c, default_color, 'mm')
        if num > 1:
            charter = music.charts[num].charter
            if coloumWidth(charter) > 19:
                charter = changeColumnWidth(charter, 18) + '...'
            sy.draw(535, 1597 + 75 * (num - 2), 26, charter, default_color, 'mm')
            ra = sorted([computeRa(music.ds[num], r) for r in achievementList[-6:]], reverse=True)
            for _n, value in enumerate(ra):
                size = 35
                if not calc:
                    rating = value
                elif not isfull:
                    size = 30
                    rating = f'{value}(+{value})'
                elif value > bestlist[-1].ra:
                    new = newbestscore(music.id, num, value, bestlist)
                    if new == 0:
                        rating = value
                    else:
                        size = 30
                        rating = f'{value}(+{new})'
                else:
                    rating = value
                tb.draw(770 + 155 * _n, 1597 + 75 * (num - 2), size, rating, default_color, 'mm')
    hy.draw(900, 1900, 30, f'Powered BY @澪度 - MilkBOT',default_color, anchor='mm')
    return im


async def music_play_data(qqid: int, music_id: Union[str,list,int]) -> Union[str, Image.Image]:
    """谱面游玩"""
    try:
        diff: List[Union[PlayInfoDev, PlayInfoDefault, None]]
        if not maimaitoken:
            data = await maiApi.query_user_post_dev(qqid=qqid, music_id=music_id)
            if not data:
                raise MusicNotPlayError

            music = mai.total_list.by_id(music_id)
            diff = [None for _ in music.ds]
            for _d in data:
                diff[_d.level_index] = _d
            dev = True
        else:
            version = list(set(_v for _v in plate_to_version.values()))
            data = await maiApi.query_user_plate(qqid=qqid, version=version)

            music = mai.total_list.by_id(music_id)
            _temp = [None for _ in music.ds]
            diff = copy.deepcopy(_temp)

            for _d in data:
                if _d.song_id == int(music_id):
                    diff[_d.level_index] = _d
            if diff == _temp:
                raise MusicNotPlayError
            dev = False

        im = Image.open(maimaidir / 'info_bg.png').convert('RGBA')

        dr = ImageDraw.Draw(im)
        tb = DrawText(dr, TBFONT)
        hy = DrawText(dr, HANYI)
        sy = DrawText(dr, SIYUAN)

        cover = Image.open(await maiApi.download_music_pictrue(music_id))
        im.alpha_composite(cover.resize((450, 450)), (125, 365))
        im.alpha_composite(Image.open(maimaidir / f'info-{category[music.basic_info.genre]}.png').convert('RGBA'), (120, 355))
        im.alpha_composite(Image.open(maimaidir / f'{music.basic_info.version}.png').convert('RGBA').resize((220, 109)), (455, 295))
        im.alpha_composite(Image.open(maimaidir / f'{music.type}.png').convert('RGBA').resize((80, 30)), (495, 816))

        color = (0, 86, 162, 255)
        artist = music.basic_info.artist
        if coloumWidth(artist) > 70:
            artist = changeColumnWidth(artist, 69) + '...'
        sy.draw(370, 870, 15, artist, color, 'mm')
        title = music.title
        if coloumWidth(title) > 38:
            l = title[:19]
            r = title[19:]
            sy.draw(110, 940, 28, l + '\n' + r, color, 'lm', multiline=True)
        else:
            sy.draw(370, 915, 30, title, color, 'mm')
        tb.draw(240, 1050, 32, music.id, color, 'mm')
        tb.draw(480, 1050, 32, music.basic_info.bpm, color, 'mm')

        y = 150
        for num, info in enumerate(diff):
            im.alpha_composite(Image.open(maimaidir / f'd-{num}.png'), (980, 355 + y * num))
            if info:
                if dev:
                    dxscore = info.dxScore
                    _dxscore = sum(music.charts[num].notes) * 3
                    dxnum = dxScore(dxscore / _dxscore * 100)
                    rating, rate = info.ra, score_Rank_l[info.rate]
                    im.alpha_composite(Image.open(maimaidir / 'ra-dx.png'), (1350, 396 + y * num))
                    if dxnum != 0:
                        im.alpha_composite(Image.open(maimaidir / f'UI_GAM_Gauge_DXScoreIcon_0{dxnum}.png'), (1351, 438 + y * num))
                    tb.draw(1465, 416 + y * num, 30, rating, color, 'mm')
                    tb.draw(1465, 454 + y * num, 20, f'{dxscore}/{_dxscore}', color, 'mm')
                else:
                    rating, rate = computeRa(music.ds[num], info.achievements, israte=True)
                    im.alpha_composite(Image.open(maimaidir / 'ra.png'), (1350, 405 + y * num))
                    tb.draw(1436, 450 + y * num, 35, rating, color, 'mm')

                im.alpha_composite(Image.open(maimaidir / 'fcfs.png'), (1130, 370 + y * num))
                if info.fc:
                    im.alpha_composite(Image.open(maimaidir / f'UI_CHR_PlayBonus_{fcl[info.fc]}.png').resize((93, 93)), (1141, 381 + y * num))
                if info.fs:
                    im.alpha_composite(Image.open(maimaidir / f'UI_CHR_PlayBonus_{fsl[info.fs]}.png').resize((93, 93)), (1226, 381 + y * num))
                im.alpha_composite(Image.open(maimaidir / f'UI_TTR_Rank_{rate}.png').resize((160, 76)), (1540, 400 + y * num))

                tb.draw(770, 440 + y * num, 70, f'{info.achievements:.4f}%', color, 'lm')
                tb.draw(1030, 372 + y * num, 35, music.ds[num], anchor='mm')
            else:
                tb.draw(1030, 372 + y * num, 35, music.ds[num], anchor='mm')
                sy.draw(1225, 445 + y * num, 50, '未游玩', color, 'mm')
        if len(diff) == 4:
            sy.draw(1225, 445 + y * 4, 45, '没有该难度', color, 'mm')

        hy.draw(900, 1265, 30, f'Powered BY @澪度 - MilkBOT', color, 'mm')
        return im
    except UserNotFoundError as e:
        raise UserNotFoundError(f'找不到用户: {e}')
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f'用户查询被禁用: {e}')
    except Exception as e:
        log.error(traceback.format_exc())
        raise Exception(f'遇到了无法处理的错误... {type(e)}')


def calc_achievements_fc(scorelist: Union[List[float], List[str]], lvlist_num: int, isfc: bool = False) -> int:
    r = -1
    obj = range(4) if isfc else achievementList[-6:]
    for __f in obj:
        if len(list(filter(lambda x: x >= __f, scorelist))) == lvlist_num:
            r += 1
        else:
            break
    return r


async def draw_rating_table(qqid: int, rating: str, isfc: bool = False) -> Union[str, Image.Image]:
    """绘制定数表"""
    try:
        version = list(set(_v for _v in plate_to_version.values()))
        data = await maiApi.query_user('plate', qqid=qqid, version=version)
        
        if rating in levelList[-3:]:
            bg = ratingdir / '14.png'
            ralist = list(reversed(levelList[-3:]))
            merge = True
        else:
            bg = ratingdir / f'{rating}.png'
            ralist = [rating]
            merge = False
        
        fromid = {}
        for _data in data['verlist']:
            if _data['level'] in ralist:
                if (id := str(_data['id'])) not in fromid:
                    fromid[id] = {}
                fromid[id][str(_data['level_index'])] = {
                    'achievements': _data['achievements'],
                    'fc': _data['fc'],
                    'level': _data['level']
                }

        musiclist = mai.total_list.lvList(rating=True)
        achievements_fc_list: List[Union[float, List[float]]] = []
        if merge:
            lvlist = {}
            for lv in ralist:
                lvlist.update(musiclist[lv])
                achievements_fc_list.append([])
        else:
            lvlist = musiclist[ralist[0]]
        
        im = Image.open(bg).convert('RGBA')
        draw = ImageDraw.Draw(im)
        tb = DrawText(draw, TBFONT)
        y = 168
        for ra in lvlist:
            x = 198
            y += 20
            for num, music in enumerate(lvlist[ra]):
                if num % 14 == 0:
                    x = 198
                    y += 85
                else:
                    x += 85
                if music.id in fromid and music.lv in fromid[music.id]:
                    if isfc:
                        if _fc := fromid[music.id][music.lv]['fc']:
                            achievements_fc_list[ralist.index(music.lvp)].append(combo_rank.index(_fc)) if merge else achievements_fc_list.append(combo_rank.index(_fc))
                            fc = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fcl[_fc]}.png').resize((50, 50))
                            im.alpha_composite(fc, (x + 15, y - 6))
                    else:
                        score = fromid[music.id][music.lv]['achievements']
                        achievements_fc_list[ralist.index(music.lvp)].append(score) if merge else achievements_fc_list.append(score)
                        rate = computeRa(music.ds, score, onlyrate=True)
                        rank = Image.open(maimaidir / f'UI_TTR_Rank_{rate}.png').resize((78, 36))
                        im.alpha_composite(rank, (x, y))
        if merge:
            lvkey = list(lvlist.keys())
            lvnum = [lvkey[:1], lvkey[1:4], lvkey[4:]]
            for num, i in enumerate(lvnum):
                lvlistlen = len([ _ for x in i for _ in lvlist[x] ])
                if len(achievements_fc_list[num]) == lvlistlen:
                    r = calc_achievements_fc(achievements_fc_list[num], lvlistlen, isfc)
                    if r != -1:
                        im.alpha_composite(Image.open(maimaidir / 'UI_Chara_Level_S #4824.png'), (600 + 250 * num, 154))
                        tb.draw(648 + 250 * num, 200, 40, ralist[num], anchor='mm')
                        pic = fcl[combo_rank[r]] if isfc else score_Rank_l[score_Rank[-6:][r]]
                        im.alpha_composite(Image.open(maimaidir / f'UI_MSS_Allclear_Icon_{pic}.png'), (700 + 250 * num, 120))
        else:
            lvlistlen = sum([len(lvlist[_]) for _ in lvlist])
            if len(achievements_fc_list) == lvlistlen:
                r = calc_achievements_fc(achievements_fc_list, lvlistlen, isfc)
                if r != -1:
                    pic = fcl[combo_rank[r]] if isfc else score_Rank_l[score_Rank[-6:][r]]
                    im.alpha_composite(Image.open(maimaidir / f'UI_MSS_Allclear_Icon_{pic}.png'), (1270, 120))
        return im
    except UserNotFoundError as e:
        raise UserNotFoundError(f'找不到用户: {e}')
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f'用户查询被禁用: {e}')
    except Exception as e:
        raise Exception(f'遇到了无法处理的错误... {type(e)}')


async def draw_plate_table(qqid: int, version: str, plan: str) -> Union[str, Image.Image]:
    """绘制完成表"""
    try:
        if version == '真':
            ver = list(set(_v for _v in list(plate_to_version.values())[0:2]))
        elif version in ['华', '華']:
            ver = [plate_to_version['熊']]
        elif version == '煌':
            ver = [plate_to_version['爽']]
        elif version == '星':
            ver = [plate_to_version['宙']]
        elif version == '祝':
            ver = [plate_to_version['祭']]
        else:
            ver = [plate_to_version[version]]
        music = mai.total_list.by_version(ver)
        plate_num = len(music)
        obj = await maiApi.query_user('plate', qqid=qqid, version=ver)
        playerdata: List[PlayInfoDefault] = list(filter(lambda x: str(x.song_id) not in ignore_music, [PlayInfoDefault(**v, ds=mai.total_list.by_id(str(v['id'])).ds[v['level_index']]) for v in obj['verlist']]))
        newdata = sorted(list(filter(lambda x: x.level_index == 3, playerdata)), key=lambda x: x.level_index,reverse=True)
        ra: Dict[str, Dict[str, Optional[PlayInfoDefault]]] = {}
        """
        {
            "14+": {
                "365": PlayInfoDefault,
                "xxx": {}
            },
            "14": {
                "xxx": PlayInfoDefault
            }
        }
        """
        music.sort(key=lambda x: x.ds[3], reverse=True)
        for _m in music:
            if _m.level[3] not in ra:
                ra[_m.level[3]] = {}
            ra[_m.level[3]][_m.id] = None

        for _d in newdata:
            ra[_d.level][str(_d.song_id)] = _d

        im = Image.open(platedir / f'{version}.png')
        draw = ImageDraw.Draw(im)
        tr = DrawText(draw, TBFONT)
        hy = DrawText(draw, HANYI)
        if version != '双':
            plate = Image.open(platedir / f'{version}{"極" if plan == "极" else plan}.png')
            im.alpha_composite(plate.crop((360, 0, 720, 116)), (790, 335))
        im.alpha_composite(Image.open(maimaidir / f'{plate_to_version[version]}.png'), (361, 300))
        b2 = Image.new('RGBA', (100, 100), (0, 0, 0, 150))
        lv: List[int] = []
        y = 375
        # if plan == '者':
        #     lv = [sum([1 for _ in data if _['level_index'] == n and _['achievements']] >= 80) for n in range(5)]
        #     for _ in ra:
        #         y += 15
        #         num = 0
        #         for _ms in ra[_r]:
        #             for _m in ra[_r][_ms]:
        #                 if num % 10 == 0:
        #                     x = 225
        #                     y += 115
        #                 else:
        #                     x += 115
        #                 num += 1
        #                 if 'achievements' not in _m or not _m['achievements'] >= 80: continue
        #                 fc = Image.open(root / 'maimaidx' / 'maimai' / f'UI_MSS_MBase_Icon_{fcl[_m["fc"]]}.png')
        #                 im.alpha_composite(fc, (x, y))
        if plan == '极' or plan == '極':
            lv = [plate_num - sum([1 for _ in playerdata if _.level_index == n and _.fc]) for n in range(4)]
            for _r in ra:
                x = 235
                y += 15
                for num, _ms in enumerate(ra[_r]):
                    if num % 10 == 0:
                        x = 235
                        y += 115
                    else:
                        x += 115
                    if (m := ra[_r][_ms]) and m.fc:
                        im.alpha_composite(b2, (x - 25, y - 25))
                        fc = Image.open(maimaidir / f'UI_CHR_PlayBonus_{fcl[m.fc]}.png').resize((75, 75))
                        im.alpha_composite(fc, (x - 12, y - 12))
        if plan == '将':
            lv = [plate_num - sum([1 for _ in playerdata if _.level_index == n and _.achievements >= 100]) for n in range(4)]
            for _r in ra:
                x = 235
                y += 15
                for num, _ms in enumerate(ra[_r]):
                    if num % 10 == 0:
                        x = 235
                        y += 115
                    else:
                        x += 115
                    if m := ra[_r][_ms]:
                        if m.achievements >= 100:
                            im.alpha_composite(b2, (x - 25, y - 25))
                        rate = computeRa(m.ds, m.achievements, onlyrate=True).lower()
                        rank = Image.open(maimaidir / f'UI_TTR_Rank_{rate}.png').resize((102, 48))
                        im.alpha_composite(rank, (x - 25, y))
        if plan == '神':
            _fc = ['ap', 'app']
            lv = [plate_num - sum([1 for _ in playerdata if _.level_index == n and _.fc in _fc]) for n in range(4)]
            for _r in ra:
                x = 235
                y += 15
                for num, _ms in enumerate(ra[_r]):
                    if num % 10 == 0:
                        x = 235
                        y += 115
                    else:
                        x += 115
                    if (m := ra[_r][_ms]) and m.fc in _fc:
                        im.alpha_composite(b2, (x - 25, y - 25))
                        ap = Image.open(maimaidir / f'UI_CHR_PlayBonus_{fcl[m.fc]}.png').resize((75, 75))
                        im.alpha_composite(ap, (x - 12, y - 12))
        if plan == '舞舞':
            fs = ['fsd', 'fdx', 'fsdp', 'fdxp']
            lv = [plate_num - sum([1 for _ in playerdata if _.level_index == n and _.fs in fs]) for n in range(4)]
            for _r in ra:
                x = 235
                y += 15
                for num, _ms in enumerate(ra[_r]):
                    if num % 10 == 0:
                        x = 235
                        y += 115
                    else:
                        x += 115
                    if (m := ra[_r][_ms]) and m.fs in fs:
                        im.alpha_composite(b2, (x - 25, y - 25))
                        fsd = Image.open(maimaidir / f'UI_CHR_PlayBonus_{fsl[m.fs]}.png').resize((75, 75))
                        im.alpha_composite(fsd, (x - 12, y - 12))
        for num, _v in enumerate(lv):
            if _v == 0:
                hy.draw(420 + 220 * num, 230, 40, '完成', (5, 51, 101, 255), 'mm')
            else:
                tr.draw(420 + 220 * num, 225, 50, _v, (5, 51, 101, 255), 'mm')
        hy.draw(750, im.size[1] - 118, 28, f'Powered BY @澪度 - MilkBOT', (5, 51, 101, 255), 'mm')
        return im
    except UserNotFoundError as e:
        raise UserNotFoundError(f'找不到用户: {e}')
    except UserDisabledQueryError as e:
        raise UserDisabledQueryError(f'用户查询被禁用: {e}')
    except Exception as e:
        error = traceback.format_exc()
        raise Exception(f'遇到了无法处理的错误... {type(e)}\n{error}')