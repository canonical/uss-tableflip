# cloud-init upstream release process

This covers the cloud-init upstream release process.

## commit locally, tag, sign, push merge proposal
The change locally to mark a release should look like previous release
commits.

Examples:

 * [17.1](https://git.launchpad.net/cloud-init/commit/?id=17.1)
 * [17.2](https://git.launchpad.net/cloud-init/commit/?id=17.1)
 
The commit content should consist of

 1. File a bug.
 
    * Example Bugs: [18.1](https://pad.lv/1751145), [18.2](https://bugs.launchpad.net/bugs/1759318)
 
 2. changing the number in cloudinit/version.py
 3. updating ChangeLog file in source.
    This is most easily done done by using [log2dch](https://gist.github.com/smoser/813c84bc7a79efc75d3f7fc2f383f12f).
    
        git log 17.1..17.2 | log2dch | sed 's/^   //g'
        
 4. commit.  The git commit message should look like others:

        release 17.2
        
        Bump the version in cloudinit/version.py to be 17.2 and update ChangeLog.
        
 5. Tag.  At this point running 'tox' will fail, complaining that your version does not match what git-describe does.  To fix that you have to tag.

        git tag --annotate --sign

 6. push the branch up for review and create a merge proposal.  We will use that MP for some documentation on things that have been tested.
    Example merge proposals: [17.2](https://code.launchpad.net/~smoser/cloud-init/+git/cloud-init/+merge/335233), [18.1](https://code.launchpad.net/~smoser/cloud-init/+git/cloud-init/+merge/338588)
    
    **Note**: you need to push the tag or c-i will fail in check version.
    
## Push signed tag to git
This is mostly same as merging anything else and pushing, but make sure to push the tag.

    git checkout master
    git push upstream HEAD 17.2
    
## Update Release info on Launchpad.
Go to https://launchpad.net/cloud-init click the milestone that we're releasing.  That will take you to [lp/cloud-init/+milestone/<X.Y>](http://launchpad.net/cloud-init/+milestone/17.2) .  Hit 'Create release'.

 Model the Release notes after other releases such as [17.1](https://launchpad.net/cloud-init/+milestone/17.1/) or [17.2](https://launchpad.net/cloud-init/+milestone/17.2)

## Upload source tarball to Launchpad.
Then upload that to launchpad.  
    
    $ ./tools/make-tarball 
    cloud-init-17.2.tar.gz
    
    $ gpg --sign --armor --detach-sig cloud-init-17.2.tar.gz


Note, we can do this step including the 'Update Release info' step with with 'lp-project-upload' from 'lptools' package:


    $ lp-project-upload cloud-init 17.2 cloud-init-17.2.tar.gz 17.3 changelog-file releasenotes-file
    
    
## Close bugs (fun)
Any bugs that were listed should be marked as 'fix-released' now.
There is a tool in [uss-tableflip](https://github.com/CanonicalLtd/uss-tableflip) called lp-bugs-released that makes this sane.

    # git log <last-release>..<this-release>
    $ git log 17.1..17.2 | grep "^[ ]*LP:" | sort -u
    $ ./lp-bugs-released <version> <bug list here>
 
Basically copy the Release Notes and the Changelog into an email to
Cloud-init Mailing List <cloud-init@lists.launchpad.net>
   
Example Emails from the past at

 * [17.1](https://lists.launchpad.net/cloud-init/msg00106.html)
 
Please sign the email.
 

## Upload to Ubuntu devel release.
Follow the Ubuntu release process doc [ubuntu-release-process](https://gist.github.com/smoser/6391b854e6a80475aac473bba4ef0310#file-ubuntu-release-process-md)

## Update COPR build cloud-init/el-testing repository with latest upstream release
 * /tools/run-centos --srpm 6 --keep
 * CENT_CONTAINER=`lxc list -c n | grep cent | awk '{print $2}'`a
 * SRPM_FILE=`lxc exec $CENT_CONTAINER ls /home/ci-test/cloud-init/*rpm`
 * lxc file pull $CENT_CONTAINER/home/ci-test/cloud-init/cloud-init\*src.rpm .
 * Login to https://copr.fedorainfracloud.org/coprs/g/cloud-init/el-testing/build
 * Click New Build button -> Upload tab -> upload your src.rpm file


# Opening next release

  * Go to https://launchpad.net/cloud-init/trunk . Create a milestone, pick a target date.
