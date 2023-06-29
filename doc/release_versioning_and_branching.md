# Release Versioning and Branching

This is a high level explanation of how we do release versioning and branching on cloud-init.

# Upstream Release Numbers
(Jumping down to the examples might be more productive than reading these blocks of text)

Regular upstream release has `<major>`.`<minor>` where major is the 2-digit year and minor is an incrementing release number for the year.
Hotfixes get a .`<patch>` that gets incremented.
These versions all get reflected into ubuntu versions.

# Devel Release Numbers

Since pre-releases (i.e., `ubuntu/devel`) happen outside of the normal release schedule, `ubuntu/devel` will get a different versioning scheme:
`<next_release>~<patch>g<hash>-XubuntuY`

For example, if we just released `23.1`, then we added 5 more commits to main with the most recent commit being `#12ab34cd`, then release that to devel, the devel version would be:
`23.2~1g12ab34cd-0ubuntu1`

Upstream hotfix version numbers will NOT be encoded in the devel version number. If we then have an upstream hotfix as `23.1.1` with hash `#12ab34ce`, the devel version would be:
`23.2~2g12ab34ce-0ubuntu1`

We use the next release number in devel so that upgrades from stable series to devel will result in moving to the latest version number. If we had instead used `23.1-5g12ab34cd-0ubuntu1` as the devel version number, then a hotfix release of `23.1.1` into stable series means that the stable series could never upgrade into devel because `23.1-*` sorts lower than `23.1.1`.

We don't use the hotfix number in ubuntu/devel because it would be misleading. If stable series `23.1.1` contains `23.1` + the single hotfix commit, then ubuntu/devel shouldn't use the same number when it contains an upstream snapshot containing every single commit up to the hotfix commit.

The incrementing number between `~` and `g` is NOT the number of commits since a tag. It is simply a number that gets incremented every release. It would be confusing to use a tag because given the version number, we don't know which tag it is counting from.

# Daily Release Numbers

Because dailies go into their own PPA, they can follow a separate scheme entirely. To make it easy to know what is in the build at a glance, yet still allow for upgrading to new versions in the future, the version number for supported releases is:

`<major>.<minor>.daily-<UTC-datetime>-<commit>~<series>`.

Using this scheme, devel dailies would sort lower than any pre-release to devel, so for devel it is modified to be:

 `99.daily-<UTC-datetime>-<commit>~<series>`

## Examples
In these examples, I'll use 12ab34cd as the commit number, even though they will be random.

### Upstream release
* `23.1`

### Ubuntu/devel based on upstream
* `23.1-0ubuntu1`

### Ubuntu/jammy based on upstream
* `23.1-0ubuntu0~22.04.1`

(`0ubuntu0` because 23.1.0 was never released for this series)

### After hotfix
* Upstream: `23.1.1`
* Ubuntu/devel: `23.2~1g12ab34cd-0ubuntu1`
* Ubuntu/jammy: `23.1.1-0ubuntu0~22.04.1`

### SRU without upstream release (i.e., downstream hotfix)
* Original upstream: `23.1.1`
* Original ubuntu/jammy: `23.1.1-0ubuntu0~22.04.1`
* Fixed ubuntu/jammy: `23.1.1-0ubuntu0~22.04.2`

### First upstream snapshot into ubuntu/devel
* `23.2~1g12ab34cd-0ubuntu1`

### Next upload into ubuntu/devel
* `23.2~2g12ab34ce-0ubuntu1`


### Random daily build for jammy
* `23.1.daily-20221001050505-495cb85c~22.04`

### Random daily build for devel
* `99.daily-20221001050505-495cb85c~23.10`

With this scheme we can update the debian changelog by hand if we want/need to...which seems to be fairly often :smile:

# Upstream branching
At upstream release, we update the changelog and bump the version number.

If we need a hotfix, create a `<major>.<minor>.x` (that's a literal 'x') branch for upstream. Same rules apply for releasing a hotfix: update the d/changelog and bump the version.
After release, we **merge the changelog and version back into main**.

## Example
We released 22.4<br/>

Changelog:
```
22.4:
 * thing 1
 * thing 2
 ```

`version.py`: `22.4`

Oh no! We broke the world. Create branch `22.4.x`. Cherry-pick the fix onto `22.4.x`. Update changelog and `version.py`. Commit. Tag `22.4.1` on the `22.4.x` branch.

Changelog:
```
22.4.1:
  * cherry pick of fixing the world
22.4:
  * thing 1
  * thing 2
```

`version.py`: `22.4.1`

^ This ChangeLog and `version.py` should then get merged back into main.

The only time we wouldn't need a separate branch is if the hotfix is close enough to release that we're comfortable tagging main and upstream snapshotting to the hotfix **without skipping commits**.

# Ubuntu branching

Apart from devel, the ubuntu branch should **only** receive upstream snapshots from main (or a main-based release tag). If we need to release a hotfix, then create `ubuntu/<series>-<major>.<minor>.x` branch. Once released, merge `d/changelog` back to `ubuntu/<series>`. This process would be followed regardless of if we have SRUed or not.

## Example
(assume all of this is pre-feature freeze)

Upstream released `22.4`

`ubuntu/devel` then upstream snapshots and releases `22.4` into devel series with `22.4-0ubuntu1`.

20 commits go by and we want to release to devel again. We upstream snapshot and release with version number `23.1~1g12ab34cd-0ubuntu1`

Oh no! We broke the world! `22.4.1` gets released upstream as described above.

For `ubuntu/devel`, we upstream snapshot as always. New ubuntu/devel version number would be `23.1~2g12ab34ce-0ubuntu1`

For the stable branches, since `22.4.1` is branched from main, we don't upstream snapshot. Instead create branch `ubuntu/jammy-22.4.x` from `22.4-ubuntu1`.

Then merge `22.4.1` into `jammy/devel-22.4.x`.

Apply quilt patches and release. Tag `22.4.1-0ubuntu0~22.10.1` on `ubuntu/jammy-22.4.x` branch.

Merge `d/changelog` and any relevant packaging changes back into `ubuntu/jammy`.

# Quilt patches
cpick-style cherry-picks should be uncommon using this approach. Manual patches for series-specific behavior still need to be maintained and refreshed, but `new-upstream-snapshot` and `gbp pq` can help with that. A cpick may still be necessary in the case we SRU without an upstream change, but that's no longer a common use case.
