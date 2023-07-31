#!/usr/bin/python3
# Python 3.6+
"""Update current branch with commitish.
For the average upstream snapshot, this is roughly equivalent to:

Run git merge main.
Remove any cpick* files in debian/patches that exist in main.
For every other quilt patch run a quilt push and quilt refresh.
Commit all quilt refresh changes (if any).
Update changelog accordingly.
Print release instructions.

The commitish defaults to 'main'
"""

import argparse
import re
import subprocess
import sys
from functools import partial
from pathlib import Path
from subprocess import CalledProcessError
from typing import NamedTuple, Optional, Tuple

sh = partial(subprocess.run, check=True, shell=True)
capture = partial(sh, capture_output=True, universal_newlines=True)

QUILT_COMMAND = "quilt --quiltrc -"
QUILT_DIFF_ARGS = "-p ab --no-timestamps --no-index"
QUILT_ENV = {
    "QUILT_PATCHES": "debian/patches",
    "QUILT_DIFF_OPTS": "-p",
    "QUILT_PATCH_OPTS": "--reject-format=unified",
    "QUILT_DIFF_ARGS": f"{QUILT_DIFF_ARGS} --color=auto",
    "QUILT_REFRESH_ARGS": f"{QUILT_DIFF_ARGS}",
    "LANG": "C",
}


class CliError(Exception):
    pass


class ChangelogDetails(NamedTuple):
    # This should be cleaner with dataclasses
    source: str
    version: str
    distro: str
    urgency: str
    maintainer: str
    timestamp: str
    date: str
    bugs_fixed: str
    changes: str

    @classmethod
    def get(cls, offset=0):
        results = capture(
            f"dpkg-parsechangelog --count=1 --offset={offset}"
        ).stdout.strip()
        source = version = distro = urgency = ""
        maintainer = timestamp = date = bugs_fixed = changes = ""
        for line in results.splitlines():
            if line.startswith("Source"):
                source = line.split(": ")[1]
            elif line.startswith("Version"):
                version = line.split(": ")[1]
            elif line.startswith("Distribution"):
                distro = line.split(": ")[1]
            elif line.startswith("Urgency"):
                urgency = line.split(": ")[1]
            elif line.startswith("Maintainer"):
                maintainer = line.split(": ")[1]
            elif line.startswith("Timestamp"):
                timestamp = line.split(": ")[1]
            elif line.startswith("Date"):
                date = line.split(": ")[1]
            elif line.startswith("Launchpad-Bugs-Fixed"):
                bugs_fixed = line.split(": ")[1]
            elif line.startswith("Changes"):
                index = results.index("Changes:")
                changes = results[index + len(line) + 1 :]
                break
            else:
                raise CliError(
                    f"Could not parse 'debian/changelog' line: {line}"
                )
        return cls(
            source,
            version,
            distro,
            urgency,
            maintainer,
            timestamp,
            date,
            bugs_fixed,
            changes,
        )


def get_changelog_distro():
    """Get the distro represented by this changelog.

    The first line of d/changelog displays the distro. Since it can be
    UNRELEASED, check the most recent entries until we find one.
    """
    for i in range(5):
        details = ChangelogDetails.get(offset=i)
        changelog_distro = details.distro
        if changelog_distro != "UNRELEASED":
            break
    else:
        raise CliError("Could not determine distro from changelog")
    return changelog_distro


def remove_line_from_file(filename, text):
    """Utility function to remove a single line from a file."""
    with open(filename, "r") as f:
        lines = f.readlines()
    with open(filename, "w") as f:
        for line in lines:
            if line.strip() != text.strip():
                f.write(line)


def merge_commitish(to: str) -> None:
    """Perform 'git merge <commitish>' along with some error checking."""
    try:
        ref_name = capture(f"git describe --abbrev=8 {to}").stdout.strip()
    except CalledProcessError as e:
        raise CliError(
            f"'git describe' failed for {to}. "
            "Is it a valid commitish or annotated tag?"
        ) from e

    if to == "upstream/main":
        capture("git fetch upstream")
    command = f'git merge {to} -m "merge from {to} at {ref_name}"'
    print(f"Running: {command}")
    capture(command)


def drop_cpicks(commitish):
    """Drop any cpick files in d/p that we've pulled in from main.

    Cpick files have their commit specified in the filename.
    """
    print("Dropping any cpicks that we've pulled in from main")
    dropped_cpicks = []
    for cpick in Path("debian/patches").glob("cpick*"):
        git_hash = cpick.name.split("-")[1]
        is_ancestor = (
            sh(
                f"git merge-base --is-ancestor {git_hash} {commitish}",
                check=False,
            ).returncode
            == 0
        )
        if is_ancestor:
            print(
                f"Dropping file {cpick.name} as it is contained in the "
                "upstream snapshot"
            )
            dropped_cpicks.append(cpick.name)
            remove_line_from_file("debian/patches/series", cpick.name)
            cpick.unlink()
    if dropped_cpicks:
        commit_msg = (
            f"drop cherry picks included in {commitish}.\n\n"
            "drop the following cherry picks:\n" + "\n".join(dropped_cpicks)
        )
        sh(f"git add debian/patches && git commit -m '{commit_msg}'")


def refresh_patches(commitish) -> bool:
    """Refresh any non-cpick quilt patches.

    For every quilt patch run:
      quilt next
      quilt push
      quilt refresh

    Changes from refresh will automatically be committed without prompting.

    If automatic refresh fails, the script will exit with failure. It
    is up to the user to manually fix the quilt patches and then rerun
    the script with the '--post quilt' argument.

    :return: True when patches were refreshed
    """
    print("Attempting to automatically refresh quilt patches")
    try:
        while (
            sh(f"{QUILT_COMMAND} next", check=False, env=QUILT_ENV).returncode
            == 0
        ):
            sh(f"{QUILT_COMMAND} push", env=QUILT_ENV)
            sh(f"{QUILT_COMMAND} refresh", env=QUILT_ENV)
    except CalledProcessError as e:
        failed_patch = capture(
            f"{QUILT_COMMAND} next", env=QUILT_ENV
        ).stdout.strip()
        raise CliError(
            f"Failed applying patch '{failed_patch}'. Patch must be refreshed "
            "manually. When you can successfully "
            "'quilt push -a && quilt pop -a' rerun this script with "
            "'--post quilt' argument."
        ) from e
    rc = sh(f"{QUILT_COMMAND} pop -a", check=False, env=QUILT_ENV).returncode
    if rc not in [0, 2]:  # 2 means there were no quilt patches to pop
        raise CliError(f"'quilt pop -a' unexpectedly returned {rc}.")

    # Now commit the refreshed patches
    patches = capture(
        "git diff --name-only debian/patches/", check=False
    ).stdout.splitlines()
    if patches:
        commit_msg = (
            f"refresh patches against {commitish}\n\n"
            f"patches: \n" + "\n".join(patches)
        )
        sh(f"git commit -m '{commit_msg}' {' '.join(patches)}")
        return True
    else:
        print("No patches needed refresh")
        return False


def is_commitish_upstream_tag(commitish):
    """Return true if the commitish is an upstream tag.

    I.e., In the form of "x.y" or "x.y.z"
    """
    parts = commitish.split(".")
    if len(parts) not in (2, 3):
        return False
    for part in parts:
        try:
            int(part)
        except ValueError:
            return False
    return True


def format_devel_bugs_fixed(bugs_fixed):
    """Format the bugs fixed in devel accordingly.

    If the bugs can all fit on one line, we want a line like:
        - Bugs fixed in this snapshot: (LP: #1111111, #2222222, #3333333)

    If there are too many bugs for one line, we want something like:
        - Bugs fixed in this snapshot: (LP: #1111111, #2222222, #3333333)
          (LP: #4444444, #5555555, #6666666, #7777777)

    """
    bugs_fixed = [f"#{bug}" for bug in bugs_fixed]
    tmp_fixed = ", ".join(bugs_fixed)
    tmp_fixed = (
        "\n    - Bugs fixed in this snapshot: "
        f"(LP: {', '.join(bugs_fixed)})"
    )
    bugs_fixed_lines = []
    while len(tmp_fixed) > 79:
        # 78 here because we need room for the )
        split_index = tmp_fixed[:78].rfind(" ")
        # -1 here because we need to chop the trailing commaq
        bugs_fixed_lines.append(f"{tmp_fixed[:split_index-1]})")
        tmp_fixed = f"      (LP: {tmp_fixed[split_index + 1:]}"
    bugs_fixed_lines.append(tmp_fixed)
    return "\n".join(bugs_fixed_lines)


def get_changelog_message(commitish, bug, is_upstream_tag, is_devel):
    """Get the "changes" message for d/changelog.

    This will vary based on if the commitish is an upstream tag, if there's
    an SRU bug, and if this is a devel upload with LPs fixed.

    Generally, it will look something like this for SRUs:
    * Upstream snapshot based on <commitish>. (LP: #1111111)
      List of changes from upstream can be found at
      https://raw.githubusercontent.com/canonical/cloud-init/<commitish>/ChangeLog

    and something like this for devel uploads:
    * Upstream snapshot based on <commitish>
      - Bugs fixed in this snapshot: (LP: #1111111, #2222222, #3333333)
    """
    if is_upstream_tag:
        target = commitish
        release_text = (
            "\n    List of changes from upstream can be found at\n"
            "    https://raw.githubusercontent.com/canonical/cloud-init/"
            f"{commitish}/ChangeLog"
        )
    else:
        commit = capture(f"git rev-parse --short=8 {commitish}").stdout.strip()
        target = (
            commit
            if commitish.startswith(commit)
            else f"{commitish} at {commit}"
        )
        release_text = ""
    bug_text = f" (LP: #{bug})." if bug else ""
    bugs_fixed_msg = ""
    bugs_fixed = list(get_bugs_fixed_devel())
    if is_devel and bugs_fixed:
        bugs_fixed_msg = format_devel_bugs_fixed(bugs_fixed)
    return (
        "  * Upstream snapshot based on "
        f"{target}.{bug_text}{release_text}{bugs_fixed_msg}"
    )


def get_original_head():
    """Get the original head before the upstream snapshot merge"""
    for i in range(5):
        commitish = f"HEAD~{i}"
        if capture(f"git cat-file -p {commitish}").stdout.count("parent") > 1:
            return f"HEAD~{i+1}"
    raise CliError("No recent merge. Can't continue")


def get_bugs_fixed_devel():
    """Get all bugs fixed in this upstream snapshot.

    Search for any `LP: #` in the git log for commits between the original
    branch HEAD and the new branch HEAD.
    """
    orig_head = get_original_head()
    commit_msgs = capture(f"git log {orig_head}..HEAD").stdout.strip()
    for line in commit_msgs.splitlines():
        if line.strip().startswith("LP: #"):
            yield line.split("LP: #")[1].strip()


def increment_major_version(original: str) -> str:
    """Given a version number, increment and return the major version.

    Examples:
    22.1 -> 22.2
    22.2.3 -> 22.3
    22.3.4~literally-anything -> 22.4
    22.4 -> 23.1
    """
    split = original.split(".", 1)
    major = int(split[0])
    minor = int(split[1][0]) + 1
    if minor == 5:
        major += 1
        minor = 1
    return f"{major}.{minor}"


def update_changelog(
    commitish,
    bug,
    changelog_details: ChangelogDetails,
    is_devel,
    first_devel_upload,
):
    """Update the changelog with the new details.

    Specifically, get the changelog message, determine the new version, then
    use `dch` to write out a blank message and fill it in ourselves, then
    commit.. We fill it in ourselves because the `dch` formatting sucks.
    """
    print("Updating changelog")
    old_version = changelog_details.version
    previously_unreleased = changelog_details.distro.upper() == "UNRELEASED"
    commitish_is_upstream_tag = is_commitish_upstream_tag(commitish)
    next_series_suffix = get_next_series_suffix(old_version)

    msg = get_changelog_message(
        commitish, bug, commitish_is_upstream_tag, is_devel
    )

    # Determine new changelog version
    changelog_version = ""
    if commitish_is_upstream_tag:
        # Upstream tag always takes priority. For 22.1:
        # 22.1-0ubuntu1 on devel
        # 22.1-0ubuntu0~22.04.1 on jammy
        if is_devel:
            if not previously_unreleased or first_devel_upload:
                changelog_version = f"{commitish}-0ubuntu1"
        elif next_series_suffix:
            changelog_version = f"{commitish}-0ubuntu0~{next_series_suffix}"
        else:
            # If it's not devel and it doesn't have a series suffix, then
            # this is the first SRU to a series
            series_number = capture("distro-info --stable -r").stdout.strip()
            changelog_version = f"{commitish}-0ubuntu0~{series_number}.1"
    elif is_devel:
        # If not an upstream tag, then bump current number. For devel this
        # looks something like:
        # 22.1~1g12ab34cd-0ubuntu1 -> 22.1~2g12ab34ce-0ubuntu1
        #
        # Note that even if the version stays unreleased, we're going to
        # increment the ~<num> as it's intended to be less of a significant
        # version number and more a way to ensure newer releases sort higher
        git_hash = capture(
            f"git rev-parse --short=8 {commitish}"
        ).stdout.strip()
        if "~" in old_version:
            v = old_version
            increment = int(v[v.find("~") + 1 : v.find("g")]) + 1
            prefix = old_version.split("~")[0]
        else:
            upstream_version = old_version.split("-")[0]
            prefix = increment_major_version(upstream_version)
            increment = 1
        changelog_version = f"{prefix}~{increment}g{git_hash}-0ubuntu1"
    elif previously_unreleased:
        # If we our previous snapshot went UNRELEASED, then there's no reason
        # to bump the version number
        changelog_version = old_version
    elif next_series_suffix:
        # If it's not an upstream tag or devel, we're just bumping the suffix
        # E.g.,:
        # 22.1-0ubuntu0~22.04.1 -> 22.1-0ubuntu0~22.04.2
        changelog_version = (
            f"{old_version.rsplit('~')[0]}~{next_series_suffix}"
        )
    else:
        raise CliError(
            "Shouldn't be here. There is an bug in "
            "`new_upstream_snapshot.py`. Stopping as version number "
            "is likely to be wrong. "
        )

    dch_command = f"dch --no-multimaint --newversion '{changelog_version}' ' '"
    # Add new changelog entry with blank changelog message
    sh(dch_command)

    # Fill in the changelog message
    add_msg_to_changelog(msg)

    # Commit the changelog
    sh(
        "git commit -m 'update changelog (new upstream snapshot)' "
        "debian/changelog"
    )


def add_msg_to_changelog(msg):
    """`dch` added an empty changelog message, now fill it in."""
    changelog_path = Path("debian/changelog")
    changelog = changelog_path.read_text()
    if changelog.count("  *\n") != 1:
        raise CliError(
            "debian/changelog has more than one blank changelog entry. "
            "Not sure how to proceed."
        )
    with changelog_path.open("w") as f:
        for line in changelog.splitlines():
            if line == "  *":
                line = msg
            f.write(f"{line}\n")


def get_next_series_suffix(old_version):
    """Get the suffix (if it exists) for the next release version

    Any SRUed release should end with <series-number>.x. E.g.
    1.0-0ubuntu0~10.04.1
    The series suffix returned would be "10.04.2".

    Devel releases will return None.
    """
    if "~" not in old_version:
        return None  # I.e., it's a devel upload
    elif old_version.count("~") == 1:
        old_series_suffix = old_version.split("~")[1]
        if "." not in old_series_suffix:
            # Devel has ~ but no series suffix.
            # E.g., 23.2.1~1g111f1a6e-0ubuntu1
            return None
        parts = old_series_suffix.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    else:
        raise CliError(
            "Don't know what to do with multiple '~' in version number"
        )


def show_release_steps(changelog_details, devel_distro, is_devel):
    """Because we all like automation telling us to do more things."""
    series = devel_distro if is_devel else changelog_details.distro
    if series.upper() == "UNRELEASED":
        series = get_changelog_distro()
    new_version = ChangelogDetails.get().version
    git_branch_name = capture("git rev-parse --abbrev-ref HEAD").stdout.strip()
    m = re.match(
        r"^(?P<package_version>\d+\.\d+(\.\d+)?).*", changelog_details.version
    )
    new_tag = new_version.replace("~", "_")
    if "ubuntu" in new_tag and not new_tag.startswith("ubuntu/"):
        new_tag = f"ubuntu/{new_tag}"

    print("To release:")
    print(f"dch -r -D {series} ''")
    print(
        f"git commit -m 'releasing cloud-init version {new_version}' "
        "debian/changelog"
    )
    print(f"git tag {new_tag}")
    print("")
    print(
        "Don't forget to include previously released changelogs from "
        f"upstream/{git_branch_name}-{m['package_version']}.x!"
    )


def get_possible_devel_options(
    known_first_devel_upload, known_first_sru, changelog_details
) -> Tuple[str, bool, bool, bool]:
    """Determine if we're on devel and our options for the devel branch.

    If we're on a devel branch and the changelog distro doesn't match
    the current devel release, we have no way of determining whether this
    is a new devel upload or a new SRU. If the user provided no flags telling
    us what to do, we have to ask.
    """
    is_devel = is_first_devel_upload = known_first_devel_upload
    is_first_sru = known_first_sru
    devel_distro = capture("distro-info --devel").stdout.strip()
    if is_first_devel_upload and is_first_sru:
        raise CliError(
            "Can't simultaneously be first SRU and first devel upload"
        )
    if (
        not known_first_devel_upload
        and not known_first_sru
        and not re.match(r".*~\d+\.\d+\.\d+", changelog_details.version)
    ):
        changelog_distro = get_changelog_distro()
        is_devel = True
        if devel_distro != changelog_distro:
            # Changelog shows devel release numbers, but not the current devel
            # release. We need to know whether this is a new devel upload
            # or the first SRU upload for a series.
            print(
                f"d/changelog shows current devel distro as "
                f"{changelog_distro}, yet `distro-info` says it is "
                f"{devel_distro}."
            )
            if (
                input(
                    f"Is this the first devel upload for {devel_distro} "
                    "(y/N)? "
                ).lower()
                == "y"
            ):
                is_devel = True
                is_first_devel_upload = True
            elif (
                input(
                    f"Is this the first SRU for series {changelog_distro} "
                    "(y/N)? "
                ).lower()
                == "y"
            ):
                is_devel = False
                is_first_sru = True
    return devel_distro, is_devel, is_first_devel_upload, is_first_sru


def get_sru_bug(bug, no_sru_bug):
    """Ask the user for an SRU bug if they did not provide one.

    Don't ask if they tell us not to ask.
    """
    if not bug and not no_sru_bug:
        bug = input(
            "No SRU bug. Enter one now or leave blank for no SRU bug: "
        ).strip()
        if not bug:
            bug = None
    return bug


def new_upstream_snapshot(
    commitish: str,
    bug: Optional[str] = None,
    known_first_devel_upload: bool = False,
    no_sru_bug: bool = False,
    known_first_sru: bool = False,
    post_stage: Optional[str] = None,
) -> None:
    """Perform a new upstream snapshot.

    At a high level, this means:
     - Merge the specified commitish
     - Drop any cpick files included in the snapshot
     - Refresh all quilt patches on the branch
     - Update the changelog accordingly
     - Tell user how to release this update
    """
    if not Path("debian/changelog").exists():
        raise CliError(
            "No debian/changelog found. Are we in the right dir or branch?"
        )

    old_changelog_details = ChangelogDetails.get()
    skip_past_merge = post_stage in {"merge", "quilt"}
    skip_past_quilt = post_stage == "quilt"

    if not skip_past_merge:
        merge_commitish(commitish)
    if not skip_past_quilt:
        drop_cpicks(commitish)
        refresh_patches(commitish)

    # If arguments haven't been passed, we have a few things to determine
    (
        devel_distro,
        is_devel,
        first_devel_upload,
        first_sru,
    ) = get_possible_devel_options(
        known_first_devel_upload=known_first_devel_upload,
        known_first_sru=known_first_sru,
        changelog_details=old_changelog_details,
    )
    bug = None if is_devel else get_sru_bug(bug, no_sru_bug)
    update_changelog(
        commitish,
        bug,
        old_changelog_details,
        is_devel,
        first_devel_upload,
    )

    show_release_steps(old_changelog_details, devel_distro, is_devel)


def parse_args() -> argparse.Namespace:
    """
    Parsing arguments in Python
    Is quite simple and fun
    Just use the argparse module
    And your script will be done!
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-c",
        "--commitish",
        required=False,
        default="upstream/main",
        type=str,
        help="Commitish (tag, branch name, or commit) to merge to",
    )
    parser.add_argument(
        "-b",
        "--bug",
        required=False,
        type=str,
        help="SRU bug number to add to debian/changelog",
    )
    parser.add_argument(
        "-d",
        "--first-devel-upload",
        required=False,
        default=False,
        action="store_true",
        help=(
            "Provide this flag when this is the first upload to a devel "
            "series. It will determine the right version suffix. If not "
            "provided, it may be determined interactively."
        ),
    )
    parser.add_argument(
        "-n",
        "--no-sru-bug",
        required=False,
        action="store_true",
        help=("Do not add (or prompt for) SRU bug reference."),
    )
    parser.add_argument(
        "-p",
        "--post-stage",
        required=False,
        default=None,
        type=str,
        choices=["merge", "quilt"],
        help=(
            "Run with this flag if script previously failed because you had "
            "to manually fix the branch due to a merge or having to refresh "
            "quilt patches. It assumes the steps prior to and including "
            "this stage have already been run and will run the remaining "
            "steps accordingly."
        ),
    )
    parser.add_argument(
        "-s",
        "--first-sru",
        required=False,
        default=False,
        action="store_true",
        help=(
            "Provide this flag when this is the first SRU to a series. "
            "It will determine the right version suffix. If not provided, "
            "it may be determined interactively."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        new_upstream_snapshot(
            args.commitish,
            args.bug,
            args.first_devel_upload,
            args.no_sru_bug,
            args.first_sru,
            args.post_stage,
        )
    except CliError as e:
        print(e)
        sys.exit(1)
