# ctool - container tool

ctool lives in ubuntu server team's ['scripts'](https://github.com/CanonicalLtd/uss-tableflip/tree/master/scripts) directory

It has some useful functionality for working with lxd containers.

 * Launch a container and wait for it to finish booting.

       $ ctool run-container -v --name=b2 ubuntu-daily:bionic
       Waiting up to 30s for 'b2' to boot.
       ........[b2] done after 8 uptime=8.36s
       [b2] adding user ci-user
       not deleting container 'b2'.

 * Add a user to the container

       $ ctool add-user -v --container=b1 smoser
       [b1] adding user smoser

   add-user also has:

     * `--import-id` to run ssh-import-id as that user
     * `--no-sudo` to *not* add password-less sudo to the user.

 * Execute a command as a user.

       $ ctool exec --container=b1 --user=smoser whoami
       smoser


   It can also change the directory before executing the command:

       $ ctool exec --container=b1 --user=smoser --dir=/etc head -n 3 passwd
       root:x:0:0:root:/root:/bin/bash
       daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
       bin:x:2:2:bin:/bin:/usr/sbin/nologin


 * Get a shell as a given user

       $ ctool exec --container=b1 --dir=/tmp --user=ubuntu
       To run a command as administrator (user "root"), use "sudo <command>".
       See "man sudo_root" for details.

       ubuntu@b1:/tmp$ exit

 * Launch a container, run a command, delete the container.

   This is the heart of script interaction with ctool.  We use it to execute c-i in a clean environment.

   For demonstration  purposes, say you wanted to see what /etc/hosts looks like in a clean environment.  Here, we start a randomly named container, cat /etc/hosts and then delete the container.

       $ ctool run-container ubuntu-daily:bionic cat /etc/hosts
       127.0.0.1 localhost

       # The following lines are desirable for IPv6 capable hosts
       ::1 ip6-localhost ip6-loopback
       fe00::0 ip6-localnet
       ff00::0 ip6-mcastprefix
       ff02::1 ip6-allnodes
       ff02::2 ip6-allrouters
       ff02::3 ip6-allhosts
