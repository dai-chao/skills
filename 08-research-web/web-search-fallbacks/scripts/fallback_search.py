#!/usr/bin/env python3
"""Lightweight fallback search when SearXNG returns 403."""
import urllib.request, urllib.parse, ssl, re, html, json, sys

ctx = ssl.create_default_context()

WEATHER_CODES = {
    0: "晴朗", 1: "mainly clear", 2: "多云", 3: "阴天",
    45: "雾", 48: "雾凇", 51: "毛毛雨", 53: "小雨", 55: "中雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    95: "雷雨", 96: "雷雹", 99: "强雷雹"
}

TAIWAN_CITIES = {
    "台北": (25.0330, 121.5654), "台中": (24.1478, 120.6736),
    "高雄": (22.6273, 120.3014), "台南": (22.9997, 120.2270),
    "花莲": (23.9911, 121.6112), "台东": (22.7583, 121.1444),
}


def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def weather(city=None):
    cities = [(city, *TAIWAN_CITIES[city])] if city and city in TAIWAN_CITIES else \
             [(n, c[0], c[1]) for n, c in TAIWAN_CITIES.items()]
    out = []
    for name, lat, lon in cities:
        url = (f"https://api.open-meteo.com/v1/forecast?"
               f"latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m,weather_code"
               f"&timezone=Asia/Taipei")
        data = fetch_json(url)
        cur = data.get("current", {})
        code = cur.get("weather_code", -1)
        desc = WEATHER_CODES.get(code, f"代码{code}")
        out.append(f"{name}: {cur.get('temperature_2m')}°C, 湿度 {cur.get('relative_humidity_2m')}%, {desc}")
    return "\n".join(out)


def ddg_search(query, num=5):
    q = urllib.parse.quote(query)
    url = f"https://lite.duckduckgo.com/lite/?q={q}"
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    })
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        text = resp.read().decode("utf-8", errors="ignore")

    results = []
    for url, title in re.findall(
        r'<a[^>]*class="[^"]*result-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        text, re.DOTALL | re.I
    ):
        title = html.unescape(re.sub(r'<[^>]+>', '', title)).strip()
        if url.startswith("//"):
            url = "https:" + url
        results.append({"title": title, "url": url})
    return results[:num]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "weather":
        print(weather(sys.argv[2] if len(sys.argv) > 2 else None))
    elif cmd == "search":
        print(json.dumps(ddg_search(" ".join(sys.argv[2:])), ensure_ascii=False, indent=2))
    else:
        print("Usage: fallback_search.py weather [city] | search <query>")
