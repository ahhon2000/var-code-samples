#!/bin/bash

set -u
set -e


SSH_PORT=1187
SSH_CMD="ssh -p $SSH_PORT -o 'StrictHostKeyChecking no' -o 'IdentitiesOnly yes'"
remoteHostName="specsrv"
trgDir="$remoteHostName:/home/ahhon/"

hn="`cat /etc/hostname`"

if [ "$hn" = "$remoteHostName" ]; then
	echo cannot install from the remote host >&2
	exit 1
fi

rsync -T=/tmp/ --exclude-from=.rsync_exclusions -rt -e "$SSH_CMD" \
	"../specBot" "$trgDir"
