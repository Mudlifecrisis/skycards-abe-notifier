@echo off
echo ===============================================
echo SYNOLOGY DOCKER PATH DETECTION
echo ===============================================
echo.
echo Checking common Docker locations on your NAS...

set USERHOST=TheDrizzle@192.168.4.75

echo [1/4] Testing /usr/local/bin/docker...
ssh %USERHOST% "sudo /usr/local/bin/docker --version" && (
    echo ✅ Found Docker at: /usr/local/bin/docker
    set DOCKER_PATH=/usr/local/bin/docker
    goto compose_test
) || echo ❌ Not found at /usr/local/bin/docker

echo.
echo [2/4] Testing /usr/bin/docker...
ssh %USERHOST% "sudo /usr/bin/docker --version" && (
    echo ✅ Found Docker at: /usr/bin/docker
    set DOCKER_PATH=/usr/bin/docker
    goto compose_test
) || echo ❌ Not found at /usr/bin/docker

echo.
echo [3/4] Testing /usr/syno/bin/docker...
ssh %USERHOST% "sudo /usr/syno/bin/docker --version" && (
    echo ✅ Found Docker at: /usr/syno/bin/docker
    set DOCKER_PATH=/usr/syno/bin/docker
    goto compose_test
) || echo ❌ Not found at /usr/syno/bin/docker

echo.
echo [4/4] Testing default docker command...
ssh %USERHOST% "sudo docker --version" && (
    echo ✅ Found Docker via PATH
    set DOCKER_PATH=docker
    goto compose_test
) || echo ❌ Docker not found via PATH

echo.
echo ❌ Docker not found at any common location!
echo.
echo Try finding Docker manually:
echo   ssh %USERHOST%
echo   sudo find / -name docker -type f 2>/dev/null
echo.
pause
exit /b 1

:compose_test
echo.
echo Testing Docker Compose with found Docker path...

if "%DOCKER_PATH%"=="/usr/local/bin/docker" (
    ssh %USERHOST% "sudo /usr/local/bin/docker compose version" && (
        echo ✅ Docker Compose v2 available
        echo Your deployment will use: sudo /usr/local/bin/docker compose
    ) || (
        echo ❌ Docker Compose v2 not available, trying legacy...
        ssh %USERHOST% "sudo docker-compose --version" && (
            echo ✅ Legacy docker-compose available
            echo Your deployment will use: sudo docker-compose
        ) || echo ❌ No Docker Compose found
    )
) else (
    ssh %USERHOST% "sudo %DOCKER_PATH% compose version" && (
        echo ✅ Docker Compose v2 available
        echo Your deployment will use: sudo %DOCKER_PATH% compose
    ) || (
        echo ❌ Docker Compose v2 not available, trying legacy...
        ssh %USERHOST% "sudo docker-compose --version" && (
            echo ✅ Legacy docker-compose available  
            echo Your deployment will use: sudo docker-compose
        ) || echo ❌ No Docker Compose found
    )
)

echo.
echo ===============================================
echo DOCKER PATH DETECTION COMPLETE
echo.
echo The deployment scripts will automatically try:
echo 1. sudo /usr/local/bin/docker compose
echo 2. sudo docker-compose  
echo 3. sudo /usr/syno/bin/docker-compose
echo.
echo Continue with: PRE_FLIGHT_CHECK.bat
echo ===============================================
pause