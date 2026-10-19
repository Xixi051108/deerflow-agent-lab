"""Keep generated runtime skills outside the backend lint surface."""

import subprocess
import sys
from pathlib import Path


def test_ruff_ignores_runtime_skill_copies(tmp_path: Path) -> None:
    runtime = tmp_path / ".deer-flow" / "skills_view"
    runtime.mkdir(parents=True)
    (runtime / "generated.py").write_text("undefined_runtime_name\n", encoding="utf-8")
    (tmp_path / "source.py").write_text("answer = 42\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(Path(__file__).resolve().parents[1] / "ruff.toml"), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
