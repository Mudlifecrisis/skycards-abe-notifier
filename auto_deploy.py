#!/usr/bin/env python3
"""
Automatic deployment system for Skycards bot
Claude can trigger this to deploy updates directly to NAS
"""
import subprocess
import sys
import os
import json
from pathlib import Path

class AutoDeployer:
    def __init__(self, nas_ip="192.168.4.75", nas_user="TheDrizzle"):
        self.nas_ip = nas_ip
        self.nas_user = nas_user
        self.project_root = Path(__file__).parent
        self.deployment_path = "/volume1/docker/skycards/skycards-bot"
        
    def log(self, message, level="INFO"):
        """Log deployment messages"""
        print(f"[{level}] {message}")
        
    def run_command(self, cmd, description, check=True):
        """Run command with error handling"""
        self.log(f"Running: {description}")
        try:
            result = subprocess.run(cmd, shell=True, check=check, 
                                  capture_output=True, text=True)
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"FAILED: {description} - {e}", "ERROR")
            if e.stderr:
                self.log(f"Error: {e.stderr.strip()}", "ERROR")
            return None
            
    def test_ssh_connection(self):
        """Test SSH connection to NAS"""
        self.log("Testing SSH connection...")
        cmd = f'ssh -o ConnectTimeout=10 {self.nas_user}@{self.nas_ip} "echo Connection successful"'
        result = self.run_command(cmd, "SSH connection test", check=False)
        return result and result.returncode == 0
        
    def deploy_file(self, local_file, remote_file=None):
        """Deploy single file to NAS"""
        if not remote_file:
            remote_file = Path(local_file).name
            
        local_path = self.project_root / "synology-deploy" / local_file
        if not local_path.exists():
            self.log(f"Local file not found: {local_path}", "ERROR")
            return False
            
        # Copy file to NAS temp location
        temp_path = f"/tmp/skycards_{remote_file}"
        scp_cmd = f'scp "{local_path}" {self.nas_user}@{self.nas_ip}:{temp_path}'
        
        if not self.run_command(scp_cmd, f"Upload {local_file}"):
            return False
            
        # Hot-swap file in container
        swap_cmd = f'''ssh {self.nas_user}@{self.nas_ip} "
            sudo docker cp {temp_path} skycards-bot:/app/{remote_file} &&
            rm {temp_path} &&
            echo 'File deployed successfully: {remote_file}'
        "'''
        
        return bool(self.run_command(swap_cmd, f"Hot-swap {remote_file}"))
        
    def restart_container(self):
        """Restart the bot container"""
        restart_cmd = f'''ssh {self.nas_user}@{self.nas_ip} "
            cd {self.deployment_path} &&
            sudo docker-compose restart
        "'''
        return bool(self.run_command(restart_cmd, "Restart container"))
        
    def get_container_logs(self, lines=20):
        """Get recent container logs"""
        log_cmd = f'ssh {self.nas_user}@{self.nas_ip} "sudo docker logs skycards-bot --tail {lines}"'
        result = self.run_command(log_cmd, f"Get last {lines} log lines", check=False)
        return result.stdout if result else "Could not retrieve logs"
        
    def deploy_update(self, files=None, restart=True, description=""):
        """Deploy update with specified files"""
        self.log(f"Starting deployment: {description}")
        
        # Test connection first
        if not self.test_ssh_connection():
            self.log("SSH connection failed - cannot deploy", "ERROR")
            return False
            
        success = True
        
        # Deploy specified files
        if files:
            for file_info in files:
                if isinstance(file_info, str):
                    local_file = remote_file = file_info
                else:
                    local_file, remote_file = file_info
                    
                if not self.deploy_file(local_file, remote_file):
                    success = False
                    
        # Restart container if requested
        if restart and success:
            success = self.restart_container()
            
        if success:
            self.log(f"Deployment successful: {description}", "SUCCESS")
            # Show recent logs
            logs = self.get_container_logs(10)
            self.log("Recent container logs:")
            print(logs)
        else:
            self.log(f"Deployment failed: {description}", "ERROR")
            
        return success

def main():
    """Command line interface for deployment"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-deploy Skycards bot updates")
    parser.add_argument("--files", nargs="+", help="Files to deploy")
    parser.add_argument("--no-restart", action="store_true", help="Don't restart container")
    parser.add_argument("--description", default="Manual deployment", help="Deployment description")
    parser.add_argument("--logs", type=int, default=20, help="Number of log lines to show")
    
    args = parser.parse_args()
    
    deployer = AutoDeployer()
    
    if args.files:
        success = deployer.deploy_update(
            files=args.files,
            restart=not args.no_restart,
            description=args.description
        )
        sys.exit(0 if success else 1)
    else:
        # Just show logs
        logs = deployer.get_container_logs(args.logs)
        print(logs)

if __name__ == "__main__":
    main()