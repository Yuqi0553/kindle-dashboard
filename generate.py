#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont

# =========================================================
# 基本配置
# =========================================================

WIDTH, HEIGHT = 758, 1024
TZ = ZoneInfo("Europe/Madrid")

LOCATION_NAME = "PARLA"
LATITUDE = 40.24
LONGITUDE = -3.77

OUTPUT_FILE = "dashboard.png"
TODOS_FILE = "todos.txt"

BG = "white"
FG = "black"
LINE = "black"

PADDING = 36
LEFT = PADDING
RIGHT = WIDTH - PADDING

# =========================================================
# 字体
# =========================================================

def load_font(size=24, bold=False):
    candidates = []

    if bold:
        candidates += [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
    else:
        candidates += [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass

    return ImageFont.load_default()


FONT_SMALL = load_font(22, bold=False)
FONT_SMALL_BOLD = load_font(22, bold=True)
FONT_TEXT = load_font(28, bold=False)
FONT_TEXT_BOLD = load_font(28, bold=True)
FONT_SECTION = load_font(32, bold=True)
FONT_DATE = load_font(38, bold=True)
FONT_TIME = load_font(84, bold=True)
FONT_BIG = load_font(52, bold=True)

# =========================================================
# 工具函数
# =========================================================

def weather_code_to_text(code):
    mapping = {
        0: "晴",
        1: "基本晴",
        2: "局部多云",
        3: "阴",
        45: "雾",
        48: "冻雾",
        51: "小毛毛雨",
        53: "毛毛雨",
        55: "强毛毛雨",
        56: "冻毛毛雨",
        57: "强冻毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "冻雨",
        67: "强冻雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "阵雨",
        81: "强阵雨",
        82: "暴雨",
        85: "阵雪",
        86: "强阵雪",
        95: "雷暴",
        96: "雷暴夹小冰雹",
        99: "雷暴夹大冰雹",
    }
    return mapping.get(code, f"天气代码 {code}")


def weekday_cn(dt):
    arr = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return arr[dt.weekday()]


def draw_hline(draw, y, width=2):
    draw.line((LEFT, y, RIGHT, y), fill=LINE, width=width)


def draw_box(draw, x1, y1, x2, y2, radius=18, width=2):
    draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, outline=LINE, width=width, fill=BG)


def wrap_text(draw, text, font, max_width):
    if not text:
        return [""]

    lines = []
    current = ""

    for ch in text:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch

    if current:
        lines.append(current)

    return lines


def get_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}&longitude={LONGITUDE}"
        "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
        "&daily=temperature_2m_max,temperature_2m_min"
        "&timezone=Europe%2FMadrid"
        "&forecast_days=1"
    )

    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()

    current = data.get("current", {})
    daily = data.get("daily", {})

    return {
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "weather_code": current.get("weather_code"),
        "weather_text": weather_code_to_text(current.get("weather_code")),
        "wind": current.get("wind_speed_10m"),
        "temp_max": (daily.get("temperature_2m_max") or [None])[0],
        "temp_min": (daily.get("temperature_2m_min") or [None])[0],
    }


def load_todos(path=TODOS_FILE, max_items=8):
    p = Path(path)
    if not p.exists():
        return [
            "把待办写到 todos.txt",
            "每行一条事项",
            "例如：买菜",
            "例如：给木木洗澡",
        ]

    items = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            items.append(line)

    if not items:
        items = ["今天没有待办"]

    return items[:max_items]


# =========================================================
# 主绘图函数
# =========================================================

def build_dashboard():
    now = datetime.now(TZ)

    try:
        weather = get_weather()
        weather_ok = True
    except Exception:
        weather_ok = False
        weather = {
            "temperature": "--",
            "humidity": "--",
            "weather_code": None,
            "weather_text": "天气获取失败",
            "wind": "--",
            "temp_max": "--",
            "temp_min": "--",
        }

    todos = load_todos()

    img = Image.new("L", (WIDTH, HEIGHT), 255)  # 灰度图，255 白色
    draw = ImageDraw.Draw(img)

    # 标题区域
    y = 28
    draw.text((LEFT, y), "KINDLE DASHBOARD", fill=0, font=FONT_SECTION)
    y += 52
    draw.text((LEFT, y), "Parla · Date · Weather · Todos", fill=0, font=FONT_SMALL)
    y += 38
    draw_hline(draw, y, width=2)

    # 时间日期区域
    y += 28
    time_text = now.strftime("%H:%M")
    date_text = now.strftime("%Y-%m-%d")
    weekday_text = weekday_cn(now)

    draw.text((LEFT, y), time_text, fill=0, font=FONT_TIME)

    # 右边日期块
    date_x = 430
    draw.text((date_x, y + 10), date_text, fill=0, font=FONT_DATE)
    draw.text((date_x, y + 62), weekday_text, fill=0, font=FONT_BIG)

    y += 128
    draw_hline(draw, y, width=2)

    # 天气区
    y += 26
    weather_top = y
    weather_bottom = y + 240
    draw_box(draw, LEFT, weather_top, RIGHT, weather_bottom, radius=18, width=2)

    draw.text((LEFT + 18, weather_top + 16), f"{LOCATION_NAME} · 天气", fill=0, font=FONT_SECTION)

    if weather_ok:
        temp_now = f"{round(weather['temperature'])}°C" if weather["temperature"] != "--" and weather["temperature"] is not None else "--"
        desc = weather["weather_text"]
        tmax = f"{round(weather['temp_max'])}°" if weather["temp_max"] not in (None, "--") else "--"
        tmin = f"{round(weather['temp_min'])}°" if weather["temp_min"] not in (None, "--") else "--"
        hum = f"{weather['humidity']}%" if weather["humidity"] not in (None, "--") else "--"
        wind = f"{weather['wind']} km/h" if weather["wind"] not in (None, "--") else "--"
    else:
        temp_now = "--"
        desc = "天气获取失败"
        tmax = "--"
        tmin = "--"
        hum = "--"
        wind = "--"

    draw.text((LEFT + 24, weather_top + 70), temp_now, fill=0, font=FONT_TIME)
    draw.text((LEFT + 24, weather_top + 160), desc, fill=0, font=FONT_TEXT_BOLD)

    info_x = 430
    line_y = weather_top + 78
    draw.text((info_x, line_y),     f"最高: {tmax}", fill=0, font=FONT_TEXT)
    draw.text((info_x, line_y+40),  f"最低: {tmin}", fill=0, font=FONT_TEXT)
    draw.text((info_x, line_y+80),  f"湿度: {hum}", fill=0, font=FONT_TEXT)
    draw.text((info_x, line_y+120), f"风速: {wind}", fill=0, font=FONT_TEXT)

    y = weather_bottom + 24

    # 待办区
    todo_top = y
    todo_bottom = HEIGHT - 80
    draw_box(draw, LEFT, todo_top, RIGHT, todo_bottom, radius=18, width=2)
    draw.text((LEFT + 18, todo_top + 16), "今日待办", fill=0, font=FONT_SECTION)

    text_y = todo_top + 70
    max_text_width = RIGHT - LEFT - 70
    line_height = 38

    for i, item in enumerate(todos, start=1):
        bullet = f"{i}. "
        bullet_x = LEFT + 24
        item_x = LEFT + 58

        wrapped = wrap_text(draw, item, FONT_TEXT, max_text_width)
        if text_y + line_height > todo_bottom - 20:
            break

        draw.text((bullet_x, text_y), bullet, fill=0, font=FONT_TEXT)

        for j, line in enumerate(wrapped):
            if text_y + line_height > todo_bottom - 20:
                break
            draw.text((item_x, text_y), line, fill=0, font=FONT_TEXT)
            text_y += line_height

        text_y += 8

    # 底部
    footer = f"Updated: {now.strftime('%H:%M:%S')}  |  {LOCATION_NAME}"
    draw.text((LEFT, HEIGHT - 42), footer, fill=0, font=FONT_SMALL)

    img.save(OUTPUT_FILE)
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    build_dashboard()
