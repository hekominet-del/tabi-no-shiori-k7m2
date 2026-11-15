#!/usr/bin/env python3
"""2026-09-18/19 ツーリングの該当トラックを抽出して概要と停車点を出す。"""
import datetime, json, math, re, sys
import xml.etree.ElementTree as ET

JST = datetime.timezone(datetime.timedelta(hours=9))
GPX = r"G:\マイドライブ\GPS DATA 2026年11月15日.gpx"


def _tag(el):
    return el.tag.split('}')[-1]


def children(el, name):
    return [c for c in el if _tag(c) == name]


def text_of(el, name):
    for c in el:
        if _tag(c) == name and c.text:
            return c.text
    return None


def haversine(a, b):
    R = 6371000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dp, dl = la2 - la1, lo2 - lo1
    x = math.sin(dp / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def smooth(vals, k=5):
    out = []
    for i in range(len(vals)):
        w = [v for v in vals[max(0, i - k):i + k + 1] if v is not None]
        out.append(sum(w) / len(w) if w else None)
    return out


def parse_time(s):
    s = s.strip()
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    dt = datetime.datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(JST)


root = ET.parse(GPX).getroot()
alltracks = []
for trk in [e for e in root.iter() if _tag(e) == 'trk']:
    name = (text_of(trk, 'name') or '').strip()
    pts = []
    for seg in children(trk, 'trkseg'):
        for pt in children(seg, 'trkpt'):
            e, t = text_of(pt, 'ele'), text_of(pt, 'time')
            pts.append((float(pt.get('lat')), float(pt.get('lon')),
                        float(e) if e else None,
                        parse_time(t) if t else None))
    if len(pts) < 2:
        continue
    alltracks.append(dict(name=name, pts=pts))

print("total tracks:", len(alltracks))
pat = re.compile(r'(千曲川|志賀高原の林道|栄村|津南町|飯山市)')
sel = [t for t in alltracks if pat.search(t['name'])]
print("matched:", len(sel))
for t in sel:
    ts = [p[3] for p in t['pts'] if p[3]]
    el = [p[2] for p in t['pts'] if p[2] is not None]
    km = sum(haversine(t['pts'][i][:2], t['pts'][i + 1][:2]) for i in range(len(t['pts']) - 1)) / 1000
    print(f"  {t['name']!r} n={len(t['pts'])} {min(ts).strftime('%Y-%m-%d %H:%M')}..{max(ts).strftime('%m-%d %H:%M')} km={km:.1f} ele={min(el):.0f}-{max(el):.0f}")

with open('tracks_sel.json', 'w', encoding='utf-8') as f:
    json.dump([dict(name=t['name'],
                    pts=[[round(p[0], 6), round(p[1], 6), p[2],
                          p[3].strftime('%Y-%m-%d %H:%M:%S') if p[3] else None] for p in t['pts']])
               for t in sel], f, ensure_ascii=False)
print("wrote tracks_sel.json")
