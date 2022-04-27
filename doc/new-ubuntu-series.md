# Setup for a new Ubuntu release/series.

In order to get new daily builds for cloud-init and curtin, at the start of
a new Ubuntu release, we have to do a few things:

## cloud-init

### Populate a package into the new release for the "test-archive".
 
This PPA is used for test.  If we run test of _release_ and there is no
package there, then the `apt-get update` will fail. So we copy the
`smello` package to the new release.  Simply go to this url
and 'Copy Packages' and pick the newest `smello` there and
'Copy existing binaries' to the new 'Destination series'.

 * [cloud-init-dev/test-archive](https://launchpad.net/~cloud-init-dev/+archive/ubuntu/test-archive)

### Create a new stable release branch for cloud-init
We maintain a branch for each ubuntu release.  The newly released branch *was*
being built from `ubuntu/devel`, but now we want to create a `ubuntu/<release>`
branch.

```bash
    $ git clone -o upstream git@github.com:canonical/cloud-init
    $ cd cloud-init
    $ git checkout ubuntu/devel
    $ PREVIOUS_RELEASE=`dpkg-parsechangelog --offset 0 --count=1 --show-field Distribution`
    $ git checkout -b ubuntu/$PREVIOUS_RELEASE

    # If you DO NOT have ability to push branches as an upstream committer:
    $ git push origin ubuntu/$PREVIOUS_RELEASE
    # Ask for a review of your branch from cloud-init upstream committer
    https://github.com/canonical/cloud-init/compare/ubuntu/devel...<YOUR_GITHUB_USER>:ubuntu/<PREVIOUS_RELEASE>?expand=1

    # Committer to push branch to upstream
    $ git push upstream ubuntu/$PREVIOUS_RELEASE
```

### To add a new release for cloud-init build recipe
cloud-init recipe is harder than other packages because we have packaging
branches that differ between releases
Some release-specific quilt patches are applied via
ubuntu/<release>/debian/patches keep SRUable behavior.
So instead of one recipe, we have a recipe per release.

Here is the procedure followed when 'kinetic' was opened as a development
release and 'jammy' just published as 'stable':

 1. Edit the devel recipe by clicking ["Edit Recipe"](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-devel) and checking 'Kinetic", unchecking 'Jammy' in 'Default distribution series'


 2. go to [~cloud-init-dev/+recipes](https://code.launchpad.net/~cloud-init-dev/+recipes).  Look at one of these for reference.  Ie, there should be a `cloud-init-daily-<RELEASE-2>` Specific to this example, open [Impish daily recipe](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-impish)

 3. go to [cloud-init/main](https://code.launchpad.net/~cloud-init-dev/cloud-init/+git/cloud-init/+ref/main).  Click 'Create packaging recipe'.  Follow the answers below, remember to replace 'jammy' with the stable release name.

   * **Name**: cloud-init-jammy
   * **Description**: build cloud-init from main branch with packaging from ubuntu/jammy branch.
   * [✔️ ] **Use an existing PPA**.  Select 'cloud-init daily builds' here (~cloud-init-dev/ubuntu/daily).  *Note*, here you have to find that in possibly a long list.
   * **Default distribution series**: jammy
   * **Recipe text**: adjust recipe from '2' above replacing impish with jammy

The new recipe will be linked at [~cloud-init-dev/+recipes](https://code.launchpad.net/~cloud-init-dev/+recipes).

### Jenkins jobs

The cloud-init Jenkins jobs are kept in the `cloud-init` directory of the
[server-jenkins-jobs](https://github.com/canonical/server-jenkins-jobs/)
repository. When a new release is out:

  1. If the previous release was not a LTS, drop all the `-integration`
  jobs which are not for `-proposed`. 
  2. Add new `-integration` and `-proposed` jobs for the new release.
  3. Cleanup any job definition for unsupported releases.
  4. Test the job definition using `test-jenkins-jobs` (part of the
  `server-jenkins-jobs` repo). Push the changes and trigger `admin-jobs-update`
  to deploy the new jobs.
  5. Manually delete any removed job from the Jenkins web interface.

## curtin

### Populate a package into the new release for the "test-archive".

This PPAs is used for test. Simply go to this url and 'Copy Packages' and pick
the newest `smello` there and 'Copy existing binaries' to the new 'Destination
series'.

 * [curtin-dev/test-archive](https://launchpad.net/~curtin-dev/+archive/ubuntu/test-archive)

### Add a new release for curtin daily recipe
Curtin just has one recipe (we have the same source and debian packaging)
for all stable releases.

Simply open the recipe link in a browser and hit 'Distribution series'
and add the new release.

  * [curtin-daily recipe](https://code.launchpad.net/~curtin-dev/+recipe/curtin-daily)

