"""
Biểu đồ hệ chính #1 — nDCG@5 của 4 pipeline (11.759 chunk).
Nổi bật: Vector đơn lẻ SỤP (0.399); Hybrid mạnh nhất (0.866); rerank không đổi thứ hạng.
"""
import numpy as np
import matplotlib.pyplot as plt
from _style import save, C, barlabels, style_axes, titles, PIPELINE_COLORS

pipelines = ["BM25", "Vector", "Hybrid", "Hybrid\n+rerank"]
ndcg = [0.809, 0.399, 0.866, 0.866]

fig, ax = plt.subplots(figsize=(8.4, 5.2))
bars = ax.bar(pipelines, ndcg, width=0.52, color=PIPELINE_COLORS, zorder=3)
barlabels(ax, bars, fontsize=11)

style_axes(ax, ylabel="nDCG@5")
ax.set_ylim(0, 1.0)
ax.axhline(0.8, color=C["good"], ls=(0, (4, 4)), lw=1.2, alpha=0.6, zorder=2)
ax.text(-0.45, 0.808, "ngưỡng tốt 0.8", color=C["good"], fontsize=9.5, ha="left", va="bottom")
titles(ax, "nDCG@5 của 4 pipeline — hệ chính (11.759 chunk)",
       "Vector đơn lẻ yếu trên dữ liệu lớn nhiễu; Hybrid mạnh nhất")

ax.annotate("Vector SỤP: MiniLM + dữ liệu\ncrawl nhiễu (ngược với sample)",
            xy=(1, 0.399), xytext=(1.35, 0.20), fontsize=9.5, color=C["bad"], ha="left",
            arrowprops=dict(arrowstyle="->", color=C["bad"], lw=1.3))
ax.annotate("rerank = hybrid\n(relevant đã nằm trong top-K)",
            xy=(3, 0.866), xytext=(2.15, 0.94), fontsize=9, color=C["muted"], ha="left")
save(fig, "m01_main_ndcg_pipelines")
