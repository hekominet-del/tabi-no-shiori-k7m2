#!/usr/bin/env python3
"""停車点（速度ほぼ0が5分以上）と標高ピークを抽出する。"""
import json, math

JST_H = 9


def haversine(a, b):
    R = 6371000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dp, dl = la2 - la1, lo2 - lo1
    x = math.sin(dp / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


data = json.load(open('tracks_sel.json', encoding='utf-8'))
for trk in data:
    pts = trk['pts']
    print("\n=====", trk['name'], "=====")
    # cumulative moving speed
    stops = []
    i = 0
    n = len(pts)
    while i < n - 1:
        # detect a run where displacement over next window is tiny
        lat0, lon0 = pts[i][0], pts[i][1]
        j = i + 1
        while j < n and haversine((lat0, lon0), (pts[j][0], pts[j][1])) < 120:
            j += 1
        dur = j - i
        # time span
        t0, t1 = pts[i][3], pts[j - 1][3]
        if dur >= 3 and t0 and t1:
            stops.append((t0, t1, pts[i][0], pts[i][1], pts[i][2], round(haversine((lat0, lon0), (pts[j-1][0], pts[j-1][1])))))
        i = j if j > i + 1 else i + 1
    for s in stops:
        print(f"  stop {s[0][11:16]}-{s[1][11:16]} lat={s[2]:.4f} lon={s[3]:.4f} ele={s[4]:.0f} r={s[5]}m")
    els = [(p[2], p[3]) for p in pts if p[2] is not None]
    top = sorted(els, key=lambda x: -x[0])[:1]
    print("  max ele:", top)
    print("  start:", pts[0][3], "end:", pts[-1][3])
