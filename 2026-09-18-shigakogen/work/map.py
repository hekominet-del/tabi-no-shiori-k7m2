#!/usr/bin/env python3
"""GPX から OSM タイルを使って軌跡図（PNG）を作る。トリミングではなく全体表示。"""
import json, math, os, sys
import requests
from PIL import Image, ImageDraw, ImageFont

UA = {"User-Agent": "hermes-trip-album/1.0 (personal, contact: local)"}
CACHE = "tiles"
FONT = "C:/Windows/Fonts/meiryo.ttc"
FONT_B = "C:/Windows/Fonts/meiryob.ttc"
Z = 13
TS = 256


def wpx(lat, lon, z=Z):
    n = TS * 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile(z, x, y):
    os.makedirs(CACHE, exist_ok=True)
    p = f"{CACHE}/{z}_{x}_{y}.png"
    if not os.path.exists(p):
        r = requests.get(f"https://tile.openstreetmap.org/{z}/{x}/{y}.png", headers=UA, timeout=30)
        if r.status_code != 200:
            return None
        open(p, "wb").write(r.content)
    return Image.open(p).convert("RGB")


def make_map(track_pts_list, labels, out, margin_px=150, width=1300, title=None, subtitle=None, extra_bbox=None):
    xs, ys = [], []
    for lat, lon in (extra_bbox or []):
        x, y = wpx(lat, lon)
        xs.append(x); ys.append(y)
    for pts in track_pts_list:
        for lat, lon, ele, t in pts:
            x, y = wpx(lat, lon)
            xs.append(x); ys.append(y)
    x0, x1 = min(xs) - margin_px, max(xs) + margin_px
    y0, y1 = min(ys) - margin_px, max(ys) + margin_px
    tx0, tx1 = int(x0 // TS), int(x1 // TS)
    ty0, ty1 = int(y0 // TS), int(y1 // TS)
    W = (tx1 - tx0 + 1) * TS
    H = (ty1 - ty0 + 1) * TS
    canvas = Image.new("RGB", (W, H), (238, 238, 234))
    n_ok = 0
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            im = tile(Z, tx, ty)
            if im is not None:
                canvas.paste(im, (tx * TS - tx0 * TS, ty * TS - ty0 * TS))
                n_ok += 1
    crop = canvas.crop((int(x0) - tx0 * TS, int(y0) - ty0 * TS, int(x1) - tx0 * TS, int(y1) - ty0 * TS))
    ox, oy = int(x0), int(y0)

    def px(lat, lon):
        x, y = wpx(lat, lon)
        return x - ox, y - oy

    d = ImageDraw.Draw(crop, "RGBA")
    colors = [(200, 30, 30), (20, 90, 200), (0, 130, 90), (150, 60, 180)]
    for i, pts in enumerate(track_pts_list):
        xy = [px(p[0], p[1]) for p in pts]
        # 白フチ → 色線
        for w, col in ((11, (255, 255, 255, 225)), (6, colors[i % len(colors)] + (240,))):
            d.line(xy, fill=col, width=w, joint="curve")

    f_lab = ImageFont.truetype(FONT_B, 34)
    f_sm = ImageFont.truetype(FONT, 26)
    for lab in labels:
        lat, lon, text, sub = lab[0], lab[1], lab[2], (lab[3] if len(lab) > 3 else None)
        dx = lab[4] if len(lab) > 4 else 0
        dy = lab[5] if len(lab) > 5 else 0
        cx, cy = px(lat, lon)
        r = 9
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=3)
        tw = d.textlength(text, font=f_lab)
        bh = 52 if sub else 46
        pad = 10
        bx = cx + 18 + dx
        by = cy - bh // 2 + dy
        if bx + tw + pad * 2 > crop.width - 4:
            bx = cx - 18 - tw - pad * 2
        by = max(6, min(by, crop.height - bh - 40))
        bx = max(4, min(bx, crop.width - tw - pad * 2 - 4))
        d.rounded_rectangle([bx, by, bx + tw + pad * 2, by + bh], radius=8,
                            fill=(255, 255, 255, 238), outline=(60, 60, 60, 255), width=2)
        d.text((bx + pad, by + (8 if sub else 6)), text, font=f_lab, fill=(20, 20, 20))
        if sub:
            d.text((bx + pad, by + 6 + 4), text, font=f_lab, fill=(20, 20, 20))
            d.text((bx + pad, by + 30), sub, font=f_sm, fill=(70, 70, 70))
    # 縮尺と帰属
    km_per_px = 156543.03392 * math.cos(math.radians(36.8)) / (2 ** Z)
    bar = 2000 / km_per_px
    bx, by = 24, crop.height - 46
    d.line([bx, by, bx + bar, by], fill=(30, 30, 30, 255), width=6)
    d.text((bx, by - 30), "2km", font=f_sm, fill=(30, 30, 30))
    att = "地図データ © OpenStreetMap contributors"
    tw = d.textlength(att, font=f_sm)
    d.rectangle([crop.width - tw - 16, crop.height - 40, crop.width, crop.height], fill=(255, 255, 255, 210))
    d.text((crop.width - tw - 8, crop.height - 38), att, font=f_sm, fill=(40, 40, 40))

    scale = width / crop.width
    out_im = crop.resize((width, round(crop.height * scale)), Image.LANCZOS)
    out_im.save(out, "PNG", optimize=True)
    print(f"{out}: {out_im.size} tiles={n_ok}")
    return out_im.size


data = {t['name']: t['pts'] for t in json.load(open('tracks_sel.json', encoding='utf-8'))}
d1 = data['道の駅花の駅千曲川 志賀高原の林道-1']
d2 = data['道の駅花の駅千曲川 志賀高原の林道-2']
day2 = [p for p in d2 if p[3].startswith('2026-09-19')]
cont = []
for n in ['栄村', '津南町', '飯山市']:
    cont += data[n]

def peak(pts, lo=None, hi=None):
    s = [p for p in pts if p[2] is not None and (lo is None or p[3][11:16] >= lo) and (hi is None or p[3][11:16] <= hi)]
    return max(s, key=lambda p: p[2])

print("9/18 最高点:", peak(d1))
print("9/19 最高点:", peak(day2))
print("9/19 08:41付近:", [p for p in day2 if p[3][11:16] == '08:41'][:3])

# 間引き（線を軽くする）
def thin(pts, step=3):
    return pts[::step] + [pts[-1]]

if __name__ == "__main__":
    make_map([thin(d1)], [
        (36.8822, 138.3886, "道の駅 花の駅千曲川", "発着・車中泊"),
        (36.7308, 138.5074, "志賀高原 1,677m", None, 20, -10),
        (36.7270, 138.4441, "湯田中・渋温泉方面 786m", None, -150, 52),
        (36.6585, 138.5317, "渋峠 2,174m", None),
        (36.6367, 138.5224, "万座温泉 豊国館", None),
        (36.9222, 138.4461, "野沢温泉（夜の大湯）", None),
    ], "map_day1.png", width=1250, extra_bbox=[(36.9222, 138.4461)])

    make_map([thin(day2)], [
        (36.8822, 138.3886, "道の駅 花の駅千曲川", None),
        (36.9222, 138.4461, "野沢温泉（朝湯）", None),
        (36.7906, 138.4956, "最高点 1,631m", "奥志賀スーパー林道"),
        (36.8334, 138.4997, "カヤの平方面 1,463m", None),
        (36.9529, 138.5053, "栄村の山あい 618m", None),
        (36.9888, 138.5816, "道の駅さかえ", None),
        (37.0432, 138.6111, "十日町の棚田", None),
        (36.8480, 138.3600, "飯山市内の寺院", None),
    ], "map_day2.png", width=1250)
