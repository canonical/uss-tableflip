# cloud-init upstream release process

This covers the cloud-init upstream release process.

## commit locally, push merge proposal
The change locally to mark a release should look like previous release
commits.

Examples:

 * [17.1](https://git.launchpad.net/cloud-init/commit/?id=17.1)
 * [17.2](https://git.launchpad.net/cloud-init/commit/?id=17.1)
 * [20.1](https://git.launchpad.net/cloud-init/commit/?id=20.1)

The commit content is obtained with the following:

 1. Clone latest cloud-init master branch and run `upstream-release`
   ```bash
   cd <cloud-init-root-dir>
   git checkout master
   git pull
   uss-tableflip/scripts/upstream-release <NEW_major_minor> <PREV_major_minor>
   ```
 2. You will be prompted with content to file a release process bug in launchpad
   * Example Bugs:
   [18.1](https://pad.lv/1751145),
   [18.2](https://bugs.launchpad.net/bugs/1759318),
   [19.4](https://pad.lv/1851428)

 3. Enter the bug you created which will be used in the git commit message on
    a new local **upstream/X.Y** branch.

    **Note:** If a branch other than master was used or master is out of date,
     you will get strange entries in Changelog about cherry pick commits or
     commits will not match tip of upstream/master.

    **Note:**  At this point, running `tox` locally will fail, complaining
     that your version does not match what git-describe does.  CI is
     configured to work around this problem for release branches, so you
     can disregard these local failures.  (We will create a tag later in
     the process which fixes this issue.)

 4. Push the branch up for review and create a pull request.  We will
    use that PR for some documentation on things that have been tested.
    Example merge proposals:
    [17.2](https://code.launchpad.net/~smoser/cloud-init/+git/cloud-init/+merge/335233),
    [18.1](https://code.launchpad.net/~smoser/cloud-init/+git/cloud-init/+merge/338588)
    [20.1](https://github.com/canonical/cloud-init/pull/222)

Once the pull request has been squash merged into master, you can
proceed.  Ensure that your local master is on that squash-merged commit
before proceeding.

## Update Release info on Launchpad.
Go to https://launchpad.net/cloud-init click the milestone that we're
releasing.  That will take you to
[lp/cloud-init/+milestone/<X.Y>](http://launchpad.net/cloud-init/+milestone/17.2)
.  Hit 'Create release'.

 Model the Release notes after other releases such as
 [17.1](https://launchpad.net/cloud-init/+milestone/17.1/) or
 [17.2](https://launchpad.net/cloud-init/+milestone/17.2)

To help get some of those bits of information, add '| wc -l' for just
the numbers. not done here to have you sanity check output.

  * just get log into a file

        git log 18.2..HEAD > git-log

  * contributors

        grep Author git-log | sed 's,.*: ,,'  | sort -u

  * top level domains

        grep Author git-log | sed 's,.*: ,,'  | sort -u | sed 's,.*@,,' | sort -u

  * bugs

        grep '^[ ]*LP' git-log | sed -e 's,#,,g' -e 's,.*LP: ,,' -e 's/,[ ]*/\n/'

## Tag and push it to git

First, ensure that you have a clean working tree with the squash-merged
release commit:

    git checkout master
    git fetch upstream
    git reset --hard upstream/master

Then create a signed tag, pointing at the squash-merged release commit:

    git tag --annotate --sign YY.N

Then push it:

    git push upstream YY.N


## Upload source tarball to Launchpad.
Then upload that to launchpad.

    $ ./tools/make-tarball
    cloud-init-17.2.tar.gz

    $ gpg --sign --armor --detach-sig cloud-init-17.2.tar.gz


Note, we can do this step including the 'Update Release info' step with
with 'lp-project-upload' from 'lptools' package:


    $ lp-project-upload cloud-init 17.2 cloud-init-17.2.tar.gz 17.3 changelog-file releasenotes-file


## Close bugs.
Any bugs that were listed should be marked as 'fix-released' now.
There is a tool in
[uss-tableflip](https://github.com/CanonicalLtd/uss-tableflip) called
lp-bugs-released that makes this sane.

    # git log <last-release>..<this-release>
    $ git log 17.1..17.2 | grep "^[ ]*LP:" | sort -u
    $ ./lp-bugs-released <project> <version> <bug list here>

Basically copy the Release Notes and the Changelog into an email to
Cloud-init Mailing List <cloud-init@lists.launchpad.net>

Example Emails from the past at

 * [17.1](https://lists.launchpad.net/cloud-init/msg00106.html)

Please sign the email.


## Upload to Ubuntu devel release.
Follow the Ubuntu release process doc [ubuntu-release-process](https://gist.github.com/smoser/6391b854e6a80475aac473bba4ef0310#file-ubuntu-release-process-md)

## Update COPR build cloud-init/el-testing repository with latest upstream release
 * Build srpm

       $ ./tools/run-container --source-package --unittest --artifacts=./srpm/ centos/7

 * Load [el-testing project/builds](https://copr.fedorainfracloud.org/coprs/g/cloud-init/el-testing/builds/)
 * Click New Build button -> Upload tab -> upload your src.rpm file


# Opening next release

  * Go to https://launchpad.net/cloud-init/trunk . Create a milestone,
    enter the next release number (YY.1) and pick a target date.
