"""Tests for new_upstream_snapshot.py

Requires pytest
"""
import os
from functools import partial
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess
from unittest import mock

import pytest

from scripts.new_upstream_snapshot import (
    ChangelogDetails,
    CliError,
    VersionInfo,
    capture,
    new_upstream_snapshot,
    sh,
)

PACKAGED_VERSION = "1.4"
PACKAGED_NEXT = "2.1"
UPSTREAM_MAIN_VERSION = "2.3"


def new_capture(devel_series, stable_number, *args, **kwargs):
    if args[0] == "distro-info --devel":
        return CompletedProcess(args[0], 0, stdout=devel_series)
    elif args[0] == "distro-info --stable -r":
        return CompletedProcess(args[0], 0, stdout=stable_number)
    return capture(*args, **kwargs)


@pytest.fixture(autouse=True)
def mock_distro_info():
    side_effect = partial(new_capture, "bseries", "10.04")
    with mock.patch(
        "scripts.new_upstream_snapshot.capture", side_effect=side_effect
    ):
        yield


@pytest.fixture()
def mock_new_sru():
    side_effect = partial(new_capture, "cseries", "10.10")
    with mock.patch(
        "scripts.new_upstream_snapshot.capture", side_effect=side_effect
    ):
        yield


@pytest.fixture()
def main_setup(tmp_path):
    commits = []

    previous_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        capture("git init -b main")
    except CalledProcessError as e:
        if "usage: " in e.stderr:
            # Jammy doesn't have a -b switch
            sh("git init")
            sh("git checkout -B main")

    # Create main branch
    for i in range(5):
        sh(f"echo 'line{i}' >> file.txt")
        sh("git add file.txt")
        sh(f"git commit -m 'line{i}\n\nLP: #12345{i}'")
        git_hash = capture("git rev-parse HEAD").stdout.strip()
        commits.append(git_hash)
    sh(
        f"git tag -a {PACKAGED_VERSION} {commits[0]} -m "
        f"'release {PACKAGED_VERSION}' && "
        f"git tag -a {UPSTREAM_MAIN_VERSION} {commits[3]} -m "
        "'release {UPSTREAM_MAIN_VERSION}'"
    )

    yield commits
    os.chdir(previous_dir)


@pytest.fixture()
def devel_setup(main_setup):
    main_commits = main_setup
    # Create ubuntu/devel
    sh(f"git checkout {main_commits[0]} -b ubuntu/devel")
    Path("debian").mkdir()
    Path("debian/changelog").write_text(
        f"cloud-init ({PACKAGED_VERSION}-0ubuntu1) UNRELEASED; "
        "urgency=medium\n\n"
        "  * Initial release\n\n"
        " -- J Doe <j.doe@canonical.com>  Fri, 12 Sep 2008 15:30:32 +0200\n"
    )
    Path("debian/patches").mkdir()
    Path("debian/patches/series").touch()
    sh("git add debian/ && git commit -m 'update changelog'")
    sh(f"cherry-pick --yes {main_commits[1]}")
    sh("git add .pc && git commit --amend --no-edit")
    sh(
        "sed -i -e '1s/UNRELEASED/bseries/' debian/changelog && "
        f"git commit -m 'releasing cloud-init {PACKAGED_VERSION}-0ubuntu1' "
        "debian/changelog && "
        "git checkout main"
    )
    return main_commits


@pytest.fixture()
def series_setup(main_setup):
    main_commits = main_setup
    # Create ubuntu/devel
    sh(f"git checkout {main_commits[0]} -b ubuntu/aseries")
    Path("debian").mkdir()
    Path("debian/changelog").write_text(
        f"cloud-init ({PACKAGED_VERSION}-0ubuntu0~10.04.1) UNRELEASED; "
        "urgency=medium\n\n"
        "  * Initial release\n\n"
        " -- J Doe <j.doe@canonical.com>  Fri, 12 Sep 2008 15:30:32 +0200\n"
    )
    Path("debian/patches").mkdir()
    Path("debian/patches/series").touch()
    sh("git add debian/ && git commit -m 'update changelog'")
    sh(f"cherry-pick --yes {main_commits[1]}")
    sh("git add .pc && git commit --amend --no-edit")
    sh(
        "sed -i -e '1s/UNRELEASED/aseries/' debian/changelog && "
        f"git commit -m 'releasing cloud-init {PACKAGED_VERSION}-0ubuntu0~10.04.1' "  # noqa: E501
        "debian/changelog && "
        "git checkout main"
    )
    return main_commits


def test_devel_new_upstream_snapshot_main(devel_setup, capsys):
    sh("git checkout ubuntu/devel")
    new_upstream_snapshot("main")
    head = capture("git rev-parse HEAD").stdout
    for commit in devel_setup:
        sh(f"git merge-base --is-ancestor {commit} {head}")
    details = ChangelogDetails.get()
    print(Path("debian/changelog").read_text())
    assert f"{PACKAGED_NEXT}~1g{devel_setup[-1][:8]}-0ubuntu1" == str(
        details.version
    )
    assert details.distro == "UNRELEASED"
    assert (
        f"Upstream snapshot based on main at {devel_setup[-1][:8]}."
    ) in details.changes
    assert (
        "Bugs fixed in this snapshot: (LP: #123454, #123453, #123452, #123451)"
        in details.changes
    )
    assert (
        "List of changes from upstream can be found at" not in details.changes
    )
    assert not Path("debian/patches/series").read_text().strip()
    assert len(list(Path("debian/patches").iterdir())) == 1  # only series
    assert "update changelog" in capture("git log -1 --oneline").stdout

    stdout = capsys.readouterr().out
    assert "dch -r -D bseries ''" in stdout
    print(Path("debian/changelog").read_text())


def test_devel_new_upstream_snapshot_tag(devel_setup, capsys):
    sh("git checkout ubuntu/devel")
    new_upstream_snapshot(UPSTREAM_MAIN_VERSION, no_sru_bug=True)
    head = capture("git rev-parse HEAD").stdout
    for commit in devel_setup[:4]:
        sh(f"git merge-base --is-ancestor {commit} {head}")
    with pytest.raises(CalledProcessError):
        sh(f"git merge-base --is-ancestor {devel_setup[4]} {head}")
    details = ChangelogDetails.get()
    assert str(details.version) == f"{UPSTREAM_MAIN_VERSION}-0ubuntu1"
    assert details.distro == "UNRELEASED"
    # The \n here is also ensuring we have no LP on this line
    assert (
        f"Upstream snapshot based on {UPSTREAM_MAIN_VERSION}.\n"
        in details.changes
    )
    assert "List of changes from upstream can be found at" in details.changes
    assert "Bugs fixed in this snapshot" in details.changes

    stdout = capsys.readouterr().out
    assert "dch -r -D bseries ''" in stdout


def test_devel_new_upstream_snapshot_commit(devel_setup, capsys):
    sh("git checkout ubuntu/devel")
    new_upstream_snapshot(devel_setup[2], no_sru_bug=True)
    head = capture("git rev-parse HEAD").stdout
    for commit in devel_setup[:3]:
        sh(f"git merge-base --is-ancestor {commit} {head}")
    for commit in devel_setup[3:]:
        with pytest.raises(CalledProcessError):
            sh(f"git merge-base --is-ancestor {commit} {head}")
    details = ChangelogDetails.get()
    assert f"{PACKAGED_NEXT}~1g{devel_setup[2][:8]}-0ubuntu1" == str(
        details.version
    )
    assert details.distro == "UNRELEASED"
    assert (
        f"Upstream snapshot based on {devel_setup[2][:8]}" in details.changes
    )
    assert (
        "List of changes from upstream can be found at" not in details.changes
    )
    assert "Bugs fixed in this snapshot" in details.changes

    stdout = capsys.readouterr().out
    assert "dch -r -D bseries ''" in stdout


def test_series_new_upstream_snapshot_main(series_setup, capsys):
    sh("git checkout ubuntu/aseries")
    new_upstream_snapshot("main", bug="123456")
    head = capture("git rev-parse HEAD").stdout
    for commit in series_setup:
        sh(f"git merge-base --is-ancestor {commit} {head}")
    details = ChangelogDetails.get()
    assert str(details.version) == f"{PACKAGED_VERSION}-0ubuntu0~10.04.2"
    assert details.distro == "UNRELEASED"
    assert (
        f"Upstream snapshot based on main at {series_setup[-1][:8]}. "
        "(LP: #123456)"
    ) in details.changes
    assert (
        "List of changes from upstream can be found at" not in details.changes
    )
    assert "Bugs fixed in this snapshot" not in details.changes
    assert not Path("debian/patches/series").read_text().strip()
    assert len(list(Path("debian/patches").iterdir())) == 1  # only series

    stdout = capsys.readouterr().out
    assert "dch -r -D aseries ''" in stdout


def test_series_new_upstream_snapshot_tag(series_setup, capsys):
    sh("git checkout ubuntu/aseries")
    new_upstream_snapshot(UPSTREAM_MAIN_VERSION, no_sru_bug=True)
    head = capture("git rev-parse HEAD").stdout
    for commit in series_setup[:4]:
        sh(f"git merge-base --is-ancestor {commit} {head}")
    with pytest.raises(CalledProcessError):
        sh(f"git merge-base --is-ancestor {series_setup[4]} {head}")
    details = ChangelogDetails.get()
    assert str(details.version) == f"{UPSTREAM_MAIN_VERSION}-0ubuntu0~10.04.1"
    assert details.distro == "UNRELEASED"
    assert (
        f"Upstream snapshot based on {UPSTREAM_MAIN_VERSION}"
        in details.changes
    )
    assert "List of changes from upstream can be found at" in details.changes
    assert "Bugs fixed in this snapshot" not in details.changes
    assert "LP" not in details.changes

    stdout = capsys.readouterr().out
    assert "dch -r -D aseries ''" in stdout


def test_series_new_upstream_snapshot_commit(series_setup, capsys):
    sh("git checkout ubuntu/aseries")
    new_upstream_snapshot(series_setup[2], no_sru_bug=True)
    head = capture("git rev-parse HEAD").stdout
    for commit in series_setup[:3]:
        sh(f"git merge-base --is-ancestor {commit} {head}")
    for commit in series_setup[3:]:
        with pytest.raises(CalledProcessError):
            sh(f"git merge-base --is-ancestor {commit} {head}")
    details = ChangelogDetails.get()
    assert str(details.version) == f"{PACKAGED_VERSION}-0ubuntu0~10.04.2"
    assert details.distro == "UNRELEASED"
    assert (
        f"Upstream snapshot based on {series_setup[2][:8]}" in details.changes
    )
    assert (
        "List of changes from upstream can be found at" not in details.changes
    )
    assert "Bugs fixed in this snapshot" not in details.changes

    stdout = capsys.readouterr().out
    assert "dch -r -D aseries ''" in stdout


def test_devel_changelog_from_unreleased(devel_setup):
    sh("git checkout ubuntu/devel")
    new_upstream_snapshot("main~", no_sru_bug=True)
    new_upstream_snapshot("main", no_sru_bug=True)
    details = ChangelogDetails.get()
    assert (
        str(details.version)
        == f"{PACKAGED_NEXT}~2g{devel_setup[-1][:8]}-0ubuntu1"
    )
    assert details.distro == "UNRELEASED"
    assert (
        f"Upstream snapshot based on main at {devel_setup[-1][:8]}"
    ) in details.changes
    print(Path("debian/changelog").read_text())
    expected_changelog = (
        f"   * Upstream snapshot based on main~ at {devel_setup[-2][:8]}.\n"
        "     - Bugs fixed in this snapshot: (LP: #123453, #123452, #123451)\n"
        f"   * Upstream snapshot based on main at {devel_setup[-1][:8]}.\n"
        "     - Bugs fixed in this snapshot: (LP: #123454)"
    )
    assert expected_changelog in details.changes


def test_series_changelog_from_unreleased(series_setup):
    sh("git checkout ubuntu/aseries")
    new_upstream_snapshot("main~", no_sru_bug=True)
    new_upstream_snapshot("main", no_sru_bug=True)
    details = ChangelogDetails.get()
    assert str(details.version) == f"{PACKAGED_VERSION}-0ubuntu0~10.04.2"
    assert details.distro == "UNRELEASED"
    assert (
        f"Upstream snapshot based on main at {series_setup[-1][:8]}"
    ) in details.changes
    assert (
        f"Upstream snapshot based on main~ at {series_setup[-2][:8]}."
    ) in details.changes


def test_new_upstream_snapshot_not_found(devel_setup):
    sh("git checkout ubuntu/devel")
    with pytest.raises(
        CliError, match="Is it a valid commitish or annotated tag"
    ):
        new_upstream_snapshot("12345678")


def test_devel_lp_splitting(devel_setup):
    Path("newfile").write_text("test")
    sh(
        "git add newfile && git commit -m '"
        "LP: #123455\nLP: #123456\nLP: #123457\nLP: #123458'"
    )
    sh("git checkout ubuntu/devel")

    new_upstream_snapshot("main", no_sru_bug=True)
    expected_changelog = (
        "     - Bugs fixed in this snapshot: (LP: #123455, #123456, #123457, #123458)\n"  # noqa: E501
        "       (LP: #123454, #123453, #123452, #123451)"
    )
    details = ChangelogDetails.get()
    assert expected_changelog in details.changes
    print(Path("debian/changelog").read_text())


def test_first_devel_upload(devel_setup, mock_new_sru, capsys):
    sh("git checkout ubuntu/devel")
    new_upstream_snapshot(
        UPSTREAM_MAIN_VERSION, known_first_devel_upload=True, no_sru_bug=True
    )
    details = ChangelogDetails.get()
    assert str(details.version) == f"{UPSTREAM_MAIN_VERSION}-0ubuntu1"
    assert details.distro == "UNRELEASED"
    assert "Bugs fixed in this snapshot" in details.changes
    assert "List of changes from upstream" in details.changes

    stdout = capsys.readouterr().out
    assert "dch -r -D cseries ''" in stdout


def test_first_sru_to_series(devel_setup, mock_new_sru, capsys):
    sh("git checkout ubuntu/devel")
    new_upstream_snapshot(
        UPSTREAM_MAIN_VERSION, no_sru_bug=True, known_first_sru=True
    )
    details = ChangelogDetails.get()
    assert str(details.version) == f"{UPSTREAM_MAIN_VERSION}-0ubuntu0~10.10.1"
    assert details.distro == "UNRELEASED"
    assert "Bugs fixed in this snapshot" not in details.changes
    assert "List of changes from upstream" in details.changes

    stdout = capsys.readouterr().out
    assert "dch -r -D bseries ''" in stdout


def test_refresh_patches(devel_setup):
    sh("git checkout ubuntu/devel")

    sh(
        "quilt new new-patch && "
        "quilt add file.txt && "
        "echo 'patch-stuff' >> file.txt && "
        "quilt refresh && "
        "quilt pop -a && "
        "git add debian/patches/series && "
        "git add debian/patches/new-patch && "
        "git commit -m 'add quilt patch'"
    )
    new_upstream_snapshot(UPSTREAM_MAIN_VERSION, no_sru_bug=True)
    assert "patch-stuff" not in Path("file.txt").read_text()
    sh("quilt push -a")
    assert Path("file.txt").read_text().startswith("line0\npatch-stuff\nline1")
    assert (
        f"refresh patches against {UPSTREAM_MAIN_VERSION}"
        in capture("git log HEAD~ -1 --oneline").stdout
    )


def test_refresh_fail(devel_setup):
    sh("git checkout ubuntu/devel")

    sh(
        "quilt new new-patch && "
        "quilt add file.txt && "
        "rm file.txt && "
        "quilt refresh && "
        "quilt pop -a && "
        "git add debian/patches/series && "
        "git add debian/patches/new-patch && "
        "git commit -m 'add quilt patch'"
    )
    with pytest.raises(CliError, match="Failed applying patch 'new-patch'"):
        new_upstream_snapshot(UPSTREAM_MAIN_VERSION, no_sru_bug=True)

@pytest.mark.parametrize(
    "src_version,major,minor,hotfix,pre_revision,pre_commit,debian,ubuntu",
    (
        ("23.3.3-0ubuntu4~23.04.1",23, 3, None, None, None, 0, 4),
        ("23.1-0ubuntu2", 23, 1, None, None, None, 0, 2),
        ("23.4~3g0cb0b80f-0ubuntu1", 23, 4, None, 3, "0cb0b80f", 0, 1),
    )
)
def test_version_info_from_string(
    src_version,
    major,
    minor,
    hotfix,
    pre_revision,
    pre_commit,
    debian,
    ubuntu,
):
    """Assert VersionInfo from string parses correct attributes"""
    ver = VersionInfo.from_string(src_version)
    assert major == ver.major
    assert minor == ver.minor
    if hotfix:
        assert hotfix == ver.hotfix
    else:
        assert hotfix is None
    if pre_revision:
        assert pre_revision == ver.pre_revision
    else:
        assert pre_revision is None
    if pre_commit:
        assert pre_commit == ver.pre_commit
    else:
        assert pre_commit is None
    assert debian == ver.debian
    assert ubuntu == ver.ubuntu


def test_release_instructions(devel_setup, capsys):
    sh("git checkout ubuntu/devel")
    new_upstream_snapshot("main", no_sru_bug=True)
    pre_changelog = ChangelogDetails.get()
    expected_version = f"{PACKAGED_NEXT}~1g{devel_setup[-1][:8]}-0ubuntu1"
    tag_version = expected_version.replace("~", "_")
    assert str(pre_changelog.version) == expected_version
    assert pre_changelog.distro == "UNRELEASED"

    stdout = capsys.readouterr().out
    assert "dch -r -D bseries ''" in stdout
    assert f"releasing cloud-init version {expected_version}" in stdout
    assert f"git tag ubuntu/{tag_version}" in stdout

    # The "yes" is because dch warns and prompts about the name 'bseries'
    sh(
        "yes | dch -r -D bseries '' && "
        f"git commit -m 'releasing cloud-init version {expected_version}' "
        "debian/changelog && "
        f"git tag {tag_version}"
    )

    post_changelog = ChangelogDetails.get()
    assert str(post_changelog.version) == expected_version
    assert post_changelog.distro == "bseries"
    assert int(post_changelog.timestamp) >= int(pre_changelog.timestamp)
    # Because series went from UNRELEASED->bseries, we know the first line
    # has changed. Verify that the bulleted entries under the first line
    # have not changed
    assert (
        pre_changelog.changes.splitlines()[1:]
        == post_changelog.changes.splitlines()[1:]
    )
