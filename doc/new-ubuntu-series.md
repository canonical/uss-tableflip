# Setup for a new Ubuntu release/series.

In order to get new daily builds for cloud-init and curtin, at the start of
a new Ubuntu release, we have to do a few things:

## Populate a package into the new release for each "test-archive".
 
These PPAs are used for test.  If we run test of _release_ and there is no 
package there, then the `apt-get update` will fail. So we copy the
`smello` package to the new release.  Simply go to these urls
and 'Copy Packages' and pick the newest smello there and 
'Copy existing binaries' to the new 'Destination series'.

 * [cloud-init-dev/test-archive](https://launchpad.net/~cloud-init-dev/+archive/ubuntu/test-archive)
 * [curtin-dev/test-archive](https://launchpad.net/~curtin-dev/+archive/ubuntu/test-archive)

## Add a new release for curtin daily recipe
Curtin just has one recipe (we have the same source and debian packaging)
for all stable releases.

Simply open the recipe link in a browser and hit 'Distribution series'
and add the new release.

  * [curtin-daily recipe](https://code.launchpad.net/~curtin-dev/+recipe/curtin-daily)

## Create a new stable release branch for cloud-init
We maintain a branch for each ubuntu release.  The newly released branch *was* being built from `ubuntu/devel`, but now we want to create a `ubuntu/<release>` branch.

    $ git clone -o upstream ssh://launchpad.net/cloud-init
    $ cd cloud-init
    $ git branch ubuntu/<release> ubuntu/devel
    $ git push upstream ubuntu/<release>

## To add a new release for cloud-init build recipe
cloud-init recipe is harder because we have packaging branches that differ
between releases (some patches are applied to keep SRUable behavior).
So instead of one recipe, we have a recipe per release.

This is what I did to get a 'bionic' build after 'cosmic' was opened.
We have a 'ubuntu/devel' recipe build, which should build from ubuntu/devel
for the current development release.  Generically, where you see 'bionic'
below think "old release" and "cosmic" think "new release".

First move the 'devel' line to build cosmic instead of bionic.
At [cloud-init-daily-devel](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-devel). I unchecked 'Bionic' and checked 'Cosmic'

Then, add a 'bionic' build

 1. go to [~cloud-init-dev/+recipes](https://code.launchpad.net/~cloud-init-dev/+recipes).  Look at one of these for reference.  Ie, there should be a `cloud-init-daily-<RELEASE-2>.

 2. go to [cloud-init/master](https://code.launchpad.net/~cloud-init-dev/cloud-init/+git/cloud-init/+ref/master).  Click 'Create packaging recipe'.  Follow the answers below, remember to replace 'bionic' with the stable release name.

   * **Name**: cloud-init-bionic
   * **Description**: build cloud-init from master branch with packaging from ubuntu/bionic branch.
   * [✔️ ] **Use an existing PPA**.  Select 'cloud-init daily builds' here (~cloud-init-dev/ubuntu/daily).  *Note*, here you have to find that in possibly a long list.
   * **Default distribution series**: bionic
   * **Recipe text**: adjust recipe from '1' above

The new recipe will be linked at [~cloud-init-dev/+recipes](https://code.launchpad.net/~cloud-init-dev/+recipes).
