"""Sinh SVG cụm lá watercolor-ish (eucalyptus tròn + lá nhọn) trang trí GÓC — tự chứa.
Một cụm góc trên-trái; app tái dùng cho 4 góc bằng CSS transform (lật/xoay).
Chạy: python sample_model/assets/make_greenery.py  → ghi greenery.svg
"""
import math, random
from pathlib import Path

random.seed(11)  # cố định để SVG ổn định

W = H = 300
# Bảng xanh watercolor phong phú: sage, olive, xanh đậm, xanh vàng, xanh dương-lục
LEAF = ["#AEC6A0", "#93B187", "#7C9E77", "#B7CBB0", "#8FB2A8",
        "#6E9068", "#C3D6A8", "#5B7E5A", "#A7C48C"]
BERRY = ["#8CA88E", "#6E8C74", "#B9CDA6"]


def qbez(p0, p1, p2, t):
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
    return x, y


def tangent(p0, p1, p2, t):
    dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
    dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
    return math.degrees(math.atan2(dy, dx))


def leaf_round(x, y, ang, rx, ry, fill):
    return (f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'fill="{fill}" transform="rotate({ang:.1f} {x:.1f} {y:.1f})"/>')


def leaf_pointed(x, y, ang, L, w, fill):
    d = f"M0 0 Q {L*.5:.1f} {-w:.1f} {L:.1f} 0 Q {L*.5:.1f} {w:.1f} 0 0 Z"
    return (f'<path d="{d}" fill="{fill}" '
            f'transform="translate({x:.1f} {y:.1f}) rotate({ang:.1f})"/>')


def branch(p0, p1, p2, n=11, base=12, taper=0.55, pointed=False):
    parts = [f'<path d="M{p0[0]:.0f} {p0[1]:.0f} Q{p1[0]:.0f} {p1[1]:.0f} '
             f'{p2[0]:.0f} {p2[1]:.0f}" fill="none" stroke="#7C9E77" '
             f'stroke-width="1.5" stroke-linecap="round" opacity=".5"/>']
    for i in range(1, n + 1):
        t = i / (n + 1)
        x, y = qbez(p0, p1, p2, t)
        ang = tangent(p0, p1, p2, t)
        scale = 1 - taper * t
        jit = random.uniform(-7, 7)
        for side in (+1, -1):
            off = 90 * side
            fill = random.choice(LEAF)
            dist = base * (0.8 if pointed else 0.9) * scale
            lx = x + math.cos(math.radians(ang + off)) * dist
            ly = y + math.sin(math.radians(ang + off)) * dist
            if pointed:
                parts.append(leaf_pointed(lx, ly, ang + off + jit,
                                          base * 1.7 * scale, base * 0.42 * scale, fill))
            else:
                parts.append(leaf_round(lx, ly, ang + off + jit,
                                        base * scale, base * 0.72 * scale, fill))
    for _ in range(5):  # chùm hạt ngọn
        bx = p2[0] + random.uniform(-9, 9)
        by = p2[1] + random.uniform(-9, 9)
        parts.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{random.uniform(2.2,3.6):.1f}" '
                     f'fill="{random.choice(BERRY)}" opacity=".8"/>')
    return "".join(parts)


# 6 cành tỏa từ góc (0,0) vào giữa — xen kẽ lá tròn / lá nhọn cho phong phú
branches = [
    branch((-8, -8), (74, 42), (156, 100), n=13, base=13, pointed=False),
    branch((-8, 12), (52, 100), (104, 184), n=12, base=12, pointed=True),
    branch((24, -8), (116, 34), (206, 66), n=11, base=12, pointed=True),
    branch((-8, 44), (36, 126), (66, 220), n=9, base=11, pointed=False),
    branch((-8, -8), (34, 60), (58, 132), n=8, base=10, pointed=True),
    branch((44, -8), (150, 20), (238, 44), n=8, base=10, pointed=False),
]
body = "".join(branches)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
       f'<defs><filter id="soft" x="-20%" y="-20%" width="140%" height="140%">'
       f'<feGaussianBlur stdDeviation="0.55"/></filter></defs>'
       f'<g filter="url(#soft)" opacity="0.92">{body}</g></svg>')

out = Path(__file__).parent / "greenery.svg"
out.write_text(svg, encoding="utf-8")
print("bytes", len(svg), "ellipse", svg.count("<ellipse"),
      "path-leaf", svg.count("<path d=\"M0 0"), "circle", svg.count("<circle"))
