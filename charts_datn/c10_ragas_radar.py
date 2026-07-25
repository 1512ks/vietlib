"""
Biểu đồ #10 — Radar 7 chỉ số chất lượng sinh câu (RAGAS + coherence/fluency/citation), sample.
Nhãn giá trị đặt PHÍA TRONG điểm để không đè nhãn trục.
"""
import numpy as np
import matplotlib.pyplot as plt
from _style import save, C

labels = ["Faithfulness", "Answer\nRelevance", "Context\nPrecision@5",
          "Context\nRecall@5", "Coherence\n(/5)", "Fluency\n(/5)", "Citation\nvalid"]
vals   = [0.968, 0.911, 0.933, 0.902, 1.0, 1.0, 1.0]
raw    = ["0.968", "0.911", "0.933", "0.902", "5.0/5", "5.0/5", "100%"]

N = len(labels)
ang = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
v = vals + vals[:1]; a = ang + ang[:1]

fig, ax = plt.subplots(figsize=(7.4, 7.4), subplot_kw=dict(polar=True))
ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
ax.plot(a, v, "-", color=C["sample"], lw=2.4, zorder=3)
ax.plot(a, v, "o", color=C["sample"], ms=7, zorder=4)
ax.fill(a, v, color=C["sample"], alpha=0.15)

ax.set_xticks(ang); ax.set_xticklabels(labels, fontsize=11, color=C["ink"])
ax.set_ylim(0, 1.0); ax.set_yticks([0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0.25", "0.50", "0.75", "1.0"], fontsize=8, color="#AAB2BD")
ax.set_rlabel_position(90)
ax.grid(color=C["grid"], lw=1)
ax.spines["polar"].set_color(C["grid"])
# ngưỡng 0.9
ax.plot(a, [0.9]*len(a), "--", color=C["warn"], lw=1, alpha=0.7)
# nhãn giá trị đặt PHÍA TRONG (radius nhỏ hơn) → tránh đè nhãn trục ngoài
for ai, vi, r in zip(ang, vals, raw):
    ax.text(ai, max(vi - 0.14, 0.55), r, ha="center", va="center",
            fontsize=10, fontweight="bold", color=C["sample"])

ax.set_title("Chân dung chất lượng sinh câu · RAGAS (sample, n=28)", loc="left",
             fontsize=14, fontweight="bold", color=C["ink"], pad=26, x=-0.05)
ax.annotate("Đường cam nét đứt = ngưỡng mong muốn 0.9", xy=(0, 1.14),
            xycoords="axes fraction", ha="left", fontsize=10, color=C["muted"])
save(fig, "c10_ragas_radar")
