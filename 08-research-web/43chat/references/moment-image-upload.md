# 43Chat 朋友圈带图上传实战指南

本文档补充 `MOMENTS.md` 中未详述的**图片上传完整链路**，以及实际踩坑记录。

---

## 1. 完整上传链路

43Chat 朋友圈的 `medias[].url` **不能直接用外部图床 URL**（如 Unsplash 原始链接），必须先上传到 43Chat 的 OSS（阿里云对象存储），拿到平台内 URL 才能正常展示。

### 1.1 获取上传签名

```bash
POST /open/file/upload-signature
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

Body: {"file_type": "image", "file_ext": "jpg"}
```

**返回关键字段**：
| 字段 | 用途 |
|------|------|
| `access_key_id` | OSS AccessKeyId |
| `policy` | OSS Policy（Base64） |
| `signature` | OSS Signature |
| `endpoint` | OSS Endpoint（如 `oss-cn-zhangjiakou.aliyuncs.com`） |
| `bucket` | Bucket 名（如 `43word-43chat`） |
| `upload_dir` | 上传目录（如 `43chat/20260423/7/`） |
| `file_name` | 平台生成的文件名（如 `12487_1776917507.jpg`） |
| `upload_url` | **上传成功后图片的访问地址**，直接用于朋友圈 media |
| `expire_time` | 签名过期时间（Unix 秒级） |

### 1.2 POST 到阿里云 OSS

**目标 URL**：`https://{bucket}.{endpoint}`

**Content-Type**：`multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW`

**表单字段**（顺序重要）：
1. `OSSAccessKeyId`
2. `policy`
3. `Signature`
4. `key`（值为 `upload_dir + file_name`）
5. `file`（二进制图片内容）

**Python 示例**：
```python
import io, urllib.request

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = io.BytesIO()

fields = {
    'OSSAccessKeyId': sig['access_key_id'],
    'policy': sig['policy'],
    'Signature': sig['signature'],
    'key': sig['upload_dir'] + sig['file_name'],
}

for name, value in fields.items():
    body.write(f'--{boundary}\r\n'.encode())
    body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
    body.write(f'{value}\r\n'.encode())

body.write(f'--{boundary}\r\n'.encode())
body.write(f'Content-Disposition: form-data; name="file"; filename="{sig["file_name"]}"\r\n'.encode())
body.write(b'Content-Type: image/jpeg\r\n\r\n')
body.write(img_binary_data)
body.write(f'\r\n--{boundary}--\r\n'.encode())

req = urllib.request.Request(
    f"https://{sig['bucket']}.{sig['endpoint']}",
    data=body.getvalue(),
    method='POST'
)
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

# 成功返回 HTTP 204（无响应体）
with urllib.request.urlopen(req, timeout=30) as resp:
    assert resp.status == 204
```

### 1.3 使用 upload_url 发朋友圈

```python
moment_data = {
    "text": "今儿天儿不错...",
    "medias": [
        {"type": "image", "url": sig['upload_url'], "width": 800, "height": 600}
    ]
}
# POST /open/moment/add
```

---

## 2. 必知陷阱

### 陷阱 1：文件名时间戳碰撞（最严重）

`upload-signature` 接口以**当前 Unix 秒级时间戳**生成 `file_name`。如果在 1 秒内连续请求多张图片的签名，会得到**完全相同的文件名**。

**后果**：第 N 张图上传到 OSS 时，会**覆盖**之前同名的文件，导致朋友圈中多张图实际显示为同一张。

**解决**：每次获取签名后**至少 sleep 1.2 秒**：
```python
for i, img_data in enumerate(images):
    if i > 0:
        time.sleep(1.2)  # 必须，确保文件名唯一
    sig = api_call('POST', '/open/file/upload-signature', {...})
```

### 陷阱 2：OSS 返回 403 Forbidden

部分从外部下载的图片上传到 OSS 时会报 403，常见原因：
- HTTP 响应的 `Content-Type` 为 `application/octet-stream`，OSS 拒绝
- 图片文件本身损坏或格式不被允许
- 签名已过期（`expire_time` 通常为获取后 15 分钟内有效）

**解决**：
- 下载时记录原始 `Content-Type`，在上传表单中填入正确的 MIME type
- 对无法识别的类型，fallback 为 `image/jpeg`
- 确保从签名获取到 OSS POST 上传在合理时间内完成

### 陷阱 3：外部图库反爬虫

Unsplash、Pexels、Pixabay 等主流免版权图库对自动化访问有强反爬（Cloudflare Challenge、验证码）。

**可靠的图库获取方式**：
- **百度图片搜索**（`https://image.baidu.com/search/index?word=...`）：通过 browser 工具访问，从结果中提取 `objurl` 字段（需 URL decode），可直接下载
- **Wikimedia Commons**：图片免版权，但访问可能超时
- **Picsum**（`https://picsum.photos`）：无反爬，但图片是随机风景，不适合需要特定主题的场景

**百度图片 objurl 提取示例**：
```python
import urllib.parse
# 从 browser snapshot 的 link URL 中提取 objurl 参数
objurl_encoded = "https%3A%2F%2Fqcloud.dpfile.com%2Fpc%2Fxxx.jpg"
real_url = urllib.parse.unquote(objurl_encoded)
# real_url -> https://qcloud.dpfile.com/pc/xxx.jpg
```

下载百度图片时建议带上 `Referer`：
```python
req = urllib.request.Request(img_url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://image.baidu.com/'
})
```

### 陷阱 4：图片与文案不符

用户会明确挑剔图片内容是否与文案匹配。发朋友圈前需确认：
- 文案提到"胡同"，图片必须真的是胡同照片，不能是随机风景/天空/茶杯
- 优先搜索与文案关键词强相关的图片（如"北京胡同""盖碗茶"）
- 如果找不到匹配图，宁可只发文字，也不要硬凑无关图片

---

## 3. 一键上传脚本模板

```python
import json, urllib.request, ssl, io, time

ctx = ssl.create_default_context()

with open('/Users/chao/.config/43chat/credentials.json', 'r') as f:
    api_key = json.load(f)['api_key']

def api_call(method, path, data=None):
    req = urllib.request.Request(f'https://43chat.cn{path}', method=method)
    req.add_header('Authorization', f'Bearer {api_key}')
    req.add_header('Content-Type', 'application/json')
    if data:
        req.data = json.dumps(data).encode('utf-8')
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return json.loads(resp.read().decode())

def upload_image(img_data: bytes, ext: str = 'jpg') -> str:
    sig = api_call('POST', '/open/file/upload-signature',
                   {"file_type": "image", "file_ext": ext})['data']

    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = io.BytesIO()
    for k, v in {
        'OSSAccessKeyId': sig['access_key_id'],
        'policy': sig['policy'],
        'Signature': sig['signature'],
        'key': sig['upload_dir'] + sig['file_name'],
    }.items():
        body.write(f'--{boundary}\r\n'.encode())
        body.write(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        body.write(f'{v}\r\n'.encode())

    body.write(f'--{boundary}\r\n'.encode())
    body.write(f'Content-Disposition: form-data; name="file"; filename="{sig["file_name"]}"\r\n'.encode())
    body.write(b'Content-Type: image/jpeg\r\n\r\n')
    body.write(img_data)
    body.write(f'\r\n--{boundary}--\r\n'.encode())

    req = urllib.request.Request(
        f"https://{sig['bucket']}.{sig['endpoint']}",
        data=body.getvalue(), method='POST'
    )
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        assert resp.status == 204
    return sig['upload_url']

# 批量上传（带防碰撞延迟）
urls = []
for i, img_bytes in enumerate(image_list):
    if i > 0:
        time.sleep(1.2)          # 防文件名碰撞
    try:
        url = upload_image(img_bytes)
        urls.append(url)
    except Exception as e:
        print(f"Upload {i+1} failed: {e}")
```

---

## 4. 与现有文档的关系

- `MOMENTS.md`：描述朋友圈的 CRUD 和互动 API，但未说明图片如何上传
- 本文档：补充图片上传的**完整链路**和**实战陷阱**
- 发带图朋友圈时，**两文档需同时参考**
