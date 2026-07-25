"""
Biểu đồ #18 — Đối chứng 3 phương pháp chấm generation (n=28, judge=gemini-2.5-flash):
Tự code (kiểu RAGAS) vs RAGAS thật (0.2.15) vs DeepEval thật (4.1.2).
"""
import numpy as np
import matplotlib.pyplot as plt
from _style import save, C, style_axes, titles, BLUES

metrics = ["Faithfulness", "Answer\nRelevancy", "Context\nPrecision", "Context\nRecall"]
selfcode = [0.968, 0.911, 0.933, 0.902]
ragas    = [0.933, 0.811, 0.967, 0.816]
deepeval = [0.996, 0.908, 0.946, 0.929]

x = np.arange(len(metrics)); w = 0.26
fig, ax = plt.subplots(figsize=(9.6, 5.4))
series = [("Tự code (kiểu RAGAS)", selfcode, BLUES[1]),
          ("RAGAS thật (0.2.15)", ragas, BLUES[2]),
          ("DeepEval thật (4.1.2)", deepeval, BLUES[4])]
for i, (name, vals, col) in enumerate(series):
    pos = x + (i - 1) * (w + 0.015)
    bars = ax.bar(pos, vals, w, label=name, color=col, zorder=3)
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.012, f"{b.get_height():.2f}",
                ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=C["ink"])

style_axes(ax, ylabel="Điểm (0–1)")
ax.set_xticks(x); ax.set_xticklabels(metrics)
ax.set_ylim(0, 1.12)
titles(ax, "Đối chứng 3 phương pháp chấm generation — sample model",
       "Cùng 28 mẫu, cùng judge Gemini 2.5-flash · ba phương pháp độc lập hội tụ")
ax.legend(loc="lower center", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.2))
fig.subplots_adjust(bottom=0.2)
save(fig, "c18_framework_comparison")
