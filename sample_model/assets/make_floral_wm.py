"""Sinh SVG hình chìm hoa watercolor (magnolia hồng ombre + forget-me-not xanh + lá nhạt)
cho NỀN GIỮA vùng chat — rất nhạt, nằm dưới chữ nên không ảnh hưởng đọc nội dung.
Bố cục thưa, mép trên/dưới trống để lặp dọc (repeat-y) tự nhiên khi chat dài.
Chạy: python sample_model/assets/make_floral_wm.py  → ghi floral_wm.svg
"""
import math
import random
from pathlib import Path

random.seed(7)  # cố định để SVG ổn định

W, H = 720, 1000

# Ombre hồng: gốc đậm hơn → đầu cánh nhạt dần (gradient theo trục cánh)
PINK_DEEP = ["#EFA8BC", "#F2B4C4", "#F0AEC2"]
PINK_PALE = ["#FBE3EA", "#FADEE7", "#FCEAF0"]
LEAF = ["#CBDCC8", "#D8E6D4", "#C2D6C4"]
BLUE = ["#A9C4EA", "#BCD1F0", "#9FBCE6"]
CENTER = "#F0D48A"


def _grad(gid: str, c_from: str, c_to: str) -> str:
    """Gradient dọc theo cánh hoa (gốc → ngọn) tạo hiệu ứng ombre."""
    return (f'<linearGradient id="{gid}" x1="0" y1="1" x2="0" y2="0">'
            f'<stop offset="0" stop-color="{c_from}"/>'
            f'<stop offset="1" stop-color="{c_to}" stop-opacity=".55"/>'
            f'</linearGradient>')


def petal(x, y, ang, L, w, gid, op=1.0):
    """Cánh magnolia: giọt nước cong nhẹ, gốc tại (x,y), hướng lên, xoay ang độ."""
    d = (f"M0 0 C {-w:.0f} {-L*.30:.0f}, {-w*.92:.0f} {-L*.78:.0f}, {-w*.14:.0f} {-L:.0f} "
         f"C {w*.62:.0f} {-L*.86:.0f}, {w:.0f} {-L*.34:.0f}, 0 0 Z")
    return (f'<path d="{d}" fill="url(#{gid})" opacity="{op:.2f}" '
            f'transform="translate({x:.0f} {y:.0f}) rotate({ang:.0f})"/>')


def bud(x, y, ang, L):
    """Nụ magnolia hé (kiểu tulip trong thiệp): 3 cánh chụm + đài xanh nhạt."""
    w = L * 0.34
    parts = [
        petal(x, y, ang - 16, L * .88, w * .9, "pkB", .9),
        petal(x, y, ang + 16, L * .88, w * .9, "pkB", .9),
        petal(x, y, ang, L, w, "pkA"),
        f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{L*.10:.0f}" fill="{random.choice(LEAF)}" opacity=".8"/>',
    ]
    return "".join(parts)


def bloom(x, y, size):
    """Hoa nở: 5-6 cánh toả tròn quanh nhuỵ vàng nhạt."""
    n = random.choice((5, 6))
    parts = []
    a0 = random.uniform(0, 60)
    for i in range(n):
        ang = a0 + i * 360 / n + random.uniform(-8, 8)
        parts.append(petal(x, y, ang, size, size * .38,
                           random.choice(("pkA", "pkB")), .92))
    parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{size*.14:.0f}" '
                 f'fill="{CENTER}" opacity=".75"/>')
    return "".join(parts)


def loose_petal(x, y, ang, L):
    """Cánh hoa rơi lẻ — rải khoảng trống cho giống mưa cánh hoa trong thiệp."""
    return petal(x, y, ang, L, L * .36, "pkB", random.uniform(.5, .75))


def stem(p0, p1, p2, with_leaves=True):
    """Cành mảnh cong nhẹ + vài lá nhọn nhạt hai bên."""
    parts = [f'<path d="M{p0[0]} {p0[1]} Q{p1[0]} {p1[1]} {p2[0]} {p2[1]}" fill="none" '
             f'stroke="#CBDCC8" stroke-width="3" stroke-linecap="round" opacity=".55"/>']
    if with_leaves:
        for t in (0.3, 0.55, 0.8):
            x = (1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0]
            y = (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]
            dx = 2*(1-t)*(p1[0]-p0[0]) + 2*t*(p2[0]-p1[0])
            dy = 2*(1-t)*(p1[1]-p0[1]) + 2*t*(p2[1]-p1[1])
            ang = math.degrees(math.atan2(dy, dx)) + random.choice((-70, 70))
            Lf, wf = random.uniform(34, 52), random.uniform(9, 13)
            d = f"M0 0 Q {Lf*.5:.0f} {-wf:.0f} {Lf:.0f} 0 Q {Lf*.5:.0f} {wf:.0f} 0 0 Z"
            parts.append(f'<path d="{d}" fill="{random.choice(LEAF)}" opacity=".7" '
                         f'transform="translate({x:.0f} {y:.0f}) rotate({ang:.0f})"/>')
    return "".join(parts)


def forget_me_not(x, y, n=5):
    """Cụm hoa xanh nhỏ 5 cánh tròn + nhuỵ vàng (điểm xuyết như trong thiệp)."""
    parts = []
    for _ in range(n):
        fx = x + random.uniform(-34, 34)
        fy = y + random.uniform(-30, 30)
        r = random.uniform(6.5, 9.5)
        c = random.choice(BLUE)
        for k in range(5):
            a = math.radians(k * 72 + random.uniform(-8, 8))
            parts.append(f'<circle cx="{fx + math.cos(a)*r:.0f}" '
                         f'cy="{fy + math.sin(a)*r:.0f}" r="{r*.62:.0f}" '
                         f'fill="{c}" opacity=".8"/>')
        parts.append(f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="{r*.34:.0f}" '
                     f'fill="{CENTER}"/>')
    return "".join(parts)


# ── Bố cục: cành chéo nhẹ giữa khung, nụ + hoa nở + cánh rơi + 2 cụm xanh ──
body = "".join([
    stem((250, 860), (330, 640), (300, 430)),
    stem((300, 430), (360, 330), (450, 270), with_leaves=False),
    bud(300, 430, -12, 150),
    bud(450, 270, 14, 120),
    bloom(210, 700, 95),
    bud(500, 610, 8, 110),
    loose_petal(560, 350, 40, 70),
    loose_petal(150, 300, -25, 62),
    loose_petal(420, 500, 155, 56),
    loose_petal(600, 790, -60, 66),
    loose_petal(120, 520, 120, 52),
    forget_me_not(600, 190, n=4),
    forget_me_not(140, 850, n=5),
])

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
       f'<defs>'
       + _grad("pkA", random.choice(PINK_DEEP), random.choice(PINK_PALE))
       + _grad("pkB", "#F6C7D3", "#FCEAF0")
       + f'<filter id="wc" x="-20%" y="-20%" width="140%" height="140%">'
       f'<feGaussianBlur stdDeviation="1.4"/></filter>'
       f'</defs>'
       f'<g filter="url(#wc)" opacity="0.5">{body}</g></svg>')

out = Path(__file__).parent / "floral_wm.svg"
out.write_text(svg, encoding="utf-8")
print("bytes", len(svg), "petals", svg.count('url(#pk'), "circles", svg.count("<circle"))
