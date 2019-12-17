# cloud-init upstream release process

This covers the cloud-init upstream release process.

## commit locally, tag, sign, push merge proposal
The change locally to mark a release should look like previous release
commits.

Examples:

 * [17.1](https://git.launchpad.net/cloud-init/commit/?id=17.1)
 * [17.2](https://git.launchpad.net/cloud-init/commit/?id=17.1)
 
The commit content should consist of

 1. cd to your root directory of the cloud-init repository
 2. Run `./scripts/upstream-release` to get content for filing a bug and
    sending a release mail  to the mailing list
 3. File a bug with subject Release 20.1 and content from `upstream-release`
    script
 
    * Example Bugs: [18.1](https://pad.lv/1751145), [18.2](https://bugs.launchpad.net/bugs/1759318), [19.4](https://pad.lv/1851428)
 
 4. Your console will also prompt to perform the necessary changes for an
    upstream version bump in cloud-init repo.
 5. git commit -a.  The git commit message should look like others:

        release 19.4
        
        Bump the version in cloudinit/version.py to be 19.4 and update ChangeLog.

        LP: #<YOUR_UPSTREAM_BUG>
 6. Tag.  At this point running 'tox' will fail, complaining that your version does not match what git-describe does.  To fix that you have to tag.

        git tag --annotate --sign YY.N

 7. push the branch up for review and create a merge proposal.  We will use that MP for some documentation on things that have been tested.
    Example merge proposals: [17.2](https://code.launchpad.net/~smoser/cloud-init/+git/cloud-init/+merge/335233), [18.1](https://code.launchpad.net/~smoser/cloud-init/+git/cloud-init/+merge/338588)
    
    **Note**: you need to push the tag or c-i will fail in check version.
    
## Push signed tag to git
This is mostly same as merging anything else and pushing, but make sure to push the tag.

    git checkout master
    git push upstream HEAD 17.2
    
## Update Release info on Launchpad.
Go to https://launchpad.net/cloud-init click the milestone that we're releasing.  That will take you to [lp/cloud-init/+milestone/<X.Y>](http://launchpad.net/cloud-init/+milestone/17.2) .  Hit 'Create release'.

 Model the Release notes after other releases such as [17.1](https://launchpad.net/cloud-init/+milestone/17.1/) or [17.2](https://launchpad.net/cloud-init/+milestone/17.2)

To help get some of those bits of information, add '| wc -l' for just the numbers. not done here to have you sanity check output.

  * just get log into a file

        git log 18.2..HEAD > git-log

  * contributors

        grep Author git-log | sed 's,.*: ,,'  | sort -u

  * top level domains

        grep Author git-log | sed 's,.*: ,,'  | sort -u | sed 's,.*@,,' | sort -u

  * bugs

        grep '^[ ]*LP' git-log | sed -e 's,#,,g' -e 's,.*LP: ,,' -e 's/,[ ]*/\n/'


## Upload source tarball to Launchpad.
Then upload that to launchpad.  
    
    $ ./tools/make-tarball 
    cloud-init-17.2.tar.gz
    
    $ gpg --sign --armor --detach-sig cloud-init-17.2.tar.gz


Note, we can do this step including the 'Update Release info' step with with 'lp-project-upload' from 'lptools' package:


    $ lp-project-upload cloud-init 17.2 cloud-init-17.2.tar.gz 17.3 changelog-file releasenotes-file
    
    
## Close bugs.
Any bugs that were listed should be marked as 'fix-released' now.
There is a tool in [uss-tableflip](https://github.com/CanonicalLtd/uss-tableflip) called lp-bugs-released that makes this sane.

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

  * Go to https://launchpad.net/cloud-init/trunk . Create a milestone, enter the next release number (YY.1) and pick a target date.
