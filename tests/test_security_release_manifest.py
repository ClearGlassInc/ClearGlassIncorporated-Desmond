from tools.security_release_manifest import (
    DEFAULT_OUTPUT,
    IMPORTANT_FILES,
    build_manifest,
    digest,
    serialize,
)


def test_the_committed_manifest_matches_the_files_it_pins() -> None:
    """The gate reads the committed file; these tests only read the builder.

    `Pages Artifact Safety and Provenance` runs
    `security_release_manifest.py --check` and stops the deploy when the
    committed manifest no longer matches IMPORTANT_FILES. Nothing in the test
    suite noticed, so editing any pinned file — build_pages.py, _headers,
    pages.yml, the legal pages — left pytest green and turned that gate red
    after the merge, repeatedly. Fail here instead, where the fix is one
    command: python3 tools/security_release_manifest.py
    """
    committed = DEFAULT_OUTPUT.read_text(encoding="utf-8")
    assert committed == serialize(build_manifest()), (
        "stale provenance manifest — run: python3 tools/security_release_manifest.py"
    )


def test_manifest_is_complete_and_uses_sha256() -> None:
    manifest = build_manifest()
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, list)
    assert [artifact["path"] for artifact in artifacts] == list(IMPORTANT_FILES)
    assert all(len(artifact["sha256"]) == 64 for artifact in artifacts)


def test_digest_changes_when_content_changes(tmp_path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("first", encoding="utf-8")
    first = digest(artifact)
    artifact.write_text("second", encoding="utf-8")
    assert digest(artifact) != first
