#!/usr/bin/env python3
"""
Hot deployment system for Skycards bot updates
Updates running container without rebuilding
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run command and handle errors"""
    print(f"[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"[+] {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[-] {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python deploy_update.py <nas_ip_address>")
        sys.exit(1)
        
    nas_ip = sys.argv[1]
    
    print("SKYCARDS HOT DEPLOYMENT SYSTEM")
    print("=" * 50)
    
    # Step 1: Copy updated file to NAS
    print("[*] Copying rare_hunter.py to NAS...")
    scp_cmd = f'scp synology-deploy/rare_hunter.py TheDrizzle@{nas_ip}:/volume1/docker/skycards/temp_rare_hunter.py'
    if not run_command(scp_cmd, "Copy file to NAS"):
        sys.exit(1)
    
    # Step 2: Hot-swap the file in running container
    print("[*] Hot-swapping file in running container...")
    ssh_cmd = f'''ssh TheDrizzle@{nas_ip} "
        cd /volume1/docker/skycards/skycards-bot &&
        sudo docker cp temp_rare_hunter.py skycards-bot:/app/rare_hunter.py &&
        sudo docker exec skycards-bot python -c 'import sys; sys.path.insert(0, \"/app\"); import importlib; import rare_hunter; importlib.reload(rare_hunter); print(\"Module reloaded successfully\")' &&
        rm ../temp_rare_hunter.py &&
        echo '[+] Hot deployment completed!'
    "'''
    
    if not run_command(ssh_cmd, "Hot-swap in container"):
        print("[-] Hot deployment failed, falling back to restart...")
        # Fallback: restart container
        restart_cmd = f'ssh TheDrizzle@{nas_ip} "cd /volume1/docker/skycards/skycards-bot && sudo docker-compose restart"'
        run_command(restart_cmd, "Restart container")
    
    print("\n[+] Deployment completed! Check bot logs for OAuth success.")
    
    # Show recent logs
    log_cmd = f'ssh TheDrizzle@{nas_ip} "sudo docker logs skycards-bot --since 2m"'
    print("\nRecent logs:")
    logs = run_command(log_cmd, "Get recent logs")
    if logs:
        print(logs)

if __name__ == "__main__":
    main()