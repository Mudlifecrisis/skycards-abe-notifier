@echo off
echo ===============================================
echo COPY SHARED FILES TO NAS (TheDrizzle)
echo ===============================================
echo.

set ADMIN_HOST=TheDrizzle@192.168.4.75
set BASE=/volume1/docker/skycards

echo [1/4] Creating shared directory structure...
ssh %ADMIN_HOST% "mkdir -p %BASE%/shared/aircraft_data"

echo.
echo [2/4] Copying .env file...
if exist ".env" (
    scp .env %ADMIN_HOST%:%BASE%/shared/.env
    echo ✅ .env copied
) else (
    echo ⚠️  .env not found locally - creating placeholder on NAS
    ssh %ADMIN_HOST% "cat > %BASE%/shared/.env << 'ENV_EOF'
DISCORD_BOT_TOKEN=your_bot_token_here
OPENSKY_API={\"clientId\":\"porkchopexpress-api-client\",\"clientSecret\":\"your_secret_here\"}
RARE_CH_ID=your_channel_id_here
ENV_EOF"
    echo ⚠️  You need to edit %BASE%/shared/.env on the NAS with real values
)

echo.
echo [3/4] Copying aircraft database...
if exist "aircraft_data" (
    echo Found aircraft_data directory - this may take a while for 515K aircraft...
    scp -r aircraft_data/* %ADMIN_HOST%:%BASE%/shared/aircraft_data/
    echo ✅ Aircraft database copied
) else (
    echo ⚠️  aircraft_data not found locally
    echo Copy it later with: scp -r aircraft_data %ADMIN_HOST%:%BASE%/shared/
)

echo.
echo [4/4] Creating watchlist.json...
if exist "watchlist.json" (
    scp watchlist.json %ADMIN_HOST%:%BASE%/shared/
    echo ✅ watchlist.json copied
) else (
    echo Creating default watchlist.json...
    ssh %ADMIN_HOST% "echo '{\"aircraft\":[\"C17\",\"H47\",\"A10\",\"F16\",\"AB18\",\"VUT1\",\"KFIR\"],\"registrations\":[],\"airports\":[]}' > %BASE%/shared/watchlist.json"
    echo ✅ Default watchlist created
)

echo.
echo ===============================================
echo ✅ SHARED FILES COPIED!
echo.
echo Files on NAS:
ssh %ADMIN_HOST% "ls -la %BASE%/shared/"
echo.
echo Aircraft database:
ssh %ADMIN_HOST% "ls -la %BASE%/shared/aircraft_data/ | head -5"

echo.
echo Ready for first deployment:
echo   DEPLOY_THEDRIZZLE.bat "initial deploy"
echo ===============================================
pause