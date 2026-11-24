"""Orquestador diario: actualiza Meta + Google Ads para el mes actual vs. anterior y genera dist/index.html."""

import shutil
import subprocess
import sys
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def compute_periods(today: date) -> tuple[str, str, str, str]:
    """Devuelve (cur_start, cur_end, prev_start, prev_end).
    Si es día 1 del mes, compara el mes recién cerrado vs. el anterior."""
    if today.day == 1:
        cur_end = today - timedelta(days=1)
        cur_start = cur_end.replace(day=1)
    else:
        cur_start = today.replace(day=1)
        cur_end = today

    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end.replace(day=1)
    return (
        cur_start.isoformat(),
        cur_end.isoformat(),
        prev_start.isoformat(),
        prev_end.isoformat(),
    )


def run_step(cmd: list[str]) -> None:
    print(">>>", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(BASE_DIR))


def main() -> None:
    cur_start, cur_end, prev_start, prev_end = compute_periods(date.today())
    py = sys.executable

    run_step([
        py, "fetch_meta_data.py",
        "--cur-start", cur_start, "--cur-end", cur_end,
        "--prev-start", prev_start, "--prev-end", prev_end,
    ])
    run_step([
        py, "fetch_google_data.py",
        "--cur-start", cur_start, "--cur-end", cur_end,
        "--prev-start", prev_start, "--prev-end", prev_end,
    ])
    run_step([py, "build_dashboard.py"])

    dist_dir = BASE_DIR / "dist"
    dist_dir.mkdir(exist_ok=True)
    shutil.copy2(BASE_DIR / "dashboard.html", dist_dir / "index.html")
    print(f"\nListo: {dist_dir / 'index.html'} ({cur_start}..{cur_end} vs {prev_start}..{prev_end})")


if __name__ == "__main__":
    main()
