---
name: social-media-image-sourcing
description: 为社交媒体内容寻找和验证配图的工作流。特别适用于微信朋友圈、小红书、Twitter 等平台的配图需求，使用免版权图片源并通过 AI Vision 验证图文匹配度。
trigger: 需要为朋友圈、社交媒体帖子、小红书等找配图，或用户说"自己找图"、"配张图"
---

# 社交媒体配图寻找与验证

## 1. 明确需求
- 图片主题（如美食、旅行、生活）
- 风格氛围（如"烟火气"、文艺、极简）
- 是否需要与文案严格匹配（例如文案写"汤面"，图必须是汤面而非炒面）
- 版权要求（优先使用免费、可商用图片）

## 2. 获取免版权图片

### 首选：Wikimedia Commons API
在自动化环境中，主流免费图片网站（Pexels、Unsplash、StockSnap、Pixabay等）几乎都有 Cloudflare bot 检测，不可靠。**Wikimedia Commons 是最稳定的免版权图片源。**

```python
import urllib.request
import json
import urllib.parse

def search_commons_image(keyword, output_path="/tmp/social_media_img.jpg"):
    api_url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(keyword)}&srnamespace=6&srlimit=15&format=json&origin=*"
    req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0 (Python script)"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())
        results = data["query"]["search"]
        for r in results:
            title = r["title"]
            image_info_url = f"https://commons.wikimedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=imageinfo&iiprop=url|size&format=json&origin=*"
            req2 = urllib.request.Request(image_info_url, headers={"User-Agent": "Mozilla/5.0 (Python script)"})
            with urllib.request.urlopen(req2, timeout=30) as response2:
                data2 = json.loads(response2.read().decode())
                pages = data2["query"]["pages"]
                page = list(pages.values())[0]
                if "imageinfo" in page:
                    url = page["imageinfo"][0]["url"]
                    if url.lower().endswith(('.jpg', '.jpeg', '.png')):
                        # 下载图片
                        req3 = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req3, timeout=30) as response3:
                            img_data = response3.read()
                            with open(output_path, "wb") as f:
                                f.write(img_data)
                        return output_path, url
    return None, None
```

### 关键词策略
- 中文主题建议用英文搜索（如 "ramen"、"noodle soup"、"street food"、"night market"）
- 可以准备多个关键词候选，随机或轮询尝试

### 常见陷阱
| 图片源 | 问题 |
|---|---|
| Unsplash `source.unsplash.com` | **已彻底下线**，返回 503 |
| Unsplash 主站 | **BotStopper** 拦截，返回 `Access Denied` |
| Pexels / StockSnap / Pixabay | **Cloudflare 验证页**，bot 检测严格 |
| Wikimedia Commons | **429 Too Many Requests** — 连续搜索+获取图片详情会触发限流 |
| Foodish API | 图片类别以印度菜为主，不适合中式场景 |
| TheMealDB | 图片品质参差不齐，国别随机，无法控制风格 |

### Wikimedia Commons 限速处理
若需对多个结果逐个获取图片详情，**请求之间必须加延迟**（建议 1.5 秒以上），否则极易触发 429。单次搜索请求通常不会 429，但紧跟着对每个结果再发 `imageinfo` 请求就会爆。

```python
import time
# 搜索完成后，对结果逐个获取 URL 时
for r in results:
    # ... 获取 imageinfo ...
    time.sleep(1.5)
```

### 品牌官网 Fallback（产品图专用）
当所有免版权图库都被拦截，且需求是**特定品牌产品图**（如 MacBook、iPhone、相机等），品牌官网是比图库更稳定的来源：

1. 用 `browser_navigate` 访问官网产品页（如 `https://www.apple.com/macbook-pro/`）
2. 用 `browser_get_images` 提取页面上的产品图片 URL
3. 筛选出尺寸合适、内容正确的产品外观图
4. 用 `urllib.request` 下载到本地

**优势**：官网通常不会用 BotStopper/Cloudflare 拦截浏览器，图片质量高、产品准确。
**注意**：官网图片有版权，仅适合作为用户自己二手转卖的配图（合理使用），不适合公开发布到社媒平台。若需社媒公开发布，仍应优先寻找免版权图。

## 3. 验证图文匹配度
下载后**必须**使用 `vision_analyze` 工具检查图片是否真的符合需求，尤其是：
- 食物类型是否与文案一致（汤面 vs 炒面）
- 风格氛围是否匹配（烟火气 vs 精致摆盘）
- 是否有汤/有热气等关键元素

### Vision 验证 Prompt 模板
```
这张图是什么食物？有汤吗？看起来有烟火气和生活气息吗？适合配合朋友圈文案"XXX"来使用吗？
```

### 验证不通过时的处理
- 若图片与文案不匹配（如图是炒面但文案写汤头），**不要强行配**
- 有两种处理方式：
  1. **换图：** 重新搜索更符合的关键词，直到找到匹配的图
  2. **改文案：** 如果图的烟火气足但食物类型不对，可以调整文案来适配图片（如把"汤头熬得透"改为"锅气炒得足"）
- 优先级：如果用户强调"烟火气"，图片的场景氛围比具体菜品更重要

## 4. 上传图片获取公网 URL（API 发帖必需）

如果目标平台支持 API 发帖（如 **43Chat**、X/Twitter 等），本地图片路径无法直接使用，必须上传到图床获取公网 `https://` URL。

### 环境可用的上传方案

在自动化环境中，大多数图床会被封禁或限制。经过实际验证，以下服务可用：

**uguu.se（推荐）**
```bash
curl -s -F "files[]=@/path/to/image.jpg" https://uguu.se/upload
```
响应 JSON 中的 `files[0].url` 即为可直接使用的图片地址。

**已验证不可用的服务**
| 服务 | 问题 |
|---|---|
| catbox.moe / litterbox | 返回 412 Precondition Failed |
| transfer.sh | 连接超时 |
| 0x0.st | 已关闭匿名上传 |
| file.io | 无响应 |
| bashupload.com | 无响应 |

### 获取图片尺寸（无 PIL 时）
43Chat Moments API 要求提供 `width` 和 `height`。如果环境没有 `PIL`，用标准库解析 JPEG：
```python
import struct

def get_jpeg_size(path):
    with open(path, 'rb') as f:
        data = f.read()
    i = 0
    while i < len(data) - 1:
        if data[i] == 0xFF:
            marker = data[i+1]
            if marker == 0xD8:
                i += 2; continue
            elif marker == 0xD9:
                break
            elif marker in (0xC0, 0xC1, 0xC2, 0xC3):
                height = struct.unpack('>H', data[i+5:i+7])[0]
                width = struct.unpack('>H', data[i+7:i+9])[0]
                return width, height
            else:
                length = struct.unpack('>H', data[i+2:i+4])[0]
                i += 2 + length; continue
        i += 1
    return None, None
```

## 5. 发布到平台

### 43Chat Moments（朋友圈）
- 读取凭证：`~/.config/43chat/credentials.json` 中的 `api_key`
- 接口：`POST https://43chat.cn/open/moment/add`
- `text` 与 `medias` 不能同时为空；`medias[].type` 支持 `image`
- 成功以 `code = 0` 为准

```python
import urllib.request
import json

with open('/Users/chao/.config/43chat/credentials.json', 'r') as f:
    api_key = json.load(f)['api_key']

payload = {
    "text": "文案内容",
    "medias": [{
        "type": "image",
        "url": "https://h.uguu.se/xxxxx.jpg",
        "width": 4032,
        "height": 3024
    }]
}

req = urllib.request.Request(
    "https://43chat.cn/open/moment/add",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    method="POST"
)
```

### 手动发布（微信朋友圈等）
- 图片以 `MEDIA:/path/to/file` 格式发送给用户
- 文案以引用块格式发送
- 告知用户保存图片、复制文案后手动发布

## 注意事项
- Wikimedia Commons 的图片大小可能较大（几 MB），发送前无需压缩
- 部分图片可能带有西方文化元素（如日式拉面），如果用户强调"中式"，需要特意筛选
- 不要在未经验证的情况下直接发送图片给用户，必须经过 vision 验证
- API 发帖时，若图片与文案不匹配，优先**改文案适配图片**（快）或**重新搜图**（准）
