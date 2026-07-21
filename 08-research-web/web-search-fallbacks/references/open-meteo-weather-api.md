# Open-Meteo Weather API Reference

## Taiwan city coordinates

| City | Latitude | Longitude |
|------|----------|-----------|
| 台北 | 25.0330 | 121.5654 |
| 台中 | 24.1478 | 120.6736 |
| 高雄 | 22.6273 | 120.3014 |
| 台南 | 22.9997 | 120.2270 |
| 花莲 | 23.9911 | 121.6112 |
| 台东 | 22.7583 | 121.1444 |

## Request shape

```
https://api.open-meteo.com/v1/forecast
  ?latitude=LAT
  &longitude=LON
  &current=temperature_2m,relative_humidity_2m,weather_code
  &timezone=Asia/Taipei
```

No API key required.

## Weather code mapping (simplified)

| Code | Meaning |
|------|---------|
| 0 | 晴朗 |
| 1 |  mainly clear |
| 2 | 多云 |
| 3 | 阴天 |
| 45, 48 | 雾 / 雾凇 |
| 51, 53, 55 | 毛毛雨 |
| 61, 63, 65 | 小雨 / 中雨 / 大雨 |
| 71, 73, 75 | 小雪 / 中雪 / 大雪 |
| 95, 96, 99 | 雷雨 / 雷雹 / 强雷雹 |

See WMO Weather interpretation table in Open-Meteo docs for the full list.
