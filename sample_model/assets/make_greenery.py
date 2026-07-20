"""Sinh SVG cụm lá eucalyptus (watercolor-ish) trang trí góc — tự chứa, không phụ thuộc ảnh ngoài.
Chạy: python sample_model/assets/make_greenery.py  → ghi greenery.svg
"""
import math, random
from pathlib import Path

random.seed(7)  # cố định để SVG ổn định giữa các lần chạy

W = H = 300
# Bảng xanh sage / eucalyptus nhẹ nhàng, hợp tông tím lavender của app
LEAF = ["#AEC6A0", "#93B187", "#7C9E77", "#B7CBB0", "#8FB2A8", "#6E9068"]
BERRY = ["#8CA88E", "#6E8C74"]


def qbez(p0, p1, p2, t):
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
    return x, y


def tangent(p0, p1, p2, t):
    dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
    dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
    return math.degrees(math.atan2(dy, dx))


def leaf(x, y, ang, rx, ry, fill):
    return (f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'fill="{fill}" transform="rotate({ang:.1f} {x:.1f} {y:.1f})"/>')


def branch(p0, p1, p2, n=11, base_rx=12, taper=0.55):
    """Một cành: thân cong + các lá tròn mọc đối xứng dọc thân, nhỏ dần về ngọn."""
    parts = [f'<path d="M{p0[0]:.0f} {p0[1]:.0f} Q{p1[0]:.0f} {p1[1]:.0f} '
             f'{p2[0]:.0f} {p2[1]:.0f}" fill="none" stroke="#7C9E77" '
             f'stroke-width="1.6" stroke-linecap="round" opacity=".55"/>']
    for i in range(1, n + 1):
        t = i / (n + 1)
        x, y = qbez(p0, p1, p2, t)
        ang = tangent(p0, p1, p2, t)
        scale = 1 - taper * t
        rx, ry = base_rx * scale, base_rx * 0.72 * scale
        jit = random.uniform(-6, 6)
        for side in (+1, -1):                      # lá mọc đối (eucalyptus)
            off = 90 * side
            fill = random.choice(LEAF)
            lx = x + math.cos(math.radians(ang + off)) * rx * 0.9
            ly = y + math.sin(math.radians(ang + off)) * rx * 0.9
            parts.append(leaf(lx, ly, ang + off + jit, rx, ry, fill))
    # chùm hạt nhỏ ở ngọn
    for _ in range(4):
        bx = p2[0] + random.uniform(-8, 8)
        by = p2[1] + random.uniform(-8, 8)
        parts.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{random.uniform(2.4,3.6):.1f}" '
                     f'fill="{random.choice(BERRY)}" opacity=".8"/>')
    return "".join(parts)


# Cụm góc trên-trái: các cành tỏa từ gần góc (0,0) vào giữa
branches = [
    branch((-6, -6), (70, 40), (150, 96), n=12, base_rx=13),
    branch((-6, 14), (48, 96), (96, 176), n=11, base_rx=12),
    branch((22, -6), (110, 34), (196, 64), n=10, base_rx=11),
    branch((-6, 40), (34, 120), (60, 210), n=8, base_rx=10),
]
body = "".join(branches)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
       f'<defs><filter id="soft" x="-20%" y="-20%" width="140%" height="140%">'
       f'<feGaussianBlur stdDeviation="0.6"/></filter></defs>'
       f'<g filter="url(#soft)" opacity="0.9">{body}</g></svg>')

out = Path(__file__).parent / "greenery.svg"
out.write_text(svg, encoding="utf-8")
print("wrote", out, "| bytes:", len(svg), "| leaves ~", svg.count("<ellipse"))
