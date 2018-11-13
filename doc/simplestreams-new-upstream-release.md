# Simplestreams process for making a new upstream snapshot from master.

Simplestreams does not currently manage ubuntu packaging in upstream.
Cloud-init and curtin use 'new-upstream-snapshot' which manages most of
the process described here.  Quite possibly we should get to using
new-upstream-snapshot.

That said, this is a general process on how we put a new upstream snapshot
or upstream release into ubuntu/devel.

## simplestreams new upstream snapshot
The general process here relies on git-ubuntu packaging branches
and utilizes that.

 * **Set some variables for reference**

        $ yymmdd=$(date +%Y%m%d)
        $ ref=upstream/master

 * **Get both upstream and ubuntu pkg as remotes** (as remotes)

        $ git ubuntu clone simplestreams
        $ cd simplestreams
        $ git remote add upstream https://git.launchpad.net/simplestreams
        $ git fetch upstream

 * **Check out a working branch**

        $ git checkout -b "pkg/snapshot-$yymmdd" pkg/ubuntu/devel
        $ git describe "$ref"
        0.1.0-17-g693795b

 * **Create a orig tarball from trunk**

        # checkout master partially just to get new ./tools/export-tarball
        $ git checkout upstream/master
        $ uver=$(git describe "$ref")
        $ tarball="../simplestreams_${uver}.orig.tar.gz"
        $ ./tools/export-tarball "--output=../simplestreams_${uver}.orig.tar.gz" "$ref"

 * **Hack upstream content into packaging branch**

        $ git checkout pkg/ubuntu/devel
        $ rm -Rf *
        $ git checkout debian/
        $ tar --strip-components=1 -xvf "$tarball"

        # if upstream didn't make any changes to debian/ there may
        # well not be any changes here, so you might skip this.
        $ git add debian/
        $ git commit -m "update debian/ from $uver" debian/

        $ git add .
        $ git commit -m "update upstream files to $uver"

 * **Update debian/changelog**

   Now you have to write a debian/changelog.  Changes can be seen in 2 ways:

     1. git diff pkg/ubuntu/devel
        this is all the changes.

     2. if you can figure out the last sync point, then youc an get
        itemized changes on the upstream branch.

            git log $lastver..upstream/master | log2dch

   You can largely just ignore things in tools/ those changes.  They are not
   related to shipped contents, so they dont really need to be included or
   advertised in the debian/changelog.

        $ dch --newversion "$uver-0ubuntu1"
        # write your message

        $ git commit -m "update changelog" debian/changelog
        $ dch --release
        $ debcommit -r debian/changelog


 * **Build package and upload**

        $ build-package
        $ sbuild ...
        $ dput
