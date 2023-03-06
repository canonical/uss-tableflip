# USE PROJECT BOARD INSTEAD

Everything here has been reflected to the [project board](https://github.com/orgs/canonical/projects/29/views/1). This page will no longer be maintained.


# Assumptions
## cloud-init
cloud-init is assumed to be cloned locally with the Canonical cloud-init remote named `upstream` and your personal fork named `origin`. For example,
```bash
$ git remote -v
origin	git@github.com:MyGithubName/cloud-init.git (fetch)
origin	git@github.com:MyGithubName/cloud-init.git (push)
upstream	git@github.com:canonical/cloud-init.git (fetch)
upstream	git@github.com:canonical/cloud-init.git (push)
```
Adjust any references to `upstream` and `origin` accordingly if yours are different.

## Tools on path
Some scripts referenced in this guide invoke other tools assumed to be on the PATH, so add `uss-tableflip/scripts` to your PATH.
Additionally, the `lptools` package and `git-buildpackage` should be installed. Use `apt` to install them.

## Tools Updated For Core Contributors
To avoid repetitive names in the cloud-init changelog, core contributors' names are excluded from the changelog contribution list.

New core contributors should add themselves to the list in the following locations:
* [log2dch](https://github.com/canonical/uss-tableflip/blob/main/scripts/log2dch)

# Pre-release
## Send pre-release email to mailing list
Send an email to the cloud-init mailing list announcing the upcoming release. See previous emails for examples:
* https://lists.launchpad.net/cloud-init/msg00357.html
* https://lists.launchpad.net/cloud-init/msg00335.html

## Perform pre-release checks
* All outstanding merge proposals have been reviewed for merge
* CI is green

## Create upstream-release branch
**SAVE ALL LOCAL CHANGES TO A BRANCH**, then
```bash
git fetch upstream
git checkout main
git reset upstream/main --hard
```

Run `uss-tableflip/scripts/upstream-release <release_version> <old_version>` from cloud-init tree with updated main branch.
The script will:

* Print to stdout the release notes contents to be used later
* Create a local release branch containing a release commit and an updated changelog

**Note:** If a branch other than main was used or main is out of date,
you will get strange entries in Changelog about cherry pick commits or
commits will not match tip of upstream/main.

**Note:**  At this point, running `tox` locally will fail, complaining
that your version does not match what git-describe does.  CI is
configured to work around this problem for release branches, so you
can disregard these local failures.  (We will create a tag later in
the process which fixes this issue.)

Push the branch up for review and create a pull request against main.  We will use that PR for some documentation on things that have been tested.

## Save the release notes

Now that your PR is up and ready for review

* Copy the release notes content minus the changelog to a file called `releasenotes-file` and fill in the highlights.
* Copy the changelog part to a file called `changelog-file`.

**Note:**  There's no real formula for filling in the highlights other than a bulleted list of the 5-ish most noteworthy changes this release. Generally this won't include testing or simple bug fixes.

## Merge branch and tag
After getting approval for your release branch on Github, merge the branch.

Then tag the new commit on upstream/main created by the squash merge:
```bash
$ git fetch; git checkout main; git reset --hard upstream/main
$ git tag --annotate --sign -m 'Release <version>' <version>
```
Then push it:
```bash
$ git push upstream <version>
```
Note that if the reviewer merged your branch, they may have tagged it as well, so check the tags before tagging it yourself.

# Upstream Release
**WAIT UNTIL THE RELEASE BRANCH HAS BEEN MERGED BEFORE PERFORMING THIS SECTION**

## Create release tarball
Tarball *must* be signed.
```bash
$ ./tools/make-tarball
cloud-init-<version>.tar.gz

$ gpg --sign --armor --detach-sig cloud-init-<version>.tar.gz
```

## Create release in Launchpad
Example of a finished release: https://launchpad.net/cloud-init/trunk/21.3

### Option 1: Script
* If [this bug](https://bugs.launchpad.net/lptools/+bug/1974061) is unresolved, skip to Option 2.

```bash
$ lp-project-upload cloud-init <version> cloud-init-<version>.tar.gz <NEXT_version> changelog-file releasenotes-file
```
Note that `<NEXT_version>` in the command is for specifying our next milestone. So if we're currently releasing 21.3, `<NEXT_version>` would be 21.4.

### Option 2: Launchpad UI
Don't do this if you used Option 1 above.

Go to https://launchpad.net/cloud-init/trunk

Scroll to the bottom of 'Milestones and releases' and click '⨁  Create release'

Fill in details:

* **Don't** keep milestone active
* Specify current date for 'Date released'
* Copy the release notes from `releasenotes-file` into the 'Release notes' section
* Copy the changelog from `changelog-file` into the 'Changelog' section.

After creating the release, on the release page, under **Download files for this release**, click 'Add download file'. Set 'Description' to 'Upstream release of \<version\>'. Attach the tarball and signature created earlier and click 'Upload'.

Once we have created our release, we should create the milestone for the next release.
* From https://launchpad.net/cloud-init , under `Series and milestones` (middle of page), click the `trunk` series. If you see no `trunk` series, then click `View full history` and find it there
* Under the `Milestones and releases` section, click the `Create milestone` button
* Set Name to `<next scheduled release>`. For example, if current release is '21.3', Name should be '21.4'
* If we have a scheduled date for the next release, set the date, otherwise leave it blank
* Leave everything else blank, and click `Create Milestone`

## Create release in github
* Visit https://github.com/canonical/cloud-init/releases
* Click 'Draft new release'
* In the 'Choose a tag' dropdown, select tag pushed earlier
* Set `<version>` as Release title
* Use the "Release Highlights" from the email/launchpad/discourse posts as the description ([example here](https://github.com/canonical/cloud-init/releases/tag/22.2))
* Click 'Publish release' (double check this was done, last time it ended up in "draft" state)

## Close bugs
Any Launchdpad bugs that were listed in the git commit messages from this release should be marked as 'fix-released' now.

First, get the list of bugs that been fixed this release:
```bash
$ git log <previous_version>..<version> \
	| grep "^[ ]*LP:" \
	| sort -u \
	| awk -F 'LP: #' '{printf $2 " "}' \
	| sed 's/[,\#]//g'  # strip any loose commas and stray octothorps
```

Next, use the uss-tableflip script called lp-bugs-released to close the bugs:
```bash
$ ./lp-bugs-released <project> <version> <space separated list of bugs>
```
Example:
```bash
$ ./lp-bugs-released cloud-init 21.3 1867532 1911680 1925395 1931392 1931577 1932048 1940233 1940235 1940839
```

The lp-bugs-released script is best effort. Be sure to follow up on Launchpad
any bugs that the script warns about.

## Upload to schemastore:

The first [release](https://www.schemastore.org/api/json/catalog.json) was merged.
This serves as a placeholder for defining a process, testing, etc.

Questions to ask / answer:

1. Does [the catalog](https://www.schemastore.org/api/json/catalog.json) contain a valid link for cloud-init?
2. Does [the schema version file](https://raw.githubusercontent.com/canonical/cloud-init/main/cloudinit/config/schemas/versions.schema.cloud-config.json) have a definition for the latest release?

These checks should be automatable.

## Upload to ubuntu/devel
```bash
$ git fetch upstream
$ git checkout upstream/ubuntu/devel -B ubuntu/devel
$ new_upstream_snapshot.py  # add the Release LP: #
$ <run whatever commands new-upstream-snapshot tells you to run next to finish the release>
```

## Update COPR build cloud-init/el-testing repository with latest upstream release
 Build RPM with:
```bash
$ ./tools/run-container --source-package --unittest --artifacts=./srpm/ rockylinux/8
```
* Load [el-testing project/builds](https://copr.fedorainfracloud.org/coprs/g/cloud-init/el-testing/builds/)
* Click New Build button -> Upload tab -> upload your src.rpm file
* Unselect all 'Chroots' except for 'epel-8-x86_64'
* Click 'Build'

# Post-release
## Send release email and post to Discourse
Example emails:
* https://lists.launchpad.net/cloud-init/msg00362.html
* https://lists.launchpad.net/cloud-init/msg00338.html

Example discourse:
* https://discourse.ubuntu.com/t/release-of-cloud-init-21-3/23857
