## cloud-init ubuntu packaging ##

This document covers making an upload to Ubuntu of cloud-init.  It generally
covers releases xenial+.

## Ubuntu packaging branches ##
Ubuntu packaging is stored as branches in the upstream cloud-init
repo.  For example, see the ``ubuntu/devel``, ``ubuntu/xenial`` ... branches in the [upstream git repo](https://git.launchpad.net/cloud-init/).  Note that changes to the development release are always done in ubuntu/devel, not ubuntu/<release-name>.

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

  * merges master into the packaging branch so that history is maintained.
  * strip out coroe contributors from attribution in the debian changelog entries.
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
This is generally not the mechanism that is preferred for any release supported by trunk.  It may be used in order to get a upload in *really quickly* for a hot fix.

#### Cherry-pick Process
The tool for doing this is in ``uss-tableflip/scripts/cherry-pick``.  It takes as import a commit-ish that it will create a cherry-pick from.

The `cherry-pick` tool will:

  * add a new file to debian/patches/ named cpick-<commit>-topic that is dep-8 compatible
  * add that patch to debian/patches/series
  * verify that the patch applies (quilt push -a)
  * give you a chance to edit formatted the debian/changelog entry
  * prompt you to commit the change.

1. Optionally tag current point so you have revert point
    ```
    ## just tag current so you have a revert point.
    $ git tag --delete xx-current >/dev/null 2>&1; git tag xx-current
    ```
1. Cherry pick UPSTREAM_COMMITISH
   ```
   $ git featch upstream
   $ git checkout upstream/ubuntu/xenial -b ubuntu/xenial
   $ cherry-pick dc2bd79949
   ```
1. From here you follow along with the snapshot upload process from [`dch --release` and beyond](#upstream-snapshot-process).
1. Once published, fix daily builds by [reverting your cherry-pick'd patch](#when-the-daily-recipe-build-fails)
1. After doing that you can go to the recipe pages (see below) and click
build-now.

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
We have daily packaging recipes that upload to the [daily ppa](https://code.launchpad.net/~cloud-init-dev/+archive/ubuntu/daily).  These build Ubuntu packaging on top of trunk.  This differs from trunk built for the given Ubuntu release because the Ubuntu release may have patches applied.

  * [xenial](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-xenial)
  * [artful](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-artful)
  * [bionic](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-bionic)
  * [devel](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-devel)

### When the daily recipe build fails ###

The daily recipe for each release checks out tip of master, merges the ubuntu/$release
and builds the package from there.  Daily recipe failures occur under two conditions:
 1. Tip of master drifts enough that patches in the ubuntu/$release branch need to be refreshed/updated/dropped as upstream/master changes.
 1. You just finished a [cherry-pick an upstream commit](#cherry-pick-process) into an
    ubuntu/$release branch and need to drop that cherry pick patch so daily package
    recipes continue to build.

#### Dropping a cherry-pick patch

 * **During Ubuntu series feature freeze** we cannot use `new-upstream-snapshot` because it pulls in all upstream changes and we don't want to include other upstream commits if we need a second cherry pick during feature freeze:
   1. LOCAL_PATCH_COMMIT=`git log --pretty=oneline debian/ | awk 'NR == 1{print $1}'`
   1. git revert $LOCAL_PATCH_COMMIT
   1. PATCH_FILE=`git show --pretty="" --name-only | awk -F cpick 'NR == 1{printf "cpick" $2}'`
   1. REVERTED_COMMITISH_MSG=`git log --format="%s" HEAD~1..HEAD | awk -F '"' '/Revert/{print $2}'`
   1. cat > msg <<EOF
drop cherry pick included in master $REVERTED_COMMITISH_MSG
 - ${PATCH_FILE}
EOF
   1. dch -i $(cat msg)
   1. git commit -m 'update changelog' debian/changelog

 * **Outside of Ubuntu series feature freeze**:
   1. new-upstream-snapshot -v --update-patches-only
   1. git push upstream HEAD


#### Manually refreshing patch quilt failures

Patch refresh is typically done during the `new-upstream-release` process. However, new commits to master can break the patches.  In particular, the
ubuntu-advantage refactor is reverted on bionic and xenial; this patch needs
to be refreshed whenever changes to cloud-init touch:

 * cloudinit/config/cc_ubuntu_advantage.py
 * cloudinit/config/tests/test_ubuntu_advantage.py

At this point if daily builds are failing, this will fail when quilt
cannot apply the patch and put you into a subshell and ask you to
fix and then quit refresh.  The source of the issue is that the release
branch needs the upstream changes to ensure the patch still applies.
Do the following to fix the patch:

    $ new-upstream-snapshot -v --skip-release
    $ (refresh-fix)(hostname) cloud-init % quilt push -f
    $ (refresh-fix)(hostname) cloud-init % git checkout 528366820bb48c13957d0c58afc2a46a3ba84bef cloudinit/config/tests/test_ubuntu_advantage.py
    $ (refresh-fix)(hostname) cloud-init % git checkout 528366820bb48c13957d0c58afc2a46a3ba84bef cloudinit/config/cc_ubuntu_advantage.py
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
