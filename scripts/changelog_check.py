#!/usr/bin/python3

# Run from the root of the cloud-init source tree.
# Usage: changelog_check <ubuntu-series>
# Requires rmadison to be installed and in the path.

import os
import re
import subprocess
import sys
import urllib.request
from typing import Tuple
from urllib.error import HTTPError


def get_latest_version(series: str) -> str:
    """Get the latest version of cloud-init for the given series."""
    try:
        output = subprocess.check_output(
            [
                "rmadison",
                "cloud-init",
                "--architecture",
                "source",
                "--url",
                "ubuntu",
            ],
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running rmadison: {e}")
        sys.exit(1)

    # Example line:
    # cloud-init | 24.4.1-0ubuntu0~24.04.3            | noble-updates    | source, all
    # Prefer -updates, then -security, then plain series
    base_pattern = r"cloud-init\s*\|\s*(\S+)\s*\|\s*{series}\s*\|"
    release_pattern = base_pattern.format(series=series)
    updates_pattern = base_pattern.format(series=f"{series}-updates")
    security_pattern = base_pattern.format(series=f"{series}-security")

    for pattern in (updates_pattern, security_pattern, release_pattern):
        match = re.search(pattern, output)
        if match:
            return match.group(1).strip()

    print(f"No cloud-init version found for series '{series}'")
    sys.exit(1)


def fetch_changelog(version: str) -> str:
    """Fetch the changelog for the given version from the Ubuntu changelogs."""
    url = f"https://changelogs.ubuntu.com/changelogs/pool/main/c/cloud-init/cloud-init_{version}/changelog"  # noqa: E501
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode("utf-8")
    except HTTPError as e:
        print(f"Failed to fetch changelog from {url}: {e}")
        sys.exit(1)


def changelog_up_to_date(series: str) -> Tuple[bool, str]:
    """Check that local changelog is up to date with the released changelog."""
    if not os.path.exists("debian/changelog"):
        raise RuntimeError("debian/changelog does not exist")
    version = get_latest_version(series)
    released_changelog = fetch_changelog(version)
    with open("debian/changelog", encoding="utf-8") as f:
        local_changelog = f.read()
    diff = subprocess.run(
        ["diff", "-u", "debian/changelog", "/dev/stdin"],
        input=released_changelog,
        text=True,
        capture_output=True,
        check=False,
    )
    is_up_to_date = local_changelog.endswith(released_changelog)
    return is_up_to_date, diff.stdout + diff.stderr


def main():
    """Main function to check if the changelog is up to date."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <ubuntu-series>")
        sys.exit(1)
    series = sys.argv[1]
    try:
        is_up_to_date, diff_output = changelog_up_to_date(series)
    except RuntimeError as e:
        print(e)
        sys.exit(1)
    if is_up_to_date:
        print("Changelog is up to date")
    else:
        print("Changelog is not up to date")
        print(diff_output)
        sys.exit(1)


if __name__ == "__main__":
    main()
