@echo off
set USERHOST=TheDrizzle@192.168.4.75
set BASE=/volume1/docker/skycards

echo === CREATE DIRECTORIES ON NAS ===
ssh %USERHOST% "mkdir -p %BASE%/repo %BASE%/releases %BASE%/deploy %BASE%/shared"

echo === INIT BARE REPO ===
ssh %USERHOST% "git init --bare %BASE%/repo"

echo === INSTALL post-receive HOOK ===
ssh %USERHOST% "cat > %BASE%/repo/hooks/post-receive <<'HOOK'
#!/bin/bash
set -euo pipefail
APP_DIR=\"%BASE%\"
REPO_DIR=\"$APP_DIR/repo\"
DEPLOY_DIR=\"$APP_DIR/deploy\"
RELEASES_DIR=\"$APP_DIR/releases\"
SHARED_DIR=\"$APP_DIR/shared\"

TS=\$(date +%%Y%%m%%d-%%H%%M%%S)
NEW_RELEASE=\"$RELEASES_DIR/\$TS\"

mkdir -p \"\$NEW_RELEASE\"
git --work-tree=\"\$NEW_RELEASE\" --git-dir=\"\$REPO_DIR\" checkout -f

# link shared assets
ln -sfn \"\$SHARED_DIR/.env\"            \"\$NEW_RELEASE/.env\"
ln -sfn \"\$SHARED_DIR/aircraft_data\"   \"\$NEW_RELEASE/aircraft_data\"
ln -sfn \"\$SHARED_DIR/watchlist.json\"  \"\$NEW_RELEASE/watchlist.json\"

# quick smoke test if present
if [ -f \"\$NEW_RELEASE/quick_test.sh\" ]; then
  bash \"\$NEW_RELEASE/quick_test.sh\" || { echo '[HOOK] Tests failed'; exit 1; }
fi

# flip symlink atomically
ln -sfn \"\$NEW_RELEASE\" \"\$DEPLOY_DIR/current\"

# restart compose (try different docker paths for Synology)
cd \"\$DEPLOY_DIR/current\"
sudo /usr/local/bin/docker compose up -d 2>/dev/null || sudo docker-compose up -d 2>/dev/null || sudo /usr/syno/bin/docker-compose up -d

# keep last 5 releases
ls -1dt \"\$RELEASES_DIR\"/* | tail -n +6 | xargs -r rm -rf

echo \"[HOOK] Deployed \$TS\"
HOOK
chmod +x %BASE%/repo/hooks/post-receive"

echo === PRIME SHARED FILES ===
ssh %USERHOST% "mkdir -p %BASE%/shared/aircraft_data && touch %BASE%/shared/.env && touch %BASE%/shared/watchlist.json && [ -s %BASE%/shared/watchlist.json ] || echo '{\"aircraft\":[],\"registrations\":[],\"airports\":[]}' > %BASE%/shared/watchlist.json"

echo === ADD NAS REMOTE LOCALLY ===
git remote remove nas 2>nul
git remote add nas ssh://%USERHOST%%BASE%/repo

echo Done. Next: run DEPLOY.bat
pause