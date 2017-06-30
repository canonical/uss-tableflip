#!/bin/sh
# Reboot a system and by default clean out cloud-init logs and data.
#
# Copyright 2017 Canonical Ltd.
# Scott Moser <scott.moser@canonical.com>
# Joshua Powers <josh.powers@canonical.com>

me=${0}
PATH=${me%/*}:$PATH

error() { echo "$@" 1>&2; }
fail() { error "$@"; exit 1; }

[ "$(id -u)" = "0" ] || fail "not root"
clean=false
keep_logs=false
save=""
reboot=true
for i in "$@"; do
   case "$i" in
      clean) clean=true;;
      keep?logs) keep_logs=true;;
      save=*) save=${i#save=};;
      no-reboot) reboot=false;;
   esac
done

if [ -n "$save" ]; then
   logs-save "$save" || fail "failed save data"
   error "saved to $save"
fi

if $clean; then
   # clean but leave the seed directory due to lxc datasource
   ( set -e;
     cd /var/lib/cloud
     for i in *; do
         [ "$i" = "seed" ] && continue
         rm -Rf "$i"
     done ) || fail "failed clean of /var/lib/cloud"
   error "cleared /var/lib/cloud"
fi

if ! $keep_logs; then
   rm -Rf /var/log/cloud* || fail "failed remove logs"
   error "cleared logs"
else
   error "kept logs"
fi

if $reboot; then
    error "rebooting"
    reboot
fi
