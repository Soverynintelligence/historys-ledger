import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_check_script_exists_and_is_executable():
    path = os.path.join(REPO, "tools", "check.sh")
    assert os.path.exists(path), "tools/check.sh missing"
    assert os.access(path, os.X_OK), "tools/check.sh is not executable"


def test_check_script_runs_the_test_suite_and_the_gate():
    with open(os.path.join(REPO, "tools", "check.sh"), encoding="utf-8") as f:
        body = f.read()
    assert "pytest" in body
    assert "provenance_gate" in body
    assert "build_folios" in body
    assert "stale_open" in body
    assert "open_shelf" in body
