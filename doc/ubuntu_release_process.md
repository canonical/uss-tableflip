## cloud-init ubuntu packaging ##

This document covers making an upload to Ubuntu of cloud-init.  It generally
covers releases bionic+.

## Ubuntu packaging branches ##
Ubuntu packaging is stored as branches in the upstream cloud-init
repo.  For example, see the ``ubuntu/devel``, ``ubuntu/bionic`` ... branches in the [upstream git repo](https://git.launchpad.net/cloud-init/).  Note that changes to the development release are always done in ubuntu/devel, not ubuntu/<release-name>.

Note, that there is also the git-ubuntu cloud-init repo (aka "ubuntu server dev importer") at [lp:~usd-import-team/ubuntu/+source/cloud-init](https://code.launchpad.net/~usd-import-team/ubuntu/+source/cloud-init/+git/cloud-init).

## Uploading ##
We have high level paths for uploading:

 * **new upstream release/snapshot**
 * **cherry-picked changes**

### new upstream release/snapshot ###
This is the *only* mechanism for development release uploads, and the *heavily preferred* mechanism for stable release updates (SRU).

Our goal is (and main integration tests show) that cloud-init works with bionic and beyond.

Things that need to be considered:

 * **backwards incompatible changes.**  Any backwards incompatible changes in upstream must be reverted in a stable release.  Such changes are allowed in the Ubuntu development release, but cannot be SRU'd.  As an example of such a change see [debian/patches/azure-use-walinux-agent.patch](https://git.launchpad.net/cloud-init/tree/debian/patches/azure-use-walinux-agent.patch?h=ubuntu/xenial) in the ``ubuntu/xenial`` branch.  Patches here should be in [dep-8](http://dep.debian.net/deps/dep8/) format.

### Upstream Snapshot Process
The tool used to do this is ``uss-tableflip/scripts/new_upstream_snapshot.py``.
It does almost everything needed with a few issues listed below.

new_upstream_snapshot.py does:

* merges main into the packaging branch so that history is maintained.
* makes changes to debian/patches/series and drops any cherry-picks in that directory.
* refreshes any patches in debian/patches/
* updates debian/changelog accordingly.

In SRU, I will generally strip out commits that are not related to ubuntu, and also strip out or join any fix/revert/fixup commits into one.  Note this is a *ubuntu* changelog, so it makes sense that it only have Ubuntu specific things listed.

Assuming your Canonical remote is named 'upstream' and you have cloud-init cloned locally, the process goes like this:
    # create a clean branch tracking upstream/ubuntu/devel
    # for SRU substitute release name 'xenial' for 'devel'
    $ git fetch upstream
    $ git checkout -B ubuntu/devel upstream/ubuntu/devel
    $ new_upstream_snapshot.py -c upstream/main

    # output then ends with:
    To release:
    dch -r -D lunar ''
    git commit -m 'releasing cloud-init version 22.4.2-0ubuntu2' debian/changelog
    git tag 22.4.2-0ubuntu2

    Don't forget to include any previously released changelogs!

    ## You can follow its instructions to release and tag.

At this point, you have git in the state we want it in, but we still
have to do two things:

 * get an "orig tarball".  build-package below will use the .orig.tar.gz in the parent  directory if it is present.  If not, then it will create it using tools/make-tarball.  FIXME: Much better would be to try to download an orig tarball from a link like https://launchpad.net/ubuntu/+archive/primary/+files/cloud-init_0.7.9-231-g80bf98b9.orig.tar.gz .  Otherwise on upload you may be rejected for having a binary-different orig tarball.

 * build a source package and sign it.

The tool that I use to do this is [build-package](../scripts/build-package).

    $ build-package
    ...
    wrote ../out/cloud-init_21.4-25-g039c40f9-0ubuntu1~22.04.1.debian.tar.xz
    wrote ../out/cloud-init_21.4-25-g039c40f9-0ubuntu1~22.04.1.dsc
    wrote ../out/cloud-init_21.4-25-g039c40f9-0ubuntu1~22.04.1_source.build
    wrote ../out/cloud-init_21.4-25-g039c40f9-0ubuntu1~22.04.1_source.buildinfo
    wrote ../out/cloud-init_21.4-25-g039c40f9-0ubuntu1~22.04.1_source.changes
    wrote ../out/cloud-init_21.4-25-g039c40f9.orig.tar.gz

I then will sbuild the binary and then dput the result.

    $ sbuild --dist=jammy --arch=amd64  --arch-all ../out/cloud-init_21.4-25-g039c40f9-0ubuntu1~22.04.1.dsc
    $ dput ubuntu ../out/cloud-init_21.4-25-g039c40f9-0ubuntu1~22.04.1_source.changes


For SRUs don't forget to dput into the [cloud-init proposed ppa](https://launchpad.net/~cloud-init-dev/+archive/ubuntu/proposed)

    $ dput ppa:cloud-init-dev/proposed ../out/cloud-init_21.4-25-g039c40f9-0ubuntu1~22.04.1_source.changes

Last, we need to push our tag above now that upload succeeded.

    $ PKG_VERSION=$(dpkg-parsechangelog --show-field Version)
    $ TAG=$(echo "ubuntu/$PKG_VERSION" | tr '~' '_')
    $ git tag "$TAG"
    $ git push upstream HEAD "$TAG"


### cherry-picked changes ###
This is generally not the mechanism that is preferred for any release supported by main.  It may be used in order to get a upload in *really quickly* for a hot fix.
Note: Nonstandard packaging changes need to be applied to both the ubuntu/$SERIES branch and the ubuntu/$SERIES-hotfix branches.

#### Cherry-pick Process
The tool for doing this is in ``uss-tableflip/scripts/cherry-pick``.  It takes as import a commit-ish that it will create a cherry-pick from.

    $ git checkout ubuntu/xenial
    $ cherry-pick dc2bd79949

The tool will:

  * add a new file to debian/patches/ named cpick-<commit>-topic that is
    dep-8 compatible
  * add that patch to debian/patches/series
  * verify that the patch applies (quilt push -a)
  * give you a chance to edit formatted the debian/changelog entry
  * prompt you to commit the change.

From here you follow along with the snapshot upload process from
[`dch --release` and beyond](#upstream-snapshot-process).

**Note**: After uploading a cherry-pick quilt patch to ubuntu/$release, the
script `scripts/fix-daily-branch` must be run to fix daily builds. It will
create a local branch named ubuntu/daily/$release which will revert all
quilt cpick files to allow daily recipe builds to pass.

To cherry-pick:

    $ git checkout ubuntu/xenial  # or whatever release.
    $ new-upstream-snapshot -v --update-patches-only
    $ fix-daily-recipe -s ubuntu/xenial -d ubuntu/daily/xenial
    # Create a PR in github for merging <your_remote>/ubuntu/xenial into
    # canonical/ubuntu/xenial
    # Once that ubuntu/xenial PR is approved, push from git cmdline not Github
    $ git push upstream HEAD

    # create local ubuntu/daily/xenial branch with *cpick* reverts to fix daily
    $ fix-daily-branch xenial upstream
    $ git push upstream ubuntu/daily/xenial  --force

The `cherry-pick` will produce 1 or 2 commits on the branch with summary like:

  * refresh patches against main commit 2d6e4219
  * drop cherry picks included in main commit 2d6e4219

The `fix-daily-branch` will create a local ubuntu/daily/xenial branch from
the local ubuntu/xenial branch and revert all debian/patches/*cpick* commits

### Adding a quilt patch to debian/patches ###
This is generally needed when we are disabling backported feature from tip
in order to retain existing behavior on an older series.

**Note:** If adding a quilt patch to modify functionality introduced by
a debian/patches/cpick-\* file, the new quilt patch should have the prefix
fix-cpick-<the_ancestor_commitish_for_the_fixed_cpick>. `new-upstream-snapshot`
removes all `cpick-<hash>-\*` and fix-cpick-<hash>-\*` files from the
`debian/patches` directory when the <hash> commit is already applied to the
commit history of the snapshot.

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

## Links ##

* [SRU Exception Doc](https://wiki.ubuntu.com/CloudinitUpdates)
