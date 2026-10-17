#!/usr/bin/env python3
"""Generate publication figures (fig_gap.pdf and fig_asymmetry.pdf) matching Table 3."""

import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]

    models = ["Gemma 4 (31B)", "Llama 3.1 (70B)", "Qwen 2.5 (72B)"]
    x = np.arange(len(models))

    # Figure 3: fig_gap.pdf
    mcq = [74.98, 46.00, 39.00]
    cqa = [52.49, 46.06, 22.58]
    bleu = [1.01, 1.01, 0.08]

    width = 0.25
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=300)
    rects1 = ax.bar(
        x - width,
        mcq,
        width,
        label="MCQ Accuracy (%)",
        color="#4C72B0",
        edgecolor="black",
        linewidth=0.6,
    )
    rects2 = ax.bar(
        x,
        cqa,
        width,
        label="Context QA (F1)",
        color="#55A868",
        edgecolor="black",
        linewidth=0.6,
    )
    rects3 = ax.bar(
        x + width,
        bleu,
        width,
        label="EN->DV Translation (BLEU)",
        color="#C44E52",
        edgecolor="black",
        linewidth=0.6,
    )

    ax.set_ylabel("Performance Score (0 - 100)", fontsize=10, fontweight="bold")
    ax.set_title(
        "The Comprehension-Generation Gap in Dhivehi LLMs",
        fontsize=11,
        fontweight="bold",
        pad=12,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10, fontweight="bold")
    ax.set_ylim(0, 88)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(
        frameon=True,
        facecolor="white",
        edgecolor="#cccccc",
        fontsize=9,
        loc="upper right",
    )

    for rects in [rects1, rects2, rects3]:
        for rect in rects:
            h = rect.get_height()
            ax.annotate(
                f"{h:.2f}",
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
            )

    plt.tight_layout()
    plt.savefig("paper/fig_gap.pdf", format="pdf")
    plt.close()

    # Figure 4: fig_asymmetry.pdf
    en_dv = [29.21, 27.71, 9.42]
    dv_en = [50.95, 38.40, 40.10]

    width2 = 0.32
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=300)
    r1 = ax.bar(
        x - width2 / 2,
        en_dv,
        width2,
        label="EN->DV (Generates Thaana)",
        color="#8172B2",
        edgecolor="black",
        linewidth=0.6,
    )
    r2 = ax.bar(
        x + width2 / 2,
        dv_en,
        width2,
        label="DV->EN (Generates English)",
        color="#CCB974",
        edgecolor="black",
        linewidth=0.6,
    )

    ax.set_ylabel("Translation chrF Score", fontsize=10, fontweight="bold")
    ax.set_title(
        "Bidirectional Translation Asymmetry (Script Bottleneck)",
        fontsize=11,
        fontweight="bold",
        pad=12,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10, fontweight="bold")
    ax.set_ylim(0, 62)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(
        frameon=True,
        facecolor="white",
        edgecolor="#cccccc",
        fontsize=9,
        loc="upper right",
    )

    for rects in [r1, r2]:
        for rect in rects:
            h = rect.get_height()
            ax.annotate(
                f"{h:.2f}",
                xy=(rect.get_x() + rect.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
            )

    plt.tight_layout()
    plt.savefig("paper/fig_asymmetry.pdf", format="pdf")
    plt.close()


if __name__ == "__main__":
    main()
