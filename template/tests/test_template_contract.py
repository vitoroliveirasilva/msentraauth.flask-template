from pathlib import Path


def test_expected_application_structure_exists() -> None:
    root = Path(__file__).parents[1]
    assert (root / "src").is_dir()
    assert (root / "docs" / "ARCHITECTURE.md").is_file()
    assert (root / ".env.example").is_file()


def test_no_legacy_template_package_name() -> None:
    root = Path(__file__).parents[1]
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*.py")
    )
    assert "msentraauth" + "_template" not in text
