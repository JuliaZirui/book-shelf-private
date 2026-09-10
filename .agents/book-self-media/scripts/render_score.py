import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

WIDTH, HEIGHT = 1086, 1448
FONT_REGULAR = Path("C:/Windows/Fonts/msyh.ttc")
FONT_BOLD = Path("C:/Windows/Fonts/msyhbd.ttc")

def font(size, bold=False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)

def rgba(hex_color, alpha=255):
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)

def wrap(draw, text, text_font, max_width):
    lines, current = [], ""
    for char in text:
        candidate = current + char
        if current and draw.textlength(candidate, font=text_font) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines

def centered(draw, xy, text, text_font, fill):
    box = draw.textbbox((0, 0), text, font=text_font)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1]), text, font=text_font, fill=fill)

def fit_cover(canvas, source, box):
    raw = Image.open(source).convert("RGB")
    fitted = ImageOps.contain(raw, (box[2], box[3]), Image.Resampling.LANCZOS)
    x = box[0] + (box[2] - fitted.width) // 2
    y = box[1] + (box[3] - fitted.height) // 2
    canvas.paste(fitted, (x, y))

def blended_polygon(canvas, points, fill, outline=None):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer, "RGBA")
    layer_draw.polygon(points, fill=fill, outline=outline)
    return Image.alpha_composite(canvas, layer)

def draw_background(base_color):
    base = rgba(base_color)
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), base)
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    px = glow.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            distance = math.hypot((x - 540) / 780, (y - 720) / 920)
            alpha = max(0, int(30 * (1 - distance)))
            px[x, y] = (255, 255, 255, alpha)
    return Image.alpha_composite(canvas, glow)

def render(config_path, output_path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = config_path.parent
    background = config.get("background", "#123C32")
    foreground = config.get("foreground", "#F7F4EA")
    muted = config.get("muted", "#735724")
    accent = config.get("accent", "#FFF5D6")
    radar_color = config.get("radar_color", "#FFFFFF")
    radar_grid_alpha = int(config.get("radar_grid_alpha", 165))
    radar_fill_alpha = int(config.get("radar_fill_alpha", 28))
    selected_fill = config.get("selected_fill", "#FFFFFF")
    selected_fill_alpha = int(config.get("selected_fill_alpha", 179))
    selected_text = config.get("selected_text", "#2E2418")
    canvas = draw_background(background)
    draw = ImageDraw.Draw(canvas, "RGBA")

    logo_path = Path(config["logo"])
    if not logo_path.is_absolute():
        logo_path = base / logo_path
    canvas.alpha_composite(Image.open(logo_path).convert("RGBA"), (39, 53))

    intro_font = font(31, True)
    intro_lines = wrap(draw, config["intro"], intro_font, 585)
    draw.multiline_text((163, 48), "\n".join(intro_lines[:6]), font=intro_font, fill=foreground, spacing=9)

    cover_path = Path(config["cover"])
    if not cover_path.is_absolute():
        cover_path = base / cover_path
    fit_cover(canvas, cover_path, (806, 24, 240, 330))

    cx, cy, radius = 540, 735, 344
    grid = rgba(radar_color, radar_grid_alpha)
    grid_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid_layer, "RGBA")
    for level in range(2, 11, 2):
        ring = radius * level / 10
        grid_draw.ellipse((cx - ring, cy - ring, cx + ring, cy + ring), outline=grid, width=int(config.get("radar_grid_width", 2)))

    dimensions = ["解决问题", "行文结构", "严谨程度", "原创视角", "值得复读"]
    angles = [-90, -18, 54, 126, 198]
    default_label_positions = [(cx, 310), (905, 610), (735, 1065), (320, 1047), (48, 610)]
    label_positions = config.get("label_positions", default_label_positions)
    scores = config["scores"]
    values = [float(scores[name]) for name in dimensions]

    for angle in angles:
        rad = math.radians(angle)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        grid_draw.line((cx, cy, x, y), fill=grid, width=1)
    canvas = Image.alpha_composite(canvas, grid_layer)
    draw = ImageDraw.Draw(canvas, "RGBA")
    for level in range(2, 11, 2):
        ring = radius * level / 10
        centered(draw, (cx - 12, cy - ring - 18), str(level), font(16), radar_color)

    label_font = font(28, True)
    for name, pos in zip(dimensions, label_positions):
        if name in ("行文结构", "严谨程度", "值得复读"):
            draw.text(pos, name, font=label_font, fill=radar_color)
        else:
            centered(draw, pos, name, label_font, radar_color)

    points = []
    for value, angle in zip(values, angles):
        rad = math.radians(angle)
        ring = radius * value / 10
        points.append((cx + ring * math.cos(rad), cy + ring * math.sin(rad)))
    canvas = blended_polygon(canvas, points, rgba(radar_color, radar_fill_alpha))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.polygon(points, outline=radar_color)
    draw.line(points + [points[0]], fill=radar_color, width=4, joint="curve")
    score_font = font(31, True)
    score_offsets = [(12, -34), (14, -30), (16, 4), (-32, 4), (-32, -30)]
    for value, (x, y), (dx, dy) in zip(values, points, score_offsets):
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=radar_color)
        text = str(int(value)) if value.is_integer() else str(value)
        draw.text((x + dx, y + dy), text, font=score_font, fill=radar_color)

    centered(draw, (cx, 690), f"豆瓣评分 {config['douban_rating']}", font(27, True), radar_color)
    average = sum(values) / len(values)
    centered(draw, (cx, 735), f"{average:.1f}分", font(65, True), accent)

    categories = ["道\n世界观", "法\n方法论", "术\n技巧", "器\n工具"]
    selected_categories = set(config["categories"])
    for i, label in enumerate(categories):
        y = 1010 + i * 92
        width = 130 + i * 26
        poly = [(65, y), (65 + width, y), (65 + width + 24, y + 80), (65, y + 80)]
        active = label[0] in selected_categories
        fill = rgba(selected_fill, selected_fill_alpha) if active else rgba(foreground, 48)
        canvas = blended_polygon(canvas, poly, fill, rgba(foreground, 105))
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.multiline_text((84, y + 12), label, font=font(24, True), fill=rgba(selected_text) if active else accent, spacing=1)

    audiences = ["入门", "初级", "进阶", "高阶"]
    selected_audiences = set(config["audiences"])
    for i, label in enumerate(audiences):
        x = 622 + i * 100
        top = 1248 - i * 28
        active = label in selected_audiences
        fill = rgba(selected_fill, selected_fill_alpha) if active else rgba(foreground, 48)
        canvas = blended_polygon(canvas, [(x, top), (x + 82, top - 24), (x + 82, 1370), (x, 1370)], fill, rgba(foreground, 105))
        draw = ImageDraw.Draw(canvas, "RGBA")
        centered(draw, (x + 41, 1320), label, font(23, True), rgba(selected_text) if active else accent)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, quality=95)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.config.resolve(), args.output.resolve())

if __name__ == "__main__":
    main()