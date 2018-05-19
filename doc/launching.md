# Launching instances on different clouds #
General goal of this doc is to show how to launch images of ubuntu.

## Azure ##
For more information and a convenience wrapper
see [az-ubuntu](https://gist.github.com/smoser/5806147)

## Dreamhost cloud Dream Compute ##

Dreamcompute provides a generally open openstack installation.

See OpenStack for more information.

## AWS / Amazon / EC2 ##
Use script `./bin/launch-ec2`

## Google Compute / GCE ###
### CLI Installation ###
Use the `openstack` cli.

  * **pypi**: gcloud
  * **other**: [GCE Doc](https://cloud.google.com/sdk/downloads)


### Find an image ###
Ubuntu publishes stream data for images.  `image-status` can list gce.
See bug [1682896](https://bugs.launchpad.net/cloud-images/+bug/1682896).

    $ image-status gce-daily region=us-east1
    $ artful   20171208    us-east1        daily-ubuntu-1710-artful-v20171208
    $ bionic   20171208    us-east1        daily-ubuntu-1804-bionic-v20171208
    $ trusty   20171208    us-east1        daily-ubuntu-1404-trusty-v20171208
    $ xenial   20171208    us-east1        daily-ubuntu-1604-xenial-v20171208
    $ zesty    20171208    us-east1        daily-ubuntu-1704-zesty-v20171208


### Launching ###
The following is an example of a complete command line.  Some
things are not necessary.


    $ name="user-provided-name"
    $ gcloud compute instances create $name \
       --zone=us-east1-b \
       --image daily-ubuntu-1604-xenial-v20171011 \
       --image-project ubuntu-os-cloud-devel

Variations

  * **--image-project=ubuntu-os-cloud-devel** or **--image-project ubuntu-os-cloud**.  Use '-devel' variety for daily.
  * **--metadata-from-file user-data=/tmp/userdata**

## Joyent ##
### CLI Installation ###
Joyent client is a node client at '[node-smartdc](https://github.com/joyent/node-smartdc)'

Upstream API documentation at https://apidocs.joyent.com/cloudapi/ .

    $ apt-get install --no-install-recommends npm
    $ mkdir joyent
    $ cd joyent
    $ npm install smartdc json

That creates a 'joyent' directory with 'node_modules' in it.

Then you can:

    $ _b=$PWD/joyent/node_modules
    $ export PATH=$b/smartdc/bin:$b/smartdc/json:$PATH

### Login / Auth ###
Example creds look like this.  They use info from your ssh key.

    REGION="${REGION:-us-east-2}"
    export SDC_URL="${SDC_URL:-https://${REGION}.api.joyent.com}"
    export SDC_ACCOUNT=smoser
    export SDC_KEY_ID=$(ssh-keygen -l -f ~/.ssh/id_rsa.pub |
        awk '{print $2}' | tr -d '\n')


### Find and image ###
There is a web interface with information on Ubuntu images at
 https://docs.joyent.com/public-cloud/instances/virtual-machines/images/linux/ubuntu-certified

    # img=14b4ff36-d0f8-11e5-a8b1-e343c129d7f0
    $ sdc-listimages
    ...
    {
      "id": "5147129d-8b6a-48d6-9aef-961206f5706c",
      "name": "ubuntu-certified-16.10",
      "version": "20161012.3",
      "os": "linux",
      "requirements": {},
      "type": "zvol",
      "description": "Ubuntu 16.10 (20161012.3 64-bit). Certified Ubuntu Server Cloud Image from Canonical.",
      "files": [
        {
          "compression": "gzip",
          "sha1": "6ca144451e3a3f29efcba4a117e6edf205c4c433",
          "size": 302352902
        }
      ],
      "tags": {
        "default_user": "ubuntu",
        "role": "os"
      },
      "homepage": "https://docs.joyent.com/images/linux/ubuntu-certified",
      "published_at": "2016-10-13T18:05:47.000Z",
      "owner": "9dce1460-0c4c-4417-ab8b-25ca478c5a78",
      "public": true,
      "state": "active"
    },

    $ sdc-listimages | pastebinit
    http://paste.ubuntu.com/26171559/

### Sizes (Packages) ###

    $ sdc-listpackages
    ...
     {
       "name": "k4-highcpu-kvm-1.75G",
       "memory": 1792,
       "disk": 51200,
       "swap": 7168,
       "vcpus": 1,
       "lwps": 4000,
       "default": false,
       "id": "14b5edc4-d0f8-11e5-b4d2-b3e6e8c05f9d",
       "version": "1.0.3",
       "description": "Compute Optimized KVM 1.75G RAM - 1 vCPU - 50 GB Disk",
       "group": "Compute Optimized KVM"
     },
    ...
    $ sdc-listpackages  | pastebinit
    http://paste.ubuntu.com/26171637/


### Launching ###

    $ userdata="$(cat ./my-user-data)"
    $ name=user-provided-name
    $ sdc-createmachine  \
       --image=$img --package=$package \
       --metadata-file="cloud-init:user-data=/tmp/my-userdata" \
       --name=$name



## LXD ##

    lxc launch xenial lxd-user-data "--config=user.user-data=$(cat user-data)"


## OpenStack ##
### CLI Installation ###
Use the `openstack` cli.

  * **package**: python3-openstackclient
  * **pypi**: python-openstackclient

### Login / Auth ###
Get your credentials in a 'novarc' file.  it might look something like:

    export OS_AUTH_URL=http://10.245.161.156:5000/v3
    export OS_USERNAME=smoser
    export OS_PASSWORD=XXXXXXXXXXXX
    export OS_USER_DOMAIN_NAME=user
    export OS_PROJECT_NAME=smoser
    export OS_PROJECT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    export OS_PROJECT_DOMAIN_NAME=user
    export OS_AUTH_VERSION=3
    export OS_IDENTITY_API_VERSION=3
    export OS_REGION_NAME=serverstack

### SSH Keys ####
Upload a key:

    $ openstack keypair create --public-key ~/.ssh/id_rsa.pub default-key


### Find an image ###
List the images on an openstack server with.  They can generally be
referenced by Name or ID.

    $ openstack image list
    +--------------------------------------+---------------+-------------+
    | ID                                   | Name          | Status      |
    +--------------------------------------+---------------+-------------+
    | a0de1f1d-0312-44c3-94a1-c04d70de16ab | CentOS-6      | active      |
    | c922a7d0-cac5-4913-9b73-1ef84ae7ab2b | CentOS-7      | active      |
    | d83cc53a-720a-4972-8d9a-f92299571920 | CentOS-7      | deactivated |
    | b67b74bc-c3a8-4087-9c28-de02161fdedd | CoreOS        | deactivated |
    | 359d0683-fc4b-41e8-93a2-e79f9c7b073d | CoreOS-Stable | active      |
    | 388b1c23-5ecf-47e6-abb4-3e97e978f662 | Debian-8      | active      |
    | b105ad3b-7df8-4318-9c3d-4e4fa4cc4563 | Debian-8      | deactivated |
    | 8218ff6f-7c0c-4b4e-98a6-9d3ffb69f1ea | Debian-9      | active      |
    | 7f9b44a1-27e3-4cd0-a60c-91b333b4f28c | Fedora-25     | active      |
    | c02561c3-7861-4cf3-95d4-26ec66f625ba | Ubuntu-14.04  | active      |
    | 2c84a3bf-6858-41d5-8724-d6a45f771f20 | Ubuntu-16.04  | active      |
    +--------------------------------------+---------------+-------------+

### Sizes ####
Launching an instance requires picking a flavor (size).  List available
sizes with:

    $ dreamcompute openstack flavor list
    +-----+----------------+-------+------+-----------+-------+-----------+
    | ID  | Name           |   RAM | Disk | Ephemeral | VCPUs | Is Public |
    +-----+----------------+-------+------+-----------+-------+-----------+
    | 100 | gp1.subsonic   |  1024 |   80 |         0 |     1 | True      |
    | 200 | gp1.supersonic |  2048 |   80 |         0 |     1 | True      |
    | 300 | gp1.lightspeed |  4096 |   80 |         0 |     2 | True      |
    | 400 | gp1.warpspeed  |  8192 |   80 |         0 |     4 | True      |
    | 50  | gp1.semisonic  |   512 |   80 |         0 |     1 | True      |
    | 500 | gp1.hyperspeed | 16384 |   80 |         0 |     8 | True      |
    +-----+----------------+-------+------+-----------+-------+-----------+


### Launch an instance ###
Simplest example launch:

    $ openstack server create \
        --key-name=default-key \
        --flavor=gp1.semisonic \
        --image=Ubuntu-16.04 \
        user-provided-name

Launch with user-data:

    $ openstack server create \
        --key-name=default-key \
        --flavor=gp1.semisonic \
        --image=Ubuntu-16.04 \
        user-provided-name

Variations:

  * **config-drive**: To add a config drive (rather than metadata service)
    pass `--config-drive=1`.  This will affect the datasource used by
    cloud-init.
    
  * **--nic=net-id=<uuid>**: If you have additional networks, you may have
    to provide a `--nic=` flag like: `--nic=net-id=<uuid>` where the uuid
    comes from `openstack network list`.

  * **--user-data=<file>**: read user-data from the file `<file>`.


## Softlayer / IBMCloud / BlueMix ##
Use script `./bin/launch-softlayer`

