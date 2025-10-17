@echo off
set USERHOST=TheDrizzle@192.168.4.75
set BASE=/volume1/docker/skycards

echo === CREATE DIRECTORIES ON NAS ===
ssh %USERHOST% "mkdir -p %BASE%/repo %BASE%/releases %BASE%/deploy %BASE%/shared"

echo === INIT BARE REPO ===
ssh %USERHOST% "git init --bare %BASE%/repo"

echo === INSTALL post-receive HOOK WITH WEBHOOK ===
ssh %USERHOST% "cat > %BASE%/repo/hooks/post-receive <<'HOOK'
#!/bin/bash
set -euo pipefail
APP_DIR=\"%BASE%\"
REPO_DIR=\"$APP_DIR/repo\"
DEPLOY_DIR=\"$APP_DIR/deploy\"
RELEASES_DIR=\"$APP_DIR/releases\"
SHARED_DIR=\"$APP_DIR/shared\"

# Discord webhook URL (replace with your webhook URL)
WEBHOOK_URL=\"https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN\"

TS=\$(date +%%Y%%m%%d-%%H%%M%%S)
NEW_RELEASE=\"$RELEASES_DIR/\$TS\"

echo \"[HOOK] Starting deployment: \$TS\"

# Get git commit info for notification
COMMIT_HASH=\$(git rev-parse --short HEAD)
COMMIT_MSG=\$(git log -1 --pretty=format:'%%s')

# Notify deployment start
curl -s -H 'Content-Type: application/json' \
  -d \"{\\\"content\\\":\\\"🚀 **Deploying Skycards** \\\`\$TS\\\`\\\n**Commit:** \\\`\$COMMIT_HASH\\\` \$COMMIT_MSG\\\n**Status:** Starting...\\\"}\" \
  \"\$WEBHOOK_URL\" >/dev/null || echo \"[HOOK] Webhook failed (continuing)\"

mkdir -p \"\$NEW_RELEASE\"
git --work-tree=\"\$NEW_RELEASE\" --git-dir=\"\$REPO_DIR\" checkout -f

# link shared assets
ln -sfn \"\$SHARED_DIR/.env\"            \"\$NEW_RELEASE/.env\"
ln -sfn \"\$SHARED_DIR/aircraft_data\"   \"\$NEW_RELEASE/aircraft_data\"
ln -sfn \"\$SHARED_DIR/watchlist.json\"  \"\$NEW_RELEASE/watchlist.json\"

# quick smoke test if present
TEST_RESULT=\"passed\"
if [ -f \"\$NEW_RELEASE/quick_test.sh\" ]; then
  if ! bash \"\$NEW_RELEASE/quick_test.sh\"; then
    echo '[HOOK] Tests failed'
    curl -s -H 'Content-Type: application/json' \
      -d \"{\\\"content\\\":\\\"❌ **Skycards Deploy Failed** \\\`\$TS\\\`\\\n**Error:** Tests failed\\\n**Commit:** \\\`\$COMMIT_HASH\\\` \$COMMIT_MSG\\\"}\" \
      \"\$WEBHOOK_URL\" >/dev/null || true
    exit 1
  fi
fi

# flip symlink atomically
ln -sfn \"\$NEW_RELEASE\" \"\$DEPLOY_DIR/current\"

# restart compose (try different docker paths for Synology)
cd \"\$DEPLOY_DIR/current\"
if sudo /usr/local/bin/docker compose up -d 2>/dev/null || sudo docker-compose up -d 2>/dev/null || sudo /usr/syno/bin/docker-compose up -d; then
  echo \"[HOOK] Container restarted successfully\"
  
  # Wait for healthcheck
  sleep 30
  
  # Check if container is healthy (try different docker paths)
  if sudo /usr/local/bin/docker inspect --format='{{.State.Health.Status}}' skycards-bot 2>/dev/null | grep -q \"healthy\" || sudo docker inspect --format='{{.State.Health.Status}}' skycards-bot 2>/dev/null | grep -q \"healthy\"; then
    HEALTH_STATUS=\"✅ Healthy\"
  else
    HEALTH_STATUS=\"⚠️ Starting...\"
  fi
  
  # Success notification
  curl -s -H 'Content-Type: application/json' \
    -d \"{\\\"content\\\":\\\"✅ **Skycards Deployed Successfully** \\\`\$TS\\\`\\\n**Commit:** \\\`\$COMMIT_HASH\\\` \$COMMIT_MSG\\\n**Health:** \$HEALTH_STATUS\\\n**Location:** \\\`deploy/current -> releases/\$TS\\\`\\\"}\" \
    \"\$WEBHOOK_URL\" >/dev/null || echo \"[HOOK] Success webhook failed\"
    
else
  echo \"[HOOK] Container restart failed\"
  curl -s -H 'Content-Type: application/json' \
    -d \"{\\\"content\\\":\\\"❌ **Skycards Deploy Failed** \\\`\$TS\\\`\\\n**Error:** Container restart failed\\\n**Commit:** \\\`\$COMMIT_HASH\\\` \$COMMIT_MSG\\\"}\" \
    \"\$WEBHOOK_URL\" >/dev/null || true
  exit 1
fi

# keep last 5 releases
ls -1dt \"\$RELEASES_DIR\"/* | tail -n +6 | xargs -r rm -rf

echo \"[HOOK] ✅ Deployed \$TS\"
HOOK
chmod +x %BASE%/repo/hooks/post-receive"

echo === PRIME SHARED FILES ===
ssh %USERHOST% "mkdir -p %BASE%/shared/aircraft_data && touch %BASE%/shared/.env && touch %BASE%/shared/watchlist.json && [ -s %BASE%/shared/watchlist.json ] || echo '{\"aircraft\":[],\"registrations\":[],\"airports\":[]}' > %BASE%/shared/watchlist.json && chmod 600 %BASE%/shared/.env"

echo === ADD NAS REMOTE LOCALLY ===
git remote remove nas 2>nul
git remote add nas ssh://%USERHOST%%BASE%/repo

echo.
echo ===============================================
echo ✅ GIT DEPLOY SETUP COMPLETE WITH WEBHOOKS!
echo.
echo IMPORTANT: Edit the webhook URL in the post-receive hook:
echo   1. Go to Discord Server Settings > Integrations > Webhooks
echo   2. Create New Webhook for your deployment channel
echo   3. Copy the webhook URL
echo   4. SSH to NAS and edit: nano %BASE%/repo/hooks/post-receive
echo   5. Replace YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN with real URL
echo.
echo Then run: DEPLOY.bat "initial deploy"
echo ===============================================
pause