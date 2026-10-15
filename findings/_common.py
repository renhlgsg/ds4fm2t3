"""Helpers shared by the findings scripts."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import settings

REPORTS = settings.PROJECT_ROOT / "reports"
FIG = REPORTS / "figures"
TAB = REPORTS / "tables"
NUMS = REPORTS / "key_numbers.json"
for d in (FIG, TAB):
    d.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, GREY, RED, GREEN = "#1f4e79", "#e07b39", "#8c8c8c", "#c0392b", "#2e8b57"
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": .25, "font.size": 10})


def save_fig(fig, name: str) -> Path:
    p = FIG / f"{name}.png"
    fig.tight_layout()
    fig.savefig(p)
    plt.close(fig)
    return p


def record(key: str, value) -> None:
    """Persist a headline number so slides/report quote exactly what the code computed."""
    data = json.loads(NUMS.read_text()) if NUMS.exists() else {}
    data[key] = value
    NUMS.write_text(json.dumps(data, indent=2, default=str))
