import hashlib
import json
import subprocess
import sys
from pathlib import Path

from agent_harness.cli import main


def test_demo_command_runs_end_to_end_and_builds_bound_release(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["demo", "--root", str(tmp_path), "--json"])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["candidate_state"] == "release-ready"
    assert report["mission_completed"] is True
    assert len(report["stage_gate_log"]) == len(report["stages"])
    assert report["ledger_chain_valid"] is True
    assert report["foreign_result"] == "quarantined-foreign-mission"
    assert report["required_research_assurance"] == []
    assert report["release_disposition"] == "release"
    assert "not an independent review" in report["demo_limitations"]
    evidence = json.loads(
        (Path(report["run_root"]) / "evidence-artifacts" / "acceptance-test.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence["exit_code"] == 0
    package = Path(report["release_package"])
    assert package.is_file()
    actual_hash = hashlib.sha256(package.read_bytes()).hexdigest()
    assert actual_hash == report["release_package_sha256"]


def test_python_module_entrypoint_runs_demo(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_harness.cli",
            "demo",
            "--root",
            str(tmp_path / "module-run"),
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert completed.returncode == 0
    report = json.loads(completed.stdout)
    assert report["mission_completed"] is True
