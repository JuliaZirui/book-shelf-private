#!/usr/bin/env python3
"""Render a 3:4 citation tree with immutable real book-cover assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


WIDTH, HEIGHT = 1086, 1448
WHITE = "#F7F4EA"
MUTED = "#C7D5CF"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


def fit_font(text: str, max_width: int, start: int, minimum: int, bold: bool = False):
    for size in range(start, minimum - 1, -1):
        font = load_font(size, bold)
        if font.getlength(text) <= max_width:
            return font
    return load_font(minimum, bold)


def centered_text(draw, center_x, y, text, font, fill, max_width=None):
    if max_width:
        font_path = Path(getattr(font, "path", ""))
        font = fit_font(text, max_width, font.size, max(13, font.size - 10), font_path.name.endswith("msyhbd.ttc"))
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((center_x - (box[2] - box[0]) / 2, y), text, font=font, fill=fill)


def rounded_cover(canvas: Image.Image, source: Path, box, radius=12, shadow=True):
    x, y, w, h = box
    if not source.exists():
        raise FileNotFoundError(f"Missing cover: {source}")
    raw = Image.open(source).convert("RGB")
    fitted = ImageOps.contain(raw, (w, h), Image.Resampling.LANCZOS)
    plate = Image.new("RGB", (w, h), "white")
    plate.paste(fitted, ((w - fitted.width) // 2, (h - fitted.height) // 2))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    if shadow:
        shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_mask = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(shadow_mask).rounded_rectangle(
            (x + 7, y + 9, x + w + 7, y + h + 9), radius=radius, fill=115
        )
        shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(10))
        shadow_layer.putalpha(shadow_mask)
        canvas.alpha_composite(shadow_layer)
    canvas.paste(plate, (x, y), mask)


def rounded_line(draw, points, fill, width):
    draw.line(points, fill=fill, width=width, joint="curve")
    r = width // 2
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def bezier_line(draw, p0, p1, p2, p3, fill, width, steps=40):
    """Draw a cubic Bezier branch with horizontal and vertical end tangents."""
    points = []
    for index in range(steps + 1):
        t = index / steps
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        points.append((round(x), round(y)))
    draw.line(points, fill=fill, width=width, joint="curve")
    radius = width // 2
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def elbow_branch(draw, side, cover_x, trunk_x, y, fill, width, radius=42, direction="up"):
    """Draw a long horizontal branch with a compact quarter-circle elbow."""
    kappa = 0.5522847498
    if side == "left":
        draw.line((cover_x, y, trunk_x - radius, y), fill=fill, width=width)
        p0 = (trunk_x - radius, y)
        p1 = (trunk_x - radius + kappa * radius, y)
        if direction == "down":
            p2 = (trunk_x, y + radius - kappa * radius)
            p3 = (trunk_x, y + radius)
        else:
            p2 = (trunk_x, y - radius + kappa * radius)
            p3 = (trunk_x, y - radius)
    else:
        draw.line((trunk_x + radius, y, cover_x, y), fill=fill, width=width)
        if direction == "down":
            p0 = (trunk_x + radius, y)
            p1 = (trunk_x + radius - kappa * radius, y)
            p2 = (trunk_x, y + radius - kappa * radius)
            p3 = (trunk_x, y + radius)
        else:
            p0 = (trunk_x, y - radius)
            p1 = (trunk_x, y - radius + kappa * radius)
            p2 = (trunk_x + radius - kappa * radius, y)
            p3 = (trunk_x + radius, y)
    bezier_line(draw, p0, p1, p2, p3, fill, width, steps=20)


def relation_label(draw, x0, x1, y, text, background):
    font = fit_font(text, abs(x1 - x0) - 12, 17, 13)
    text_w = font.getlength(text)
    pill_w = min(abs(x1 - x0) - 8, text_w + 22)
    cx = (x0 + x1) / 2
    draw.rounded_rectangle(
        (cx - pill_w / 2, y - 22, cx + pill_w / 2, y + 5),
        radius=12,
        fill=background,
        outline=(247, 244, 234, 110),
        width=1,
    )
    centered_text(draw, cx, y - 19, text, font, WHITE)


def flat_cover(canvas: Image.Image, source: Path, center_x: int, y: int, max_w: int, max_h: int):
    """Paste an undistorted front cover without an added frame, card or shadow."""
    if not source.exists():
        raise FileNotFoundError(f"Missing cover: {source}")
    raw = Image.open(source).convert("RGB")
    fitted = ImageOps.contain(raw, (max_w, max_h), Image.Resampling.LANCZOS)
    x = int(center_x - fitted.width / 2)
    canvas.paste(fitted, (x, y))
    return x, y, fitted.width, fitted.height


def plain_relation(draw, x: int, y: int, lines, font_size=22, fill=WHITE):
    font = load_font(font_size)
    draw.multiline_text((x, y), "\n".join(lines), font=font, fill=fill, spacing=7)


def plain_relation_above_branch(draw, x: int, branch_y: int, lines, font_size=22, gap=14, fill=WHITE):
    """Place relation copy above its branch with a measured, guaranteed gap."""
    font = load_font(font_size)
    text = "\n".join(lines)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=7)
    y = branch_y - gap - bbox[3]
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=7)


def render(config_path: Path, output_path: Path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = config_path.parent
    background = config.get("background", "#123C32")
    accent = config.get("accent", "#E6B95C")
    related_cover_scale = float(config.get("related_cover_scale", 1.0))
    target_cover_scale = float(config.get("target_cover_scale", 1.0))
    font_bump = int(config.get("font_bump", 0))
    right_center_x = 830 + round(150 * max(0.0, related_cover_scale - 1.0))
    right_relation_x = 565 - round(200 * max(0.0, related_cover_scale - 1.0))
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(canvas, "RGBA")

    centered_text(draw, WIDTH // 2, 38, config["title"], load_font(52 + font_bump, True), WHITE)

    target = config["target"]
    flat_cover(canvas, base / target["cover"], WIDTH // 2, 102, 240, 310)
    centered_text(draw, WIDTH // 2, 422, f"《{target['title']}》", load_font(27, True), WHITE, 360)
    centered_text(draw, WIDTH // 2, 458, target["author"], load_font(20), MUTED, 360)
    tagline = config.get("tagline", "")
    if tagline:
        tag_font = load_font(18)
        tag_w = tag_font.getlength(tagline) + 34
        draw.rounded_rectangle((WIDTH / 2 - tag_w / 2, 494, WIDTH / 2 + tag_w / 2, 530), radius=18, outline=accent, width=2)
        centered_text(draw, WIDTH // 2, 499, tagline, tag_font, accent)

    trunk_x = 540
    trunk_start = 530

    books = sorted(config["books"], key=lambda item: item["year"])
    layouts = [
        {"side": "left", "cx": 145, "y": 500, "w": 160, "h": 205, "branch_y": 615, "text_x": 285, "text_y": 548},
        {"side": "right", "cx": 830, "y": 630, "w": 150, "h": 200, "branch_y": 752, "text_x": 565, "text_y": 680},
        {"side": "left", "cx": 145, "y": 790, "w": 160, "h": 205, "branch_y": 910, "text_x": 285, "text_y": 840},
        {"side": "right", "cx": 830, "y": 950, "w": 150, "h": 200, "branch_y": 1072, "text_x": 565, "text_y": 1000},
        {"side": "left", "cx": 145, "y": 1090, "w": 160, "h": 205, "branch_y": 1212, "text_x": 285, "text_y": 1140},
    ]
    for book, layout in zip(books, layouts):
        _, cover_y, _, cover_h = flat_cover(
            canvas, base / book["cover"], layout["cx"], layout["y"], layout["w"], layout["h"]
        )
        label_y = cover_y + cover_h + 10
        centered_text(draw, layout["cx"], label_y, f"《{book['title']}》", load_font(21, True), WHITE, 250)
        centered_text(draw, layout["cx"], label_y + 30, book["author"], load_font(16), MUTED, 260)
        plain_relation(draw, layout["text_x"], layout["text_y"], book.get("relation_lines", [book["relation"]]))

        if layout["side"] == "left":
            y = layout["branch_y"]
            elbow_branch(draw, "left", 225, trunk_x, y, WHITE, 4)

        else:
            y = layout["branch_y"]
            elbow_branch(draw, "right", 755, trunk_x, y, WHITE, 4)

    trunk_end = max(layout["branch_y"] for layout in layouts[: len(books)]) + 65
    rounded_line(draw, [(trunk_x, trunk_start), (trunk_x, trunk_end)], WHITE, 4)

    timeline_x = int(config.get("timeline_x", 1040))
    year_positions = {1934: 295, 1949: 470, 1958: 735, 1973: 965, 1989: 1120, 1991: 1300}
    active_years = sorted({target["year"], *(book["year"] for book in books)})
    timeline_end = max(year_positions[year] for year in active_years) + 60
    draw.line((timeline_x, 220, timeline_x, timeline_end), fill=(247, 244, 234, 180), width=2)
    draw.polygon([(timeline_x, 197), (timeline_x - 11, 222), (timeline_x + 11, 222)], fill=WHITE)
    draw.polygon([(timeline_x, timeline_end + 23), (timeline_x - 11, timeline_end - 2), (timeline_x + 11, timeline_end - 2)], fill=WHITE)
    for year in active_years:
        y = year_positions[year]
        is_target = year == target["year"]
        dot = accent if is_target else WHITE
        draw.rectangle((timeline_x - 2, y - 2, timeline_x + 2, y + 2), fill=dot)
        font = load_font(27, is_target)
        label = str(year)
        tw = font.getlength(label)
        draw.rectangle((timeline_x - tw - 26, y - 20, timeline_x - 8, y + 20), fill=background)
        draw.text((timeline_x - tw - 15, y - 19), label, font=font, fill=dot)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, quality=95)


def render_chronological(config_path: Path, output_path: Path):
    """Render every node in publication order while keeping the target visually dominant."""
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = config_path.parent
    background = config.get("background", "#123C32")
    accent = config.get("accent", "#E6B95C")
    foreground = config.get("foreground", WHITE)
    title_color = config.get("title_color", foreground)
    muted = config.get("muted", MUTED)
    timeline_color = config.get("foreground", (247, 244, 234, 180))
    related_cover_scale = float(config.get("related_cover_scale", 1.1))
    target_cover_scale = float(config.get("target_cover_scale", 1.35))
    font_bump = int(config.get("font_bump", 2))
    title_font_bump = int(config.get("title_font_bump", 4))
    label_font_bump = int(config.get("label_font_bump", 2))
    scale_delta = max(0.0, related_cover_scale - 1.0)
    right_center_x = 830 + round(250 * scale_delta)
    left_relation_x = 285 - round(100 * scale_delta)
    right_relation_x = 565 - round(100 * scale_delta)
    target = {**config["target"], "is_target": True}
    related = [{**book, "is_target": False} for book in config["books"]]
    items = sorted([target, *related], key=lambda item: item["year"])

    target_index = next(index for index, item in enumerate(items) if item["is_target"])
    configured_anchors = config.get("anchors")
    if configured_anchors and len(configured_anchors) == len(items):
        anchors = [int(anchor) for anchor in configured_anchors]
    elif len(items) == 5:
        anchors_by_target = {
            0: [400, 760, 940, 1110, 1248],
            1: [220, 520, 880, 1070, 1248],
            2: [220, 430, 730, 1090, 1248],
            3: [210, 410, 610, 900, 1248],
            4: [230, 450, 680, 860, 1160],
        }
        anchors = anchors_by_target[target_index]
    else:
        start, end = 245, 1260
        step = (end - start) / max(1, len(items) - 1)
        anchors = [round(start + index * step) for index in range(len(items))]

    canvas = Image.new("RGBA", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(canvas, "RGBA")
    centered_text(draw, WIDTH // 2, 38, config["title"], load_font(52 + font_bump + title_font_bump, True), title_color)

    trunk_x = 540
    related_sides = {}
    side_index = 0
    for item in items:
        if not item["is_target"]:
            related_sides[item["title"]] = "left" if side_index % 2 == 0 else "right"
            side_index += 1

    target_anchor = anchors[target_index]
    target_width = round(240 * target_cover_scale)
    target_height = round(300 * target_cover_scale)
    target_top = target_anchor - round(target_height * 0.6)
    target_tag_top = target_top + target_height + 72
    target_tag_bottom = target_tag_top + 36

    related_anchors = [anchor for item, anchor in zip(items, anchors) if not item["is_target"]]
    radius = 42
    upper_related = [anchor for item, anchor in zip(items, anchors) if not item["is_target"] and anchor < target_anchor]
    lower_related = [anchor for item, anchor in zip(items, anchors) if not item["is_target"] and anchor > target_anchor]
    if upper_related:
        rounded_line(draw, [(trunk_x, min(upper_related) + radius), (trunk_x, target_top)], foreground, 4)
    if lower_related:
        rounded_line(draw, [(trunk_x, target_tag_bottom), (trunk_x, max(lower_related) + 65)], foreground, 4)

    for item, anchor in zip(items, anchors):
        if item["is_target"]:
            continue
        side = related_sides[item["title"]]
        direction = "down" if anchor < target_anchor else "up"
        if side == "left":
            cover_x = 145 + round(160 * related_cover_scale / 2)
            elbow_branch(draw, "left", cover_x, trunk_x, anchor, foreground, 4, radius, direction)
            text_x = left_relation_x
        else:
            cover_x = right_center_x - round(150 * related_cover_scale / 2)
            elbow_branch(draw, "right", cover_x, trunk_x, anchor, foreground, 4, radius, direction)
            text_x = right_relation_x
        relation_lines = item.get("relation_lines", [item["relation"]])
        # Reflow within the actual branch corridor, preserving every character.
        relation_font = load_font(22 + font_bump)
        available_width = (trunk_x if side == "left" else cover_x) - text_x - 18
        fitted_lines = []
        for original_line in relation_lines:
            current = ""
            for char in original_line:
                if current and relation_font.getlength(current + char) > available_width:
                    fitted_lines.append(current)
                    current = ""
                current += char
            if current:
                fitted_lines.append(current)
        relation_lines = fitted_lines
        if font_bump:
            plain_relation_above_branch(draw, text_x, anchor, relation_lines, 22 + font_bump, gap=14, fill=foreground)
        else:
            plain_relation(draw, text_x, anchor - 60, relation_lines, 22, fill=foreground)

    timeline_x = int(config.get("timeline_x", 1040))
    timeline_top = anchors[0] - 60
    timeline_bottom = anchors[-1] + 60
    draw.line((timeline_x, timeline_top, timeline_x, timeline_bottom), fill=timeline_color, width=2)
    draw.polygon([(timeline_x, timeline_top - 23), (timeline_x - 11, timeline_top + 2), (timeline_x + 11, timeline_top + 2)], fill=foreground)
    draw.polygon([(timeline_x, timeline_bottom + 23), (timeline_x - 11, timeline_bottom - 2), (timeline_x + 11, timeline_bottom - 2)], fill=foreground)
    for item, anchor in zip(items, anchors):
        is_target = item["is_target"]
        color = accent if is_target else foreground
        draw.rectangle((timeline_x - 2, anchor - 2, timeline_x + 2, anchor + 2), fill=color)
        font = load_font(27 + font_bump, is_target)
        label = str(item["year"])
        tw = font.getlength(label)
        draw.rectangle((timeline_x - tw - 26, anchor - 20, timeline_x - 8, anchor + 20), fill=background)
        draw.text((timeline_x - tw - 15, anchor - 19), label, font=font, fill=color)

    for item, anchor in zip(items, anchors):
        if item["is_target"]:
            _, target_cover_y, _, target_cover_h = flat_cover(
                canvas, base / item["cover"], WIDTH // 2, target_top, target_width, target_height
            )
            target_label_y = target_cover_y + target_cover_h + 10
            centered_text(draw, WIDTH // 2, target_label_y, f"《{item['title']}》", load_font(27 + font_bump + label_font_bump, True), foreground, 430)
            centered_text(draw, WIDTH // 2, target_label_y + 38 + label_font_bump, item["author"], load_font(20 + font_bump + label_font_bump), muted, 430)
            tagline = config.get("tagline", "")
            if tagline:
                tag_font = load_font(18 + font_bump)
                tag_w = tag_font.getlength(tagline) + 34
                draw.rounded_rectangle(
                    (WIDTH / 2 - tag_w / 2, target_tag_top, WIDTH / 2 + tag_w / 2, target_tag_bottom),
                    radius=18,
                    outline=accent,
                    width=2,
                )
                centered_text(draw, WIDTH // 2, target_tag_top + 5, tagline, tag_font, accent)
            continue

        side = related_sides[item["title"]]
        center_x = 145 if side == "left" else right_center_x
        cover_w = round((160 if side == "left" else 150) * related_cover_scale)
        cover_max_h = round(190 * related_cover_scale)
        cover_top = anchor - round(95 * related_cover_scale)
        _, cover_y, _, cover_h = flat_cover(canvas, base / item["cover"], center_x, cover_top, cover_w, cover_max_h)
        label_y = cover_y + cover_h + 10
        centered_text(draw, center_x, label_y, f"《{item['title']}》", load_font(21 + font_bump + label_font_bump, True), foreground, 280)
        centered_text(draw, center_x, label_y + 30 + font_bump + label_font_bump, item["author"], load_font(16 + font_bump + label_font_bump), muted, 290)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, quality=95)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render_chronological(args.config.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
