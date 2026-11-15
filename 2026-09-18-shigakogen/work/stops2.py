#!/usr/bin/env python3
"""停車点（60m以内に4分以上）と標高ピークを抽出する。"""
import json, math

def hav(a, b):
    R = 6371000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dp, dl = la2 - la1, lo2 - lo1
    x = math.sin(dp/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

def ts(s):
    # 'YYYY-MM-DD HH:MM:SS'
    return s

data = json.load(open('tracks_sel.json', encoding='utf-8'))


def stops_of(pts, max_r=60, min_minutes=4):
    out = []
    i = 0
    n = len(pts)
    while i < n:
        j = i
        while j + 1 < n and hav((pts[i][0], pts[i][1]), (pts[j+1][0], pts[j+1][1])) < max_r:
            j += 1
        t0, t1 = pts[i][3], pts[j][3]
        if t0 and t1:
            from datetime import datetime
            f = '%Y-%m-%d %H:%M:%S'
            mins = (datetime.strptime(t1, f) - datetime.strptime(t0, f)).total_seconds()/60
            if mins >= min_minutes:
                out.append((t0, t1, round(mins), pts[i][0], pts[i][1], pts[i][2]))
                i = j+1
                continue
        i += 1
    return out


for trk in data:
    pts = trk['pts']
    print("\n=====", trk['name'], f"n={len(pts)}", pts[0][3], "->", pts[-1][3])
    for s in stops_of(pts):
        print(f"  {s[0][5:16]} - {s[1][11:16]} ({s[2]:>3}分) lat={s[3]:.4f} lon={s[4]:.4f} ele={s[5]:.0f}")
    # 30分ごとの位置と標高
    print("  -- 30分刻み --")
    last = None
    for p in pts:
        if not p[3]:
            continue
        key = p[3][:13] + ('0' if p[3][14] < '3' else '3')
        if key != last:
            last = key
            print(f"   {p[3][5:16]} lat={p[0]:.4f} lon={p[1]:.4f} ele={p[2]:.0f}")
