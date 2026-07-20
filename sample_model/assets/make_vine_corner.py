"""Sinh SVG cụm hoa dây leo ôm GÓC KHUNG (hoa hồng phấn nhụy nâu + lá xanh đậm
+ cành baby's breath vàng gold) — trang trí đè lên viền thẻ chat như thiệp mời.
Một cụm góc trên-trái hình chữ L; app đặt vào 2 góc đối xứng bằng CSS rotate(180deg).
Chạy: python sample_model/assets/make_vine_corner.py  → ghi vine_corner.svg
"""
import math
import random
from pathlib import Path

random.seed(21)  # cố định để SVG ổn định

W = H = 420

PINK = [("#F2AEBB", "#FADFE3"), ("#F5BCC6", "#FBE6E9"), ("#EFA3B2", "#F9D8DD")]
LEAF = ["#5F7A4E", "#75905F", "#4E6A44", "#86A06E"]
GOLD = "#C9A85C"
CREAM = ["#EFE3C2", "#F3E9CF", "#E8D9B0"]
HEART = "#6B4A3F"  # nhụy nâu


def qbez(p0, p1, p2, t):
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
    return x, y


def petal(x, y, ang, L, gid):
    """Cánh tròn bầu (gốc tại tâm hoa, hướng lên, xoay ang độ)."""
    w = L * 0.55
    d = (f"M0 0 C {-w:.0f} {-L*.20:.0f}, {-w:.0f} {-L*.75:.0f}, 0 {-L:.0f} "
         f"C {w:.0f} {-L*.75:.0f}, {w:.0f} {-L*.20:.0f}, 0 0 Z")
    return (f'<path d="{d}" fill="url(#{gid})" '
            f'transform="translate({x:.0f} {y:.0f}) rotate({ang:.0f})"/>')


def flower(x, y, size, gi):
    """Hoa 5 cánh hồng phấn + nhụy nâu + nhị chấm vàng (như hoa trong thiệp)."""
    a0 = random.uniform(0, 72)
    parts = [petal(x, y, a0 + k * 72, size, f"pk{gi}") for k in range(5)]
    parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{size*.22:.0f}" fill="{HEART}"/>')
    for k in range(8):
        a = math.radians(k * 45 + a0)
        r = size * 0.34
        parts.append(f'<circle cx="{x + math.cos(a)*r:.0f}" cy="{y + math.sin(a)*r:.0f}" '
                     f'r="{size*.045:.1f}" fill="{GOLD}"/>')
    return "".join(parts)


def mini_flower(x, y, r):
    """Hoa nhỏ 5 cánh tròn hồng nhạt + tâm vàng — rải dọc dây leo."""
    parts = []
    for k in range(5):
        a = math.radians(k * 72 + random.uniform(-10, 10))
        parts.append(f'<circle cx="{x + math.cos(a)*r:.0f}" cy="{y + math.sin(a)*r:.0f}" '
                     f'r="{r*.68:.1f}" fill="#F6CDD3"/>')
    parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r*.38:.1f}" fill="{GOLD}"/>')
    return "".join(parts)


def leaf(x, y, ang, L):
    w = L * 0.30
    d = f"M0 0 Q {L*.5:.0f} {-w:.0f} {L:.0f} 0 Q {L*.5:.0f} {w:.0f} 0 0 Z"
    return (f'<path d="{d}" fill="{random.choice(LEAF)}" opacity=".92" '
            f'transform="translate({x:.0f} {y:.0f}) rotate({ang:.0f})"/>')


def sprig(p0, p1, p2):
    """Cành baby's breath: thân gold mảnh + chùm chấm kem ở ngọn và dọc thân."""
    parts = [f'<path d="M{p0[0]} {p0[1]} Q{p1[0]} {p1[1]} {p2[0]} {p2[1]}" fill="none" '
             f'stroke="{GOLD}" stroke-width="1.6" stroke-linecap="round" opacity=".85"/>']
    for t in (0.45, 0.7, 0.9, 1.0):
        x, y = qbez(p0, p1, p2, t)
        for _ in range(random.randint(3, 5)):
            bx = x + random.uniform(-10, 10)
            by = y + random.uniform(-10, 10)
            parts.append(f'<circle cx="{bx:.0f}" cy="{by:.0f}" '
                         f'r="{random.uniform(1.8,3.2):.1f}" '
                         f'fill="{random.choice(CREAM)}"/>')
    return "".join(parts)


def stem(p0, p1, p2):
    """Dây leo chính màu lá, mảnh."""
    return (f'<path d="M{p0[0]} {p0[1]} Q{p1[0]} {p1[1]} {p2[0]} {p2[1]}" fill="none" '
            f'stroke="#6E8757" stroke-width="2.2" stroke-linecap="round" opacity=".8"/>')


# ── Bố cục chữ L ôm góc trên-trái: dây leo chạy dọc 2 cạnh + hoa to ở góc ──
body = "".join([
    # dây leo dọc cạnh trên (ra phải) và cạnh trái (xuống dưới)
    stem((90, 55), (230, 30), (395, 55)),
    stem((55, 90), (30, 230), (55, 395)),
    # cành baby's breath gold tỏa theo 2 cạnh + chéo vào trong
    sprig((110, 70), (240, 55), (360, 95)),
    sprig((70, 110), (55, 240), (95, 360)),
    sprig((120, 100), (220, 150), (300, 210)),
    # lá xanh đậm fan quanh góc và rải theo dây
    leaf(105, 75, -28, 62), leaf(160, 48, 8, 56), leaf(250, 42, -14, 50),
    leaf(320, 60, 12, 46), leaf(75, 105, 62, 62), leaf(48, 160, 82, 56),
    leaf(42, 250, 104, 50), leaf(60, 320, 78, 46), leaf(130, 130, 40, 58),
    leaf(180, 90, -55, 44), leaf(90, 180, 145, 44),
    # hoa chính ở góc + hoa vừa dọc 2 cạnh
    flower(85, 95, 46, 0),
    flower(185, 60, 33, 1),
    flower(60, 185, 35, 2),
    flower(290, 75, 26, 1),
    flower(75, 290, 27, 2),
    # hoa nhỏ rải tiếp về cuối dây cho thưa dần
    mini_flower(350, 68, 9), mini_flower(390, 90, 7),
    mini_flower(68, 350, 9), mini_flower(90, 390, 7),
    mini_flower(240, 100, 8), mini_flower(100, 240, 8),
])

grads = "".join(
    f'<linearGradient id="pk{i}" x1="0" y1="1" x2="0" y2="0">'
    f'<stop offset="0" stop-color="{deep}"/>'
    f'<stop offset="1" stop-color="{pale}"/>'
    f'</linearGradient>'
    for i, (deep, pale) in enumerate(PINK))

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
       f'<defs>{grads}'
       f'<filter id="soft" x="-15%" y="-15%" width="130%" height="130%">'
       f'<feGaussianBlur stdDeviation="0.4"/></filter></defs>'
       f'<g filter="url(#soft)" opacity="0.95">{body}</g></svg>')

out = Path(__file__).parent / "vine_corner.svg"
out.write_text(svg, encoding="utf-8")
print("bytes", len(svg), "flowers", svg.count(f'fill="{HEART}"'),
      "leaves", svg.count('opacity=".92"'), "sprig-dots", svg.count("<circle") )
