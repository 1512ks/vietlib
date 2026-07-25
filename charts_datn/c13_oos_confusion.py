"""
Biểu đồ #13 — Ma trận nhầm lẫn in-scope × OOS (sample, n=50). Đúng = xanh, lỗi = đỏ dịu.
"""
import numpy as np
import matplotlib.pyplot as plt
from _style import save, C

M = np.array([[6, 0], [1, 43]])            # hàng: OOS, In-scope | cột: Từ chối, Trả lời
kind = np.array([["good", "bad"], ["bad", "good"]])
note = np.array([["TP", "FN"], ["FP · từ chối oan", "TN"]])

fig, ax = plt.subplots(figsize=(7.4, 5.8))
for i in range(2):
    for j in range(2):
        base = C["sample"] if kind[i, j] == "good" else C["bad"]
        alpha = 0.9 if M[i, j] else 0.28    # ô = 0 thì làm mờ
        ax.add_patch(plt.Rectangle((j, 1 - i), 0.96, 0.96, color=base, alpha=alpha))
        ax.text(j + 0.48, 1 - i + 0.58, str(M[i, j]), ha="center", va="center",
                fontsize=28, fontweight="bold", color="white")
        ax.text(j + 0.48, 1 - i + 0.26, note[i, j], ha="center", va="center",
                fontsize=11, color="white")

ax.set_xlim(-0.04, 2); ax.set_ylim(0, 2.0)
ax.set_xticks([0.48, 1.48]); ax.set_xticklabels(["Hệ TỪ CHỐI", "Hệ TRẢ LỜI"], fontsize=12)
ax.set_yticks([1.48, 0.48]); ax.set_yticklabels(["OOS\n(ngoài kho, n=6)", "In-scope\n(n=44)"], fontsize=12)
ax.xaxis.tick_top()
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0); ax.grid(False)
ax.set_title("Ma trận nhầm lẫn OOS · sample model", loc="left", y=1.14,
             fontsize=15, fontweight="bold", color=C["ink"])
ax.annotate("OOS Recall = 1.00   ·   False Refusal = 0.023   ·   Refusal Precision = 0.857",
            xy=(0, 1.075), xycoords="axes fraction", ha="left", fontsize=10.5, color=C["muted"])
save(fig, "c13_oos_confusion")
