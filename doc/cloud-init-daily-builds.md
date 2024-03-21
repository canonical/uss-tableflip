# cloud-init Daily Builds

## Background

We have cloud-init [build recipes on Launchpad](https://launchpad.net/~cloud-init-dev) that build daily.  These recipes take the latest code from main, merge it with a downstream packaging branch, and then build the package. This includes applying quilt patches. The resulting package is then uploaded to the [cloud-init daily PPA](https://code.launchpad.net/~cloud-init-dev/+archive/ubuntu/daily). This PPA is what is used by [jenkins](https://jenkins.canonical.com/server-team/view/cloud-init/) in our daily integration tests.

### Navigating to the daily builds on Launchpad

Start at the [cloud-init Commiters](https://launchpad.net/~cloud-init-dev) team page.

To get to the build recipes, click "Code" at the top, then "Source package recipes" on the right side.

You should see a list of recipes for the currently supported releases + devel. Click on the "devel" link to get to the build recipe for the current devel branch.

## Understanding the build recipe

Launchpad uses a [recipe](https://help.launchpad.net/Packaging/SourceBuilds/Recipes) to build the package. The recipe should look something like:
```
# git-build-recipe format 0.4 deb-version 99.daily-{time}-{git-commit}
lp:cloud-init main
merge ubuntu-pkg lp:cloud-init ubuntu/devel
```

This recipe essentially says to take the latest code from the `cloud-init` main branch, merge it with the `cloud-init` packaging branch for the `ubuntu/devel` series, and then build the package using standard package build. **Note that this uses [Launchpad](https://code.launchpad.net/cloud-init) branches**. These builds do not use GitHub. The version number is set to `99.daily-{time}-{git-commit}`. This is a special version number that is used to indicate that this is a daily build. See [Release Versioning and Branching](release_versioning_and_branching.md#daily-release-numbers) for more information on the daily versioning scheme.

More information about build recipes can be found [on Launchpad](https://help.launchpad.net/Packaging/SourceBuilds/GettingStarted). Unfortunately, the documentation is sparse and somewhat outdated. Feel free to ask a cloud-init team member if you need help understanding or reproducing a build recipe.

## When a build fails

If you are subscribed to [build failure notifications](#build-failure-notifications), you should get an email when a daily build fails. When this happens, the daily PPA won't get updated, and Jenkins won't have the latest package to test.

Every build comes with a build log. From the [recipe](https://code.launchpad.net/~cloud-init-dev/+recipe/cloud-init-daily-devel), the "Latest builds" section will have recent build status. The most recent should say "Failed to build". If you click that "Failed to build" link, you will be taken to a build status page. From there you can click the "buildlog" link. Failures are almost always 1 of 3 reasons:

1. **Merge error**: Git is unable to merge the packaging branch with the main branch. If this happens, you'll see something like "Automatic merge failed; fix conflicts and then commit the result" near the bottom of the build log.
2. **Quilt patch error**: If this happens, you'll see something like "Exception: Failed to apply quilt patches" at the bottom of the log.
3. **Launchpad flakiness**: If this happens, you'll need to wait an re-run the build later.

Fixing the build requires manually performing an upstream snapshot on the branch, and then fixing the problem as appropriate. See the [ubuntu release process docs](ubuntu_release_process.md#upstream-snapshot-process) for using the `new_upstream_snapshot.py` tool to do a manual snapshot.

### Fixing a merge conflict

As of this writing, there is a `new_upstream_snapshot.py` branch called `merge-strategy` that should handle the merge more intelligently and not require resolving any manual merge conflicts. If the branch is already merged, update this doc please XD.

Alternatively, checkout the affected branch (we're assuming `devel` here), merge main, and resolve like you would any other merge conflict.
```bash
git checkout upstream/ubuntu/devel --track
git merge main
# See and fix merge conflict
```

### Fixing a quilt patch error

If a quilt patch fails to apply, you need to manually refresh the quilt patch. This is easiest to do in conjunction with the `new_upstream_snapshot.py` script.

```bash
new_upstream_snapshot.py --no-sru-bug
# Tool fails to apply a patch
quilt push -f
# Manually fix the patch, then run:
quilt refresh
# The following will ensure that the patches all apply and tests pass
quilt pop -a
quilt push -a
tox
quilt pop -a

git commit -m "Refresh quilt patches" debian/patches/the-name-of-your-patch.patch
new_upstream_snapshot.py --no-sru-bug --post-stage=quilt
```

## Post fix

After fixing the branch:

1. Push the updated packaging branch to your origin. Open a PR to get it merged upstream.
2. Once merged, the code needs to be reflected to Launchpad in order for Launchpad to build it. We have a [jenkins job](https://jenkins.canonical.com/server-team/view/cloud-init/job/cloud-init-github-mirror/) to do this. It runs automatically every 4 hours, but you can trigger in manually as desired.
3. Once the code has been synced, you can trigger a rebuild from the recipe page. If the build succeeds, you're done!

## Build failure notifications

At the bottom of the [landing page](https://launchpad.net/~cloud-init-dev), there is an option to subscribe to the cloud-init-dev mailing list. Build failure notifications get sent out from this list. If you're not yet a member of the cloud-init-dev team, you will need to request to join the team. Note that this is different from having GitHub commit privileges or Ubuntu upload rights. The cloud-init-dev team is specific to the Launchpad project, so feel free to request access even if you don't have other permissions.
