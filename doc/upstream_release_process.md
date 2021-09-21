This covers the cloud-init upstream release process.

This document assumes the Canonical cloud-init remote is named `upstream` whereas your personal fork is named `origin`. For example,
```bash
$ git remote -v
origin	git@github.com:MyGithubName/cloud-init.git (fetch)
origin	git@github.com:MyGithubName/cloud-init.git (push)
upstream	git@github.com:canonical/cloud-init.git (fetch)
upstream	git@github.com:canonical/cloud-init.git (push)
```

Adjust any references to `upstream` and `origin` accordingly if yours are different.

# Pre-release
## Send pre-release email to mailing list
Send an email to the cloud-init mailing list announcing the upcoming release. See previous emails for examples:
* https://lists.launchpad.net/cloud-init/msg00357.html
* https://lists.launchpad.net/cloud-init/msg00335.html

## Perform pre-release checks
* All outstanding merge proposals have been reviewed for merge
* CI is green

## Start upstream release bug
Start creating a process bug in the cloud-init project that captures the new release version, highlights, and changelog.

Use the `upstream-release` script (described in the next section) to generate the bug contents for you.

See [previous release bugs in Launchpad](https://bugs.launchpad.net/cloud-init/+bugs?field.searchtext=Release&orderby=-datecreated&search=Search&field.status%3Alist=FIXRELEASED&field.importance%3Alist=UNDECIDED).


## Create upstream-release branch
**SAVE ALL LOCAL CHANGES TO A BRANCH**, then
```bash
git fetch upstream
git checkout main
git reset upstream/main --hard
```

Run `uss-tableflip/scripts/upstream-release <release_version> <old_version>` from cloud-init tree with updated main branch.
The script will:
* Prompt you to create the bug you created in the previous section (it doesn't create it for you)
* Generate the contents to be pasted into the bug description. At this point you should finish creating the bug. You can finish the TODO later
* Prompt you to enter the bug number of the created bug
* Create a local release branch containing a release commit and an updated changelog

**Note:** If a branch other than main was used or main is out of date,
you will get strange entries in Changelog about cherry pick commits or
commits will not match tip of upstream/main.

**Note:**  At this point, running `tox` locally will fail, complaining
that your version does not match what git-describe does.  CI is
configured to work around this problem for release branches, so you
can disregard these local failures.  (We will create a tag later in
the process which fixes this issue.)

Push the branch up for review and create a pull request.  We will use that PR for some documentation on things that have been tested.

## Fill in launchpad bug highlights
Now that your PR is up and ready for review, go back to the launchpad bug you created and fill in the highlights. There's no real formula for this other than a bulleted list of the 5-ish most noteworthy changes this release. Generally this won't include testing or simple bug fixes.

## Merge branch and tag
After getting approval for your release branch, merge the branch to main, then tag (annotated and signed):
```bash
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
* Install the lptools package through apt
* Copy the changelog (for *just* this release) to a file called 'changelog-file'
* Copy the release notes (not including changelog) from the launchpad bug to a file called 'releasenotes-file'
```bash
$ lp-project-upload cloud-init <version> cloud-init-<version>.tar.gz <NEXT_version> changelog-file releasenotes-file
```
Note that `<NEXT_version>` in the command is for specifying our next milestone. So if we're currently releasing 21.3, `<NEXT_version>` would be 21.4.
### Option 2: Launchpad UI
Don't do this if you used Option 1 above.

Go to https://launchpad.net/cloud-init click the milestone that we're
releasing.

Hit 'Create release' (Under Milestone information in middle of page)

Fill in details:
* **Don't** keep milestone active
* Specify current date for 'Date released'
* Copy the release notes from the bug (minus the changelog) into the 'Release notes' section
* Copy the changelog from the bug into the 'Changelog' section.

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
* Set `'Release <version>'` as the description
* Click 'Publish release'

## Close bugs.
Any Launchdpad bugs that were listed in the git commit messages from this release should be marked as 'fix-released' now.

There is a tool in
[uss-tableflip](https://github.com/canonical/uss-tableflip/) called
lp-bugs-released that makes this sane:
```bash
$ ./lp-bugs-released <project> <version> <space separated list of bugs>
```
Example:
```bash
$ ./lp-bugs-release cloud-init 21.3 1867532 1911680 1925395 1931392 1931577 1932048 1940233 1940235 1940839
```

To get the list of bugs that have been fixed this release, use:
```bash
$ git log <previous_version>..<version> | grep "^[ ]*LP:" | sort -u | awk -F 'LP: #' '{printf $2 " "}'
```

## Upload to ubuntu/devel
TODO: link to SRU documentation

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
