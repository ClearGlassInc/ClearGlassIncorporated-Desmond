from tools.build_pages import (
    DENIED_TOP_LEVEL,
    PUBLIC_DENIED_TREE_EXCEPTIONS,
    PUBLIC_MARKDOWN,
    build,
    public_relative_paths,
)


def test_public_inventory_excludes_source_and_private_trees() -> None:
    paths = public_relative_paths()
    assert paths
    assert all(
        path.parts[0] not in DENIED_TOP_LEVEL
        or any(path.is_relative_to(exception) for exception in PUBLIC_DENIED_TREE_EXCEPTIONS)
        for path in paths
    )
    assert not any(path.suffix in {".py", ".sql", ".tf", ".env", ".yml", ".yaml"} for path in paths)
    assert not any(path.name in {"package.json", "package-lock.json", "pyproject.toml"} for path in paths)


def test_public_markdown_is_explicit() -> None:
    markdown = {path.as_posix() for path in public_relative_paths() if path.suffix == ".md"}
    assert markdown == PUBLIC_MARKDOWN


def test_build_contains_required_pages_artifacts(tmp_path) -> None:
    destination = tmp_path / "dist"
    count = build(destination)
    assert count > 0
    assert (destination / "index.html").is_file()
    assert (destination / ".nojekyll").is_file()
    assert (destination / ".well-known" / "security.txt").is_file()
    assert not (destination / ".github").exists()
