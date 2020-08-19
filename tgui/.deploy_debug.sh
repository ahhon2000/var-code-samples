#!/bin/bash

set -u
set -e


SSH_PORT=1029
SSH_CMD="ssh -p $SSH_PORT -o 'StrictHostKeyChecking no' -o 'IdentitiesOnly yes'"
remoteHostName="daxiang"
trgDir="$remoteHostName:/home/ahhon/projects"

hn="`cat /etc/hostname`"

if [ "$hn" = "$remoteHostName" ]; then
	echo cannot install from the remote host >&2
	exit 1
fi

rsync -T=/tmp/ --exclude-from=.rsync_exclusions -rt -e "$SSH_CMD" \
	"../tgui" "$trgDir"
