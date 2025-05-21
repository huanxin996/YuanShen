# Maimai API 文档

本文档详细介绍 YuanShen API 框架中的 maimai 模块相关接口。

## 🎮 功能概述

maimai 模块提供舞萌 DX 玩家成绩相关的多种图片生成接口，包括：

- 8 种不同类型的 B50 成绩图片生成
- 单曲成绩查询和绘制
- 定数表和版本表查询
- 玩家分数、定数进度信息展示
- 全球成绩数据展示
- 等级成就列表查询
- Rating 排名查询

## 🚀 接口列表

### B50 系列接口

以下所有接口均接受 POST 请求，使用 JSON 格式传参。

| 端点                      | 描述                 |
|---------------------------|---------------------|
| `/maimai/b50`             | 生成标准B50图片      |
| `/maimai/bypass50`        | 生成Bypass B50图片   |
| `/maimai/theoretical50`   | 生成理论值B50图片     |
| `/maimai/cum50`           | 生成积分B50图片      |
| `/maimai/abstract50`      | 生成简洁版B50图片     |
| `/maimai/high50`          | 生成高分B50图片      |
| `/maimai/ap50`            | 生成AP成绩B50图片     |
| `/maimai/fc50`            | 生成FC成绩B50图片     |

**请求参数：**

```json
{
  "qq": 12345678,      // 玩家QQ号（可选）
  "name": "玩家昵称"    // 玩家昵称（可选，qq和name至少填一个）
}
```

**成功响应：**

```json
{
  "returnCode": 1,
  "base64": "base64编码的图片数据..."
}
```

### 单曲信息查询

#### `/maimai/minfo` - 查询单曲成绩

**请求参数：**

```json
{
  "qq": 12345678,        // 玩家QQ号（必填）
  "songid": "1050"       // 歌曲ID或名称（必填）
}
```

#### `/maimai/music_info` - 显示自定义歌曲信息

**请求参数：**

```json
{
  "qq": 12345678,        // 玩家QQ号（必填）
  "name": "玩家昵称",    // 玩家昵称（当qq和name同时存在时，使用qq）
  "music_data": {        // 歌曲数据对象（必填）
    // 歌曲详细信息...
  }
}
```

### 定数和版本表查询

#### `/maimai/rating_table` - 查询定数表

**请求参数：**

```json
{
  "qq": 12345678,      // 玩家QQ号（必填）
  "rating": "14+",     // 定数值（必填）
  "isfc": false        // 是否仅显示FC成绩（可选，默认false）
}
```

#### `/maimai/plate_table` - 查询版本表

**请求参数：**

```json
{
  "qq": 12345678,         // 玩家QQ号（必填）
  "version": "maimai",    // 游戏版本（必填）
  "plan": "极"           // 评价等级（必填）
}
```

### 全球数据及玩家分数

#### `/maimai/music_global` - 查询全球曲目数据

**请求参数：**

```json
{
  "music_data": {        // 歌曲数据对象（必填）
    // 歌曲详细信息...
  },
  "level_index": 4       // 难度等级索引（必填）
}
```

#### `/maimai/rise_score` - 查询分数提升

**请求参数：**

```json
{
  "qq": 12345678,       // 玩家QQ号（必填）
  "name": "玩家昵称",    // 玩家名称（必填）
  "nickname": "昵称",   // 玩家昵称（可选）
  "rating": "14+",      // 定数值（必填）
  "score": "100.5"      // 分数（必填）
}
```

### 进度与排名查询

#### `/maimai/level_process` - 查询定数进度

**请求参数：**

```json
{
  "qq": 12345678,       // 玩家QQ号（必填）
  "name": "玩家昵称",    // 玩家名称（可选）
  "level": "14+",       // 定数值（必填）
  "plan": "SSS+",       // 评价等级（必填）
  "category": "default", // 分类（可选，默认为"default"）
  "page": 1             // 页码（可选，默认为1）
}
```

#### `/maimai/level_achievement_list` - 查询等级成就列表

**请求参数：**

```json
{
  "qq": 12345678,       // 玩家QQ号（必填）
  "name": "玩家昵称",    // 玩家名称（必填）
  "rating": "14+",      // 定数值（必填）
  "page": 1             // 页码（可选，默认为1）
}
```

#### `/maimai/rating_ranking` - 查询rating排名

**请求参数：**

```json
{
  "name": "玩家昵称",    // 玩家名称（必填）
  "page": 1             // 页码（必填）
}
```

## 🔧 错误处理

所有接口在发生错误时返回统一的错误格式：

```json
{
  "returnCode": 100,     // 错误码：100表示参数错误，101表示内部错误
  "msg": "错误信息描述"   // 具体错误原因
}
```

常见错误码：
- `100`: 请求参数错误（如缺少必要参数、用户不存在、曲目不存在等）
- `101`: 服务器内部错误（如生成图片失败）

## 🧩 使用示例

### 使用 Python 请求 B50 接口

```python
import requests
import json
import base64
from PIL import Image
import io

url = "https://your-api-domain.com/maimai/b50"
data = {
    "qq": 12345678,
    "name": "玩家昵称"
}

response = requests.post(url, json=data)
result = response.json()

if result["returnCode"] == 1:
    # 将Base64图片数据转为图片
    img_data = base64.b64decode(result["base64"])
    img = Image.open(io.BytesIO(img_data))
    img.show()  # 显示图片
    # 或保存图片
    # img.save("b50.png")
else:
    print(f"错误: {result['msg']}")
```

### 使用 JavaScript 请求歌曲信息

```javascript
async function getMaiMaiSongInfo() {
    const url = "https://your-api-domain.com/maimai/minfo";
    const data = {
        qq: 12345678,
        songid: "1050"  // 也可以使用歌曲名称
    };
    
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.returnCode === 1) {
            // 处理图片数据
            const imgElement = document.createElement("img");
            imgElement.src = `data:image/png;base64,${result.base64}`;
            document.body.appendChild(imgElement);
        } else {
            console.error(`请求失败: ${result.msg}`);
        }
    } catch (error) {
        console.error("请求出错:", error);
    }
}
```

## 📝 注意事项

1. **资源依赖**：本模块依赖于原 [nonebot-plugin-maimaidx](https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx) 项目的静态资源，请务必将资源文件放置在正确位置
2. **水鱼Token**：部分功能可能需要配置有效的水鱼Token，请在 `config.py` 中设置
3. **参数验证**：所有接口都有严格的参数验证，确保按规定格式传递参数
4. **响应格式**：成功响应统一为 `returnCode=1` 并包含 `base64` 字段，失败响应包含错误码和错误信息
5. **图片处理**：所有接口返回的都是图片的Base64编码，需要客户端自行解码显示

## 📚 相关资源

- [nonebot-plugin-maimaidx](https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx) - 本模块改造自该项目
- [FastAPI 文档](https://fastapi.tiangolo.com/) - API框架文档
