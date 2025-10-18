#!/bin/bash
set -euo pipefail

APP_DIR='/volume1/docker/skycards'
REPO_DIR="$APP_DIR/repo"
DEPLOY_DIR="$APP_DIR/deploy"
RELEASES_DIR="$APP_DIR/releases"
SHARED_DIR="$APP_DIR/shared"

TS=$(date +%Y%m%d-%H%M%S)
NEW_RELEASE="$RELEASES_DIR/$TS"

echo "[HOOK] Starting deployment: $TS"

# Checkout to new release
mkdir -p "$NEW_RELEASE"
git --work-tree="$NEW_RELEASE" --git-dir="$REPO_DIR" checkout -f

# Link shared assets
ln -sfn "$SHARED_DIR/.env" "$NEW_RELEASE/.env"
ln -sfn "$SHARED_DIR/aircraft_data" "$NEW_RELEASE/aircraft_data" 
ln -sfn "$SHARED_DIR/watchlist.json" "$NEW_RELEASE/watchlist.json"

# Atomic symlink flip
ln -sfn "$NEW_RELEASE" "$DEPLOY_DIR/current"

# Copy files to main directory for bind mounting
echo "[HOOK] Copying files to main directory..."
cp -f "$NEW_RELEASE/docker-compose.yml" "$APP_DIR/docker-compose.yml"
cp -f "$NEW_RELEASE/bot.py" "$APP_DIR/bot.py"
cp -f "$NEW_RELEASE/rare_hunter.py" "$APP_DIR/rare_hunter.py"
cp -f "$NEW_RELEASE/aliases.json" "$APP_DIR/aliases.json"
cp -f "$NEW_RELEASE/requirements.txt" "$APP_DIR/requirements.txt"

# Cleanup old releases (keep 5)
ls -1dt "$RELEASES_DIR"/* | tail -n +6 | xargs -r rm -rf

echo "[HOOK] ✅ Deployed $TS - Files ready for bind mount"
echo "[HOOK] ⚠️  Manual restart required: Synology Container Manager → skycards-bot → Restart"