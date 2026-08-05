from tools.build_pages import (
    ROOT,
    DENIED_TOP_LEVEL,
    PUBLIC_DATA_FEEDS,
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
        or path.as_posix() in PUBLIC_DATA_FEEDS
        for path in paths
    )
    assert not any(path.suffix in {".py", ".sql", ".tf", ".env", ".yml", ".yaml"} for path in paths)
    assert not any(path.name in {"package.json", "package-lock.json", "pyproject.toml"} for path in paths)


def test_public_markdown_is_explicit() -> None:
    markdown = {path.as_posix() for path in public_relative_paths() if path.suffix == ".md"}
    assert markdown == PUBLIC_MARKDOWN


def test_allowlisted_data_feeds_reach_the_artifact(tmp_path) -> None:
    """The live dashboards fetch these; a denied data/ tree served them 404s."""
    destination = tmp_path / "dist"
    build(destination)
    for feed in PUBLIC_DATA_FEEDS:
        assert (destination / feed).is_file(), f"{feed} missing from the artifact"


def test_only_allowlisted_data_files_are_published(tmp_path) -> None:
    """data/ also holds internal working state — nothing may ride along."""
    destination = tmp_path / "dist"
    build(destination)
    published = {
        path.relative_to(destination).as_posix()
        for path in (destination / "data").rglob("*")
        if path.is_file()
    }
    assert published == PUBLIC_DATA_FEEDS


def test_every_allowlisted_feed_exists_in_the_repo() -> None:
    """A renamed or deleted feed must fail here, not silently 404 in a browser."""
    missing = [feed for feed in PUBLIC_DATA_FEEDS if not (ROOT / feed).is_file()]
    assert missing == [], f"allowlisted but absent: {missing}"


def test_build_contains_required_pages_artifacts(tmp_path) -> None:
    destination = tmp_path / "dist"
    count = build(destination)
    assert count > 0
    assert (destination / "index.html").is_file()
    assert (destination / ".nojekyll").is_file()
    assert (destination / ".well-known" / "security.txt").is_file()
    assert not (destination / ".github").exists()
