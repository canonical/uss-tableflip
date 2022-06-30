#!/usr/bin/env python3
"""add_changelog: add unreleased commits to debian/changelog

Use gbp-dch and dch tooling to inject time-ordered changelog comments
for each commit into the package's debian/changelog.

This script is typically invoked from new-upstream-snapshot when pulling
down all upstream commits into a packaging branch.

See:
https://github.com/canonical/uss-tableflip/blob/main/doc/ubuntu_release_process.md
"""

import argparse
import os
import re
import sys
from subprocess import check_output

NEW_UPSTREAM_MSG = "New upstream"
PKG_RELEASE_RE = (
    r"(?P<pkg_name>[^ ]+) \((?P<version>[^)]+)\) (?P<dist>[^;]+);"
    r" urgency=(?P<urgency>\w+).*"
)
CHANGELOG_FILE = "debian/changelog"
GIT_GBP_CONF = ".git/gbp.conf"
PACKAGE_GBP_CONF = "debian/gbp.conf"
PACKAGE_GBP_CUSTOMIZATION = "debian/gbp_format_changelog"

# Passed through to gbp commands
GBP_ENV_VARS = (
    "DEBEMAIL",
    "DEBFULLNAME",
    "EMAIL",
    "GBP_DISABLE_SECTION_DEPRECATION",
    "GBP_DISABLE_GBP_CONF_DEPRECATION",
)
DEFAULT_GBP_CONF = os.path.join(os.path.dirname(__file__), "gbp.conf")
DEFAULT_GBP_CUSTOMIZATION = os.path.join(
    os.path.dirname(__file__), "gbp_format_changelog"
)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("message", help="Changelog message to add")
    parser.add_argument("version", help="Packaging version for changelog")
    parser.add_argument(
        "include_bugs",
        help='Set "true" to include bugs in changelog',
        choices=["true", "false"],
    )
    return parser


def _get_gbp_env():
    """Return a dict of gbp-related environment variables."""
    gbp_env = {}
    for env_var_name in GBP_ENV_VARS:
        if env_var_name in os.environ:
            gbp_env[env_var_name] = os.environ[env_var_name]
    if not any(
        [
            "GBP_CONF_FILES" in gbp_env,
            os.path.exists(PACKAGE_GBP_CONF),
            os.path.exists(GIT_GBP_CONF),
        ]
    ):
        print(
            f"NOTICE: no gbp.conf found in debian/ or .git/."
            f" Using: {DEFAULT_GBP_CONF}"
        )
        gbp_env["GBP_CONF_FILES"] = DEFAULT_GBP_CONF
    return gbp_env


def add_changelog(msg: str, version: str, include_bugs: str = "false"):
    with open(CHANGELOG_FILE) as stream:
        full_changelog = stream.read().splitlines()
    unreleased_snapshot_messages = []  # Upstream snapshot commit messages
    changelog_lines = []
    pkg_info = re.match(PKG_RELEASE_RE, full_changelog[0]).groupdict()
    unreleased_commitish = None
    if pkg_info["dist"] == "UNRELEASED":
        # Reconstruct top changelog entry
        _, _, pkg_commitish = pkg_info["version"].partition("g")
        if len(pkg_commitish) == 8:  # Then we have the commitish
            unreleased_commitish = pkg_commitish
        found_snapshot = False
        changelog_count = 0
        for line in full_changelog:
            if re.match(
                rf"{pkg_info['pkg_name']} .*urgency={pkg_info['urgency']}",
                line,
            ):
                changelog_count += 1
            if NEW_UPSTREAM_MSG in line and changelog_count == 1:
                found_snapshot = True
                continue
            if found_snapshot and changelog_count == 1:
                if line and not line.startswith(" -- "):
                    if NEW_UPSTREAM_MSG not in line:
                        unreleased_snapshot_messages.append(
                            re.sub(r"^ +\+ ?", "+", line)
                        )
                else:
                    changelog_lines.append(line)
            else:
                changelog_lines.append(line)
        if changelog_lines != full_changelog:
            with open(CHANGELOG_FILE, "w") as stream:
                stream.write("\n".join(changelog_lines) + "\n")
    # Add current msg comment
    gbp_cmd = ["gbp", "dch", "--ignore-branch", f"--new-version={version}"]
    for msg_line in msg.splitlines():
        check_output(["dch", "--nomultimaint", "-b", "-v", version, msg_line])
    if pkg_info["dist"] == "UNRELEASED":
        if not unreleased_commitish:
            _, _, pkg_commitish = pkg_info["version"].partition("g")
            if len(pkg_commitish) == 8:
                unreleased_commitish = pkg_commitish
    if not os.path.exists(PACKAGE_GBP_CUSTOMIZATION):
        print(
            f"NOTICE: no {PACKAGE_GBP_CUSTOMIZATION} found. "
            f"Using: {DEFAULT_GBP_CUSTOMIZATION}"
        )
        gbp_cmd += ["--customizations", DEFAULT_GBP_CUSTOMIZATION]
    if unreleased_commitish:
        gbp_cmd += ["-s", unreleased_commitish]
    if include_bugs == "false":
        # Skip any bug matches due in changelog entries
        gbp_cmd += ["--meta-closes-bugnum='MATCHNOBUGS'"]
    if NEW_UPSTREAM_MSG in msg:
        check_output(gbp_cmd, env=_get_gbp_env())
    for msg in unreleased_snapshot_messages:
        check_output(["dch", "-v", version, msg])

    # Post-process some formatting artifacts from gbp_format_changelog
    # when lines are wrapped or indented for scope.
    # Redact ndented scope marker from "* +" to " +"
    check_output(["sed", "-i", "s/ \\* +/   + /", CHANGELOG_FILE])
    # Redact multi-line leading marker "* "
    check_output(["sed", "-i", "s/\\*       /    /", CHANGELOG_FILE])
    # Prepend the 6th leading space for multi-line wrapped entries if only
    # 5 are present. Occurs when text-wrapping [Author Name] or (LP #<ID)
    check_output(["sed", "-i", "/^     [^ ]/{s/^/ /}", CHANGELOG_FILE])


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    try:
        check_output(["gbp", "--help"])
    except Exception:
        print(
            f"ERROR: {os.path.basename(__file__)} requires gbp. Run:"
            " sudo apt install git-buildpackage"
        )
        sys.exit(1)
    add_changelog(
        msg=args.message, version=args.version, include_bugs=args.include_bugs
    )
