#!/bin/bash
set -e

PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Validate PUID/PGID are numeric and non-root
if ! echo "$PUID" | grep -qE '^[0-9]+$' || ! echo "$PGID" | grep -qE '^[0-9]+$'; then
    echo "ERROR: PUID and PGID must be numeric (got PUID=$PUID, PGID=$PGID)" >&2
    exit 1
fi

echo "Starting with UID: $PUID, GID: $PGID"

# Update bluewatch group GID
if [ "$(id -g bluewatch 2>/dev/null)" != "$PGID" ]; then
    groupmod -o -g "$PGID" bluewatch
fi

# Update bluewatch user UID and ensure group membership
if [ "$(id -u bluewatch 2>/dev/null)" != "$PUID" ]; then
    usermod -o -u "$PUID" bluewatch
fi

# Ensure bluewatch is in the bluetooth group
usermod -aG bluetooth bluewatch 2>/dev/null || true

# Fix ownership of data directory
chown -R bluewatch:bluewatch /data

exec gosu bluewatch "$@"
