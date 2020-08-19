#!/bin/bash

set -u
set -e

SSH_PORT=22
SSH_USER=algo
SSH_KEY=~/.ssh/eugene_nbp_integration
SSH_CMD="ssh -i "$SSH_KEY" -l "$SSH_USER" -p $SSH_PORT -o 'StrictHostKeyChecking no' -o 'IdentitiesOnly yes'"
remoteHostName="47.52.113.101"
trgDir="$remoteHostName:/home/algo/nbp/"

hn="`cat /etc/hostname`"

if [ "$hn" = "$remoteHostName" ]; then
	echo cannot install from the remote host >&2
	exit 1
fi

rsync -T=/tmp/ --exclude-from=.rsync_exclusions \
	-rt -e "$SSH_CMD" \
	"../tgui" "$trgDir"
rsync -T=/tmp/ --exclude-from=.rsync_exclusions \
	--links \
	-rt -e "$SSH_CMD" \
	"../tgui/tgui.py" "$trgDir/tgui/"
