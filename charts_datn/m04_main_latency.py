"""
Biểu đồ hệ chính #4 — Latency truy hồi trung bình theo pipeline (11.759 chunk).
BM25 nhanh nhất; Hybrid chậm nhất; rerank giảm latency so với hybrid thường.
"""
import matplotlib.pyplot as plt
from _style import save, C, barlabels, style_axes, titles, PIPELINE_COLORS

pipelines = ["BM25", "Vector", "Hybrid\n+rerank", "Hybrid"]
lat = [46, 610, 608, 837]
colors = [PIPELINE_COLORS[0], PIPELINE_COLORS[1], PIPELINE_COLORS[2], PIPELINE_COLORS[3]]

fig, ax = plt.subplots(figsize=(8.4, 5.2))
bars = ax.bar(pipelines, lat, width=0.52, color=colors, zorder=3)
barlabels(ax, bars, fmt="{:.0f} ms", fontsize=11, dy=10)

style_axes(ax, ylabel="Latency trung bình (ms)")
ax.set_ylim(0, 950)
titles(ax, "Latency truy hồi theo pipeline — hệ chính",
       "BM25 rất nhanh (46 ms); rerank giảm độ trễ so với Hybrid thường")
ax.annotate("rerank cắt bớt ứng viên\n→ nhanh hơn Hybrid",
            xy=(2, 608), xytext=(1.1, 780), fontsize=9, color=C["muted"], ha="left",
            arrowprops=dict(arrowstyle="->", color=C["muted"], lw=1.1))
save(fig, "m04_main_latency")
