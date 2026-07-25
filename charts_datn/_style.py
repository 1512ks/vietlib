"""
_style.py -- Template biểu đồ ĐATN (phong cách phẳng, hiện đại).
- Font Segoe UI (đủ dấu tiếng Việt, hiện đại hơn DejaVu).
- Title canh TRÁI + subtitle mờ; grid NGANG mờ; bỏ khung (spine); bảng màu Tailwind.
- Lưu .pdf (vector, chèn Beamer) + .png (xem trước, DPI cao).
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

OUT = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)

# ---- font ----
_FONT = "Segoe UI" if "Segoe UI" in {f.name for f in fm.fontManager.ttflist} else "DejaVu Sans"

# ---- bảng màu XANH DƯƠNG (theo palette người dùng chọn) ----
# light blue -> steel -> indigo -> navy đậm -> navy
BLUES = ["#A6D5EA", "#83AECB", "#191970", "#0D0D38", "#123A63"]
INK   = "#1F2937"   # chữ chính (xám đậm)
MUTED = "#6B7280"   # chữ phụ
GRID  = "#E7ECF2"   # lưới (hơi ám xanh)
C = {
    "sample":      BLUES[2],    # indigo (hệ trọng tâm)
    "main":        BLUES[1],    # steel (nhạt hơn → tương phản tốt)
    "bm25":        BLUES[0],    # light blue
    "vector":      BLUES[1],    # steel
    "hybrid":      BLUES[4],    # navy
    "hybrid_plus": BLUES[2],    # indigo (đậm nhất = mạnh nhất)
    "good":        BLUES[4],    # navy cho đường/điểm tích cực
    "bad":         "#D9534F",   # đỏ dịu — CHỈ dùng cho ô lỗi (ma trận nhầm lẫn)
    "warn":        "#E0A458",   # cam đất — dùng cho cảnh báo
    "ink": INK, "muted": MUTED, "grid": GRID, "blues": BLUES,
}
PIPELINE_COLORS = [C["bm25"], C["vector"], C["hybrid"], C["hybrid_plus"]]

# Bề rộng cột mặc định — mảnh cho thoáng
BAR_W_GROUP = 0.28   # mỗi cột trong nhóm 2 series
BAR_W_SINGLE = 0.46  # cột đơn

plt.rcParams.update({
    "font.family": _FONT,
    "font.size": 12,
    "text.color": INK,
    "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED,
    "axes.labelsize": 12,
    "xtick.color": INK,
    "ytick.color": MUTED,
    "xtick.labelsize": 11,
    "ytick.labelsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "axes.axisbelow": True,
})


def style_axes(ax, ylabel=None, ygrid=True, xgrid=False):
    """Áp look phẳng hiện đại: bỏ khung, chỉ giữ lưới ngang mờ."""
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    if ygrid:
        ax.yaxis.grid(True, color=GRID, lw=1.0, zorder=0)
    if xgrid:
        ax.xaxis.grid(True, color=GRID, lw=1.0, zorder=0)
    ax.set_axisbelow(True)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED)


def titles(ax, title, subtitle=None):
    """Title canh TRÁI + subtitle mờ (kiểu dashboard hiện đại)."""
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold",
                 color=INK, pad=18 if subtitle else 12)
    if subtitle:
        ax.annotate(subtitle, xy=(0, 1), xytext=(0, 6),
                    xycoords="axes fraction", textcoords="offset points",
                    ha="left", va="bottom", fontsize=10.5, color=MUTED)


def barlabels(ax, bars, fmt="{:.3f}", fontsize=10, dy=0.012, color=None):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + dy, fmt.format(h),
                ha="center", va="bottom", fontsize=fontsize,
                fontweight="bold", color=color or INK)


def save(fig, name: str):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"saved: {name}.pdf + {name}.png")
