### Cloud-init COPR RPM Repositories
Cloud-init maintains two COPR rpm repositories:

 * [el-stable](https://copr.fedorainfracloud.org/coprs/g/cloud-init/el-stable/)
 * [el-testing](https://copr.fedorainfracloud.org/coprs/g/cloud-init/el-testing/)

The ``el-stable`` repository is maintained for stable release
updates of cloud-init primarily to provide newer releases of cloud-init
than might otherwise be available in downstream Centos Linux.  The el6
release of el-testing and el-stable is py26 based.  For el7, we're staying
at py27.

The ``el-testing`` repository accepts updates for each cloud-init release
as well as each Stable-Release-Update.


### Packages 
There are currently two packages included in both repositories:

 * cloud-init-el-release
 * cloud-init

The ``cloud-init-el-release`` package provides yum repository files which
point to the cloud-init COPR repositories where these files are hosted.  This
package abstraction allows for migrating respositories to some other location
in the future if needed.


### cloud-init-el-release SOURCE

The source for ``cloud-init-el-release`` is hosted
in three parts:

 * [cloud-init-el-release.spec](https://gist.github.com/raharper/b496c05343d8ac923eea36fd631a2512)
 * [cloud-init-el-stable.repo.tmpl](https://gist.github.com/raharper/c51eb6d72fdb760ac3459821f5bc1deb)
 * [cloud-init-el-testing.repo.tmpl](https://gist.github.com/raharper/4b4ba5a8223998e2a758fa0fefa7a438)

The source rpm is constructed with the following script for each centos
major release (6, 7, 8, ...).


    $ lxc launch images:centos/7/amd64 cent7-srpm-build
    $ lxc exec cent7-srpm-build bash
    $ yum install -y wget rpm-build
    $ mkdir -p ~/rpmbuild/{SOURCES,SPECS}
    $ cd ~/rpmbuild/SPECS
    $ wget
    https://gist.githubusercontent.com/raharper/b496c05343d8ac923eea36fd631a2512/raw/bb927a91ee2a38af7d8484004b4d275b21479572/cloud-init-el-release.spec
    $ cd ~/rpmbuild/SOURCES
    $ wget
    https://gist.githubusercontent.com/raharper/c51eb6d72fdb760ac3459821f5bc1deb/raw/6e51f621871934b54af826a9ff5b6fa21ecf2ac4/cloud-init-el-stable.repo.tmpl
    $ wget
    https://gist.githubusercontent.com/raharper/4b4ba5a8223998e2a758fa0fefa7a438/raw/4e49dbb97649870bd1d21144ccd65c1b60d08d4a/cloud-init-el-testing.repo.tmpl
    $ cd ~/rpmbuild
    $ rpmbuild -ba SPECS/cloud-init-el-release.spec 

The binary output is at ``~/rpmbuild/RPMS/noarch/cloud-init-el-release-<major
version>-2.norarch.rpm``.
The source rpm (SRPM) is located at
``~/rpmbuild/SRPMS/cloud-init-el-release-<major-version>-2.src.rpm``.
The SRPM is used for uploading new release of the package in the COPR repo.



###Handling COPR el-stable Updates

When uploading new source rpms (SRPMS) to th COPR ``el-stable`` repository,
please be aware that the **major version** of the src.rpm matters as it
encodes the ``redhat-release`` requirement.  This means that if you upload an
SRPM built from centos7, then it must only be enabled in the el7 respository
or you will break users when they attempt to install the package on different
releases.  Updating the ``el-stable`` repository flow is as follows:

 * Login to COPR cloud-init project
 https://copr.fedorainfracloud.org/groups/g/cloud-init/coprs/
 * Load the el-stable respository [builds
 page](https://copr.fedorainfracloud.org/coprs/g/cloud-init/el-stable/builds/)
 * Click on "New Build"
 * Select "Upload" for source type
 * Choose the correct SRPM for the major release to upload
 * Select *only* the major release Chroot for the uploaded SRPM (6 for 6, 7 for
         7, etc).  Do NOT enable more than one Chroot for any srpm build.
 * Leave "Enabling Internet access" unchecked
 * Click "Build"


###Testing COPR el-stable Updates

After uploading and building a new el-stable source rpm, to test the
repositores, for each release do

    $ lxc launch images:centos/7/amd64 cent7-el-repo-test
    $ lxc exec cent7-el-repo-test bash
    # cat > /etc/yum.repos.d/ci-bootstrap.repo << EOF 
    > [copr:copr.fedorainfracloud.org:group_cloud-init:el-stable]
    > name=Copr repo for el-stable owned by @cloud-init
    > baseurl=https://copr-be.cloud.fedoraproject.org/results/@cloud-init/el-stable/epel-7-\$basearch/
    > type=rpm-md
    > skip_if_unavailable=True
    > gpgcheck=1
    > gpgkey=https://copr-be.cloud.fedoraproject.org/results/@cloud-init/el-stable/pubkey.gpg
    > repo_gpgcheck=0
    > enabled=1
    > enabled_metadata=1
    > EOF
    # yum install cloud-init-el-release
    # ls -al /etc/yum.repos.d/cloud-init-el*.repo


