"""Orquestador diario: descarga series diarias desde Sep 2026 (Meta + Google) y genera dist/index.html."""

import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_step(cmd: list[str]) -> None:
    print(">>>", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(BASE_DIR))


def main() -> None:
    py = sys.executable
    run_step([py, "fetch_meta_data.py", "--since", "2026-09-01"])
    run_step([py, "fetch_google_data.py"])
    run_step([py, "build_dashboard.py"])

    dist_dir = BASE_DIR / "dist"
    dist_dir.mkdir(exist_ok=True)
    shutil.copy2(BASE_DIR / "dashboard.html", dist_dir / "index.html")
    print(f"\nListo: {dist_dir / 'index.html'}")


if __name__ == "__main__":
    main()
