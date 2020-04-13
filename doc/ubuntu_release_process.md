## cloud-init ubuntu packaging ##

This document covers making an upload to Ubuntu of cloud-init.  It generally
covers releases xenial+.

## Ubuntu packaging branches ##
Ubuntu packaging is stored as branches in the upstream cloud-init
repo.  For example, see the ``ubuntu/devel``, ``ubuntu/xenial`` ... branches in the [upstream git repo](https://git.launchpad.net/cloud-init/).  Note that changes to the development release are always done in ubuntu/devel, not ubuntu/<release-name>.

We build cloud-init master with each release branch to provide a daily
cloud-init for each of the releases we support. Certain features and behavior
changes are disabled in release branches. These release branch changes may
prevent master from merging with the release branch and break the daily recipe
builds.
To resolve this conflict we provide fixes (reverting cherry picks or other
feature redactions) to the release branches in a separate branch named
ubuntu/daily/$release branch. For example ubuntu/daily/devel, ubuntu/daily/xenial.

Note, that there is also the git-ubuntu cloud-init repo (aka "ubuntu server dev importer") at [lp:~usd-import-team/ubuntu/+source/cloud-init](https://code.launchpad.net/~usd-import-team/ubuntu/+source/cloud-init/+git/cloud-init).


## Uploading ##
We have high level paths for uploading:

 * **new upstream release/snapshot**
 * **cherry-picked changes**


### new upstream release/snapshot ###
This is the *only* mechanism for development release uploads, and the *heavily preferred* mechanism for stable release updates (SRU).

Our goal is (and trunk integration tests show) that cloud-init works with xenial and beyond.

Things that need to be considered:

 * **backwards incompatible changes.**  Any backwards incompatible changes in upstream must be reverted in a stable release.  Such changes are allowed in the Ubuntu development release, but cannot be SRU'd.  As an example of such a change see [debian/patches/azure-use-walinux-agent.patch](https://git.launchpad.net/cloud-init/tree/debian/patches/azure-use-walinux-agent.patch?h=ubuntu/xenial) in the ``ubuntu/xenial`` branch.  Patches here should be in [dep-8](http://dep.debian.net/deps/dep8/) format.

### Upstream Snapshot Process
The tool used to do this is ``uss-tableflip/scripts/new-upstream-snapshot``.
It does almost everything needed with a few issues listed below.

new-upstream-release does:

  * merge master into the packaging branch so that history is maintained.
  * strip out core contributors from attribution in the debian changelog entries.
  * makes changes to debian/patches/series and drops any cherry-picks in that directory.
  * refreshes any patches in debian/patches/

  * opens $EDITOR with an option to edit debian/changelog.  In SRU, I will generally strip out commits that are not related to ubuntu, and also strip out or join any fix/revert/fixup commits into one.  Note this is a *ubuntu* changelog, so it makes sense that it only have Ubuntu specific things listed.

  * During SRU regression fixes: use a separate changelog entry from what is already in -proposed and remove the SRU_BUG_NUMBER_HERE from the newest "New upstream snapshot" line.

The process goes like this:

    $ git clone ssh://git.launchpad.net/cloud-init -o upstream
    # if you do not have ssh access, use http://git.launchpad.net/cloud-init

    # create a branch tracking upstream/ubuntu/devel
    # for SRU substitute release name 'xenial' for 'devel'
    $ git checkout -b ubuntu/devel upstream/ubuntu/devel

    # if you already had a branch and did not have local changes:
    #   git checkout ubuntu/devel; git reset --hard upstream/ubuntu/devel

    ## just make a tag, so you can easily revert.
    ## to do so, just git reset --hard xx-current
    $ git tag --delete xx-current >/dev/null 2>&1; git tag xx-current

    ## 'master' can be left off as it is the default.
    $ new-upstream-snapshot master

    ## Your '$EDITOR' will be opened with the chance to change the
    ## changelog entry.
    ##   FIXME: If this is a a SRU, then you should ideally edit the packaging
    ##   portion of the version string to contain ~XX.YY.N
    ##   For example: 0.7.9-233-ge586fe35-0ubuntu1~16.04.1
    ##   It will **not** automatically add the '~16.04.1' portion.
    ##
    ## Exit from your editor and it will prompt you to commit the change.

    ## output then looks like:
    [ubuntu/devel aa945427a] update changelog (new upstream snapshot 0.7.9-242-gdc2bd7994).
    1 file changed, 26 insertions(+)
    wrote new-upstream-changes.txt for curtin version 18.1-1-g45564eef-0ubuntu1~16.04.1.
    release with:
    dch --release --distribution=xenial-proposed
    git commit -m "releasing curtin version 18.1-1-g45564eef-0ubuntu1~16.04.1" debian/changelog
    git tag ubuntu/18.1-1-g45564eef-0ubuntu1_16.04.1

    ## You can follow its instructions to release and tag.


At this point, you have git in the state we want it in, but we still
have to do two things:

 * get an "orig tarball".  build-package below will use the .orig.tar.gz in the parent  directory if it is present.  If not, then it will create it using tools/make-tarball.  FIXME: Much better would be to try to download an orig tarball from a link like https://launchpad.net/ubuntu/+archive/primary/+files/cloud-init_0.7.9-231-g80bf98b9.orig.tar.gz .  Otherwise on upload you may be rejected for having a binary-different orig tarball.

 * build a source package and sign it.

The tool that I use to do this is [build-package](../scripts/build-package).

    $ build-package
    ...
    wrote ../out/cloud-init_0.7.9-242-gdc2bd7994-0ubuntu1.debian.tar.xz
    wrote ../out/cloud-init_0.7.9-242-gdc2bd7994-0ubuntu1.dsc
    wrote ../out/cloud-init_0.7.9-242-gdc2bd7994-0ubuntu1_source.build
    wrote ../out/cloud-init_0.7.9-242-gdc2bd7994-0ubuntu1_source.buildinfo
    wrote ../out/cloud-init_0.7.9-242-gdc2bd7994-0ubuntu1_source.changes
    wrote ../out/cloud-init_0.7.9-242-gdc2bd7994.orig.tar.gz


I then will sbuild the binary and then dput the result.

    $ sbuild --dist=xenial --arch=amd64  --arch-all ../out/cloud-init_18.2-4-g05926e48
    $ dput ../out/cloud-init_18.2-4-g05926e48-0ubuntu1~16.04.1.dsc

For SRUs don't forget to dput into the [cloud-init proposed ppa](https://launchpad.net/~cloud-init-dev/+archive/ubuntu/proposed)

    $ dput ppa:cloud-init-dev/proposed ../out/cloud-init_18.2-4-g05926e48-0ubuntu1~16.04.1.dsc

Last, we need to push our tag above.

    $ git push upstream HEAD ubuntu/18.2-4-g05926e48-0ubuntu1_16.04.1


### cherry-picked changes ###
This is generally not the preferred mechanism for any release supported by trunk.  It is used either to get a upload in *really quickly* for a hot fix or during release **Feature Freeze** when only bugfixes or FeatureFreezeExceptions (FFEs) are accepted.  The tool for doing this is in ``uss-tableflip/scripts/cherry-pick``.  It takes as import a commit-ish that it will create a patch to apply the commitish via debian/patches/cpick-\*.

#### Cherry-pick Process
```
  $ git fetch upstream
  $ git checkout -b ubuntu/xenial upstream/ubuntu/xenial || git checkout ubuntu/xenial
  $ git reset --hard upstream/ubuntu/xenial
  $ cherry-pick <new_cherry_pick_commitish>
  $ cherry-pick <commit_hash_2>
  # Put up two PRs for review ubuntu/$release and ubuntu/daily/$release
  $ git push <your_remote> ubuntu/$release
  $ git push <your_remote> ubuntu/daily/$release
```


The `cherry-pick` tool will:

  * add a new file to debian/patches/ named cpick-<commit>-topic that is
    dep-8 compatible
  * append file to debian/patches/series
  * call quilt push -a
  * prompt for commiting the debian/changelog
  * checkout upstream/ubuntu/daily/$release branch
  * git cherry-pick the commit which added the debian/patches/cpick-\* into the
    ubuntu/daily/$release branch
  * git revert the cpick commit from ubuntu/daily/$release

From here you follow along with the snapshot upload process from
[`dch --release` and beyond](#upstream-snapshot-process).


#### Fixing daily builds after cherry-pick

After uploading a cherry-pick release, the daily builds will break
unless we also revert the cherry-picks from the ubuntu/daily/$release branch.
This is because the recipe will merge ubuntu/$release into master, and will get
conflicts re-applying the cherry-picked patch because it already exists.
The `cherry-pick` tool takes care of reverting any cherry picks from
ubuntu/daily/$release branches. 

**Note**: The daily build recipe assumes that all cherry-picks originate from
the project's master branch. If cherry-picks are pulled from other branches,
the author will need to rename that debian/patches/cpick-\* file to a
different prefix, and avoid reverting that cpick from ubunut/daily/$release.



After both ubuntu/$release and ubuntu/daily/$release PRs are merged, go to the
recipe pages (see below) and click build-now.

### Adding a quilt patch to debian/patches ###
This is generally needed when we are disabling backported feature from tip
in order to retain existing behavior on an older series.

The procedure is as follows:

 * quilt push -a                            # Apply existing patches in order
 * quilt new <descriptive_patch_nam>.patch  # Create a new named debian/patch
 * quilt edit <somefile_you_are_changing>   # For each changed file
 * quilt refresh                            # Write the patch to debian/patches
 * quilt header --dep3 -e                   # Edit the descriptive patch header
 * quilt pop -a
 * git add debian/patches
 * vi debian/changelog                      # Record the new debian patch file

Then follow the steps [`dch --release` and beyond](#upstream-snapshot-process).

## Outside Uploads ##
Any core-dev of ubuntu can upload to cloud-init in an SRU or development
release and skip the process above.  In order to keep sanity, we have
to support the ability to have the packaging branches keep up with uploads
that are done by members of other teams.

If someone uploads to ubuntu and does not use this process, we wont have
"rich history" of those commits.  So we will just take the dsc file and
orig tarball and put it into the branch and tag appropriately.  The tool
to do this is [git-import-dsc](https://gist.github.com/smoser/6391b854e6a80475aac473bba4ef0310#file-git-import-dsc).

Its usage is fairly simple.  Assuming a upload of cloud-init to
xenial-proposed, just run it as:

    $ git checkout ubuntu/xenial
    $ git-import-dsc cloud-init xenial-proposed


That will download the dsc that is in xenial-proposed, and commit it.
If there were a number of releases that were missed you could do

    $ git checkout ubuntu/xenial
    $ versions="0.7.9-233-ge586fe35-0ubuntu1~16.04.1 0.7.9-233-ge586fe35-0ubuntu1~16.04.2"
    $ for ver in $versions; do git-import-dsc cloud-init $ver; done


## Daily packaging recipes and ppa ##
We have daily packaging recipes which upload to the [daily ppa](https://code.launchpad.net/~cloud-init-dev/+archive/ubuntu/daily).  These build Ubuntu packaging on top of trunk.  This differs from trunk built for the given Ubuntu release because the Ubuntu release may have patches applied.

  * [xenial](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-xenial)
  * [bionic](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-bionic)
  * [eoan](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-eoan)
  * [devel](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-devel)

### When the daily recipe build fails ###

The daily recipe for each release checkouts master, merges both
ubuntu/$release and ubuntu/daily/$release and builds the package from there.
From time to time, the patches in the ubuntu/$release branch need to be
refreshed as upstream/master changes.


The example build recipe for each release follows this general format:

Checkout cloud-init tip, merge ubuntu/$release which may have cpicks, merge ubuntu/daily/$release which revert debian/patches/cpick-\* because those cpicks are already included in tip.

Ubuntu devel daily recipe:

```
# git-build-recipe format 0.4 deb-version {latest-tag}-{revno}-g{git-commit}-0ubuntu1+{revno:ubuntu-pkg}~trunk
lp:cloud-init master
merge ubuntu-pkg lp:cloud-init ubuntu/devel
merge ubuntu-pkg-daily lp:cloud-init ubuntu/daily/devel
```

This is typically done during the new-upstream-release tool process, however,
new commits to master can break the patches.  In particular, the
ubuntu-advantage refactor (commit hash: f247dd20ea73f8e153936bee50c57dae9440ecf7)
is reverted on bionic and xenial; this patch needs to be refreshed whenever changes
to cloud-init touch:

 * cloudinit/config/cc_ubuntu_advantage.py
 * cloudinit/config/tests/test_ubuntu_advantage.py

At this point if daily builds are failing, this will fail when quilt
cannot apply the patch and put you into a subshell and ask you to
fix and then quit refresh.  The source of the issue is that the release
branch needs the upstream changes to ensure the patch still applies.
Do the following to fix the patch (Note: we need to check out the files
from *before* the refactor, so we specify the previous commit by using
the ^ suffix)

    $ new-upstream-snapshot -v --skip-release
    $ (refresh-fix)(hostname) cloud-init % quilt push -f
    $ (refresh-fix)(hostname) cloud-init % git checkout f247dd20ea73f8e153936bee50c57dae9440ecf7^ cloudinit/config/tests/test_ubuntu_advantage.py
    $ (refresh-fix)(hostname) cloud-init % git checkout f247dd20ea73f8e153936bee50c57dae9440ecf7^ cloudinit/config/cc_ubuntu_advantage.py
    $ (refresh-fix)(hostname) cloud-init % quilt refresh
    $ (refresh-fix)(hostname) cloud-init % exit 0

Follow the prompt to commit the updated debian/changelog.

Revert your changes to the two files:

    $ git checkout HEAD cloudinit/config/tests/test_ubuntu_advantage.py
    $ git checkout HEAD cloudinit/config/cc_ubuntu_advantage.py


At this point, we've refreshed the patch on this branch, copy out the patch
for testing and re-use.

    $ cp debian/patches/ubuntu-advantage-revert-tip.patch /tmp/$release-debian/patches/ubuntu-advantage-revert-tip.patch

To verify this fixes things for the daily build.

    $ mkdir /tmp/test-daily-recipe-xenial
    $ cd /tmp/test-daily-recipe-xenial
    $ git clone https://github.com/canonical/cloud-init.git
    $ cd cloud-init
    $ git remote add local-ci-release /path/to/your/cloud-init/release/repo
    $ git fetch local-ci-release
    $ git merge local-ci-release/ubuntu/xenial
    $ quilt push -a; quilt pop -a


With the patch passing verification, push this branch up for review:

    $ git push <user github repo> ubuntu/xenial::ubuntu/xenial-fix-daily-ppa-YYYYMMDD

In the github UI, make sure the proposal is pointing to ubuntu/xenial rather
than master.


## Links ##

 * [SRU Exception Doc](https://wiki.ubuntu.com/CloudinitUpdates)
