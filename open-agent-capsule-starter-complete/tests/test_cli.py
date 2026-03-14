import shutil
from pathlib import Path

from oac.cli import main

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hello-capsule"
PROFILE = ROOT / "examples" / "adapter-profiles" / "gemini.default.yaml"


def test_cli_validate(capsys) -> None:
    exit_code = main(["validate", str(EXAMPLE)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "valid manifest: hello-capsule" in captured.out


def test_cli_targets(capsys) -> None:
    exit_code = main(["targets"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "codex" in captured.out
    assert "gemini" in captured.out


def test_cli_describe_target(capsys) -> None:
    exit_code = main(["describe-target", "opencode"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "OpenCode" in captured.out
    assert ".opencode/agents" in captured.out


def test_cli_describe_ingest(capsys) -> None:
    exit_code = main(["describe-ingest", "codex"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "codex ingest" in captured.out
    assert "project-rules" in captured.out


def test_cli_validate_profile(capsys) -> None:
    exit_code = main(["validate-profile", str(PROFILE)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "valid profile: gemini.default" in captured.out


def test_cli_scaffold_profile(tmp_path: Path, capsys) -> None:
    output = tmp_path / "opencode.example.test.yaml"
    exit_code = main(["scaffold-profile", "opencode", str(output)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert output.exists()
    assert "wrote profile:" in captured.out


def test_cli_hydrate(capsys, tmp_path: Path) -> None:
    output = tmp_path / "codex"
    exit_code = main(["hydrate", "codex", str(EXAMPLE), str(output)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert (output / "AGENTS.md").exists()
    assert "hydrated: codex" in captured.out


def test_cli_ingest(capsys, tmp_path: Path) -> None:
    output = tmp_path / "codex"
    hydrate_exit = main(["hydrate", "codex", str(EXAMPLE), str(output)])
    assert hydrate_exit == 0
    exit_code = main(["ingest", "codex", str(output), str(EXAMPLE)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ingested: codex" in captured.out
    assert "procedure.workflow" in captured.out


def test_cli_propose(capsys, tmp_path: Path) -> None:
    projection = tmp_path / "codex"
    proposal = tmp_path / "codex-proposal.json"
    assert main(["hydrate", "codex", str(EXAMPLE), str(projection)]) == 0
    exit_code = main(
        [
            "propose",
            "codex",
            str(projection),
            str(EXAMPLE),
            "--output",
            str(proposal),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert proposal.exists()
    assert "proposal bundle: codex" in captured.out


def test_cli_eval_and_conformance(capsys) -> None:
    eval_exit = main(["eval", str(EXAMPLE)])
    eval_output = capsys.readouterr().out
    assert eval_exit == 0
    assert "passed: yes" in eval_output
    conformance_exit = main(["conformance", str(EXAMPLE)])
    conformance_output = capsys.readouterr().out
    assert conformance_exit == 0
    assert "conformance: hello-capsule" in conformance_output


def test_cli_promote_revert_and_snapshot(capsys, tmp_path: Path) -> None:
    capsule = tmp_path / "capsule"
    shutil.copytree(EXAMPLE, capsule)
    projection = tmp_path / "codex"
    proposal = tmp_path / "codex-proposal.json"

    assert main(["hydrate", "codex", str(capsule), str(projection)]) == 0
    assert main(["propose", "codex", str(projection), str(capsule), "--output", str(proposal)]) == 0

    promote_exit = main(["promote", str(proposal), str(capsule), "--apply"])
    promote_output = capsys.readouterr().out
    assert promote_exit == 0
    assert "applied: yes" in promote_output

    promotion_root = capsule / ".oac" / "promotions"
    promotion_reports = list(promotion_root.glob("*/promotion.json"))
    assert promotion_reports, "Expected promotion.json to be written"

    revert_exit = main(["revert", str(promotion_reports[0]), str(capsule), "--apply"])
    revert_output = capsys.readouterr().out
    assert revert_exit == 0
    assert "reverted:" in revert_output

    snapshot_dir = tmp_path / "snapshots"
    snapshot_exit = main(["snapshot", str(capsule), str(snapshot_dir)])
    snapshot_output = capsys.readouterr().out
    assert snapshot_exit == 0
    assert "snapshot:" in snapshot_output
    assert list(snapshot_dir.glob("*.tar.gz"))
