#!/usr/bin/env python3
"""日別の距離・獲得標高・区間統計を出す。"""
import json, math
from datetime import datetime

F = '%Y-%m-%d %H:%M:%S'


def hav(a, b):
    R = 6371000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dp, dl = la2 - la1, lo2 - lo1
    x = math.sin(dp/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))


def smooth(vals, k=5):
    out = []
    for i in range(len(vals)):
        w = [v for v in vals[max(0, i-k):i+k+1] if v is not None]
        out.append(sum(w)/len(w) if w else None)
    return out


data = {t['name']: t['pts'] for t in json.load(open('tracks_sel.json', encoding='utf-8'))}


def stats(pts, label):
    km = sum(hav(pts[i][:2], pts[i+1][:2]) for i in range(len(pts)-1))/1000
    el = smooth([p[2] for p in pts])
    gain = sum(max(0, (el[i+1] or 0)-(el[i] or 0)) for i in range(len(el)-1))
    h = (datetime.strptime(pts[-1][3], F) - datetime.strptime(pts[0][3], F)).total_seconds()/3600
    els = [p[2] for p in pts if p[2] is not None]
    print(f"{label}: {km:.1f}km +{gain:.0f}m {h:.2f}h 最高{max(els):.0f}m 最低{min(els):.0f}m "
          f"{pts[0][3][5:16]}..{pts[-1][3][5:16]}")
    return km, gain


d1 = data['道の駅花の駅千曲川 志賀高原の林道-1']
stats(d1, '9/18 林道-1')
d2 = data['道の駅花の駅千曲川 志賀高原の林道-2']
day2 = [p for p in d2 if p[3].startswith('2026-09-19')]
night = [p for p in d2 if p[3].startswith('2026-09-18')]
stats(day2, '9/19 林道-2 全日')
print("  9/18夜の記録点:", len(night), night[0][3], night[-1][3])
cont = []
for n in ['栄村', '津南町', '飯山市']:
    cont += data[n]
stats(cont, '9/19 連続記録(栄村+津南町+飯山市)')
for n in ['栄村', '津南町', '飯山市']:
    stats(data[n], '  ' + n)

# 区間: 9/18 渋峠周辺
print("\n-- 9/18 主な点 --")
for target in ['2026-09-18 12:27', '2026-09-18 13:07', '2026-09-18 13:30', '2026-09-18 14:04',
               '2026-09-18 15:42', '2026-09-18 15:44', '2026-09-18 17:30']:
    best = min(d1 + night, key=lambda p: abs((datetime.strptime(p[3], F) - datetime.strptime(target, F)).total_seconds()))
    print(f"  {target} -> {best[3][5:16]} lat={best[0]:.4f} lon={best[1]:.4f} ele={best[2]:.0f}")
print("\n-- 9/19 主な点 --")
for target in ['2026-09-19 07:19', '2026-09-19 07:43', '2026-09-19 08:07', '2026-09-19 08:41',
               '2026-09-19 10:01', '2026-09-19 11:06', '2026-09-19 12:10', '2026-09-19 13:27',
               '2026-09-19 17:56', '2026-09-19 19:57', '2026-09-19 20:24']:
    best = min(day2, key=lambda p: abs((datetime.strptime(p[3], F) - datetime.strptime(target, F)).total_seconds()))
    print(f"  {target} -> {best[3][5:16]} lat={best[0]:.4f} lon={best[1]:.4f} ele={best[2]:.0f}")

# 標高1,600m以上の点を日別に
print("\n-- 高所 --")
for nm, pts in [('9/18', d1), ('9/19', day2)]:
    hi = [(p[3][11:16], p[2], p[0], p[1]) for p in pts if p[2] and p[2] > 1550]
    if hi:
        print(f"  {nm}: 1,550m超 {len(hi)}点 最高 {max(hi, key=lambda x: x[1])}")
