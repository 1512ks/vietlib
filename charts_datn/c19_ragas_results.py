"""
Biểu đồ #19 — Kết quả RAGAS THẬT (thư viện) trên sample model, n=28, judge Gemini 2.5-flash.
Faithfulness / Answer Relevancy / Context Precision / Context Recall.
"""
import matplotlib.pyplot as plt
from _style import save, C, barlabels, style_axes, titles

metrics = ["Faithfulness", "Answer\nRelevancy", "Context\nPrecision", "Context\nRecall"]
vals    = [0.933, 0.811, 0.967, 0.816]

fig, ax = plt.subplots(figsize=(8.4, 5.0))
bars = ax.bar(metrics, vals, width=0.5, color=C["sample"], zorder=3)
barlabels(ax, bars, fontsize=12)

style_axes(ax, ylabel="Điểm (0–1)")
ax.set_ylim(0, 1.08)
ax.axhline(0.8, color=C["good"], ls=(0, (4, 4)), lw=1.2, alpha=0.6, zorder=2)
ax.text(-0.46, 0.808, "ngưỡng tốt 0.8", color=C["good"], fontsize=9.5, ha="left", va="bottom")
titles(ax, "Kết quả đánh giá RAGAS — Sample Model",
       "Thư viện RAGAS 0.2.15 · judge Gemini 2.5-flash · 28 mẫu")
save(fig, "c19_ragas_results")
