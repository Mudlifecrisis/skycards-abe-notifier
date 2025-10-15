#!/usr/bin/env python3
"""
Bot Manager - Start, stop, monitor the Skycards Discord bot
"""
import subprocess
import psutil
import time
import os
from pathlib import Path

class BotManager:
    def __init__(self):
        self.bot_script = Path(__file__).parent / "bot.py"
        self.process = None
        
    def is_bot_running(self) -> bool:
        """Check if bot is actually running"""
        if self.process and self.process.poll() is None:
            return True
            
        # Check for any python process running bot.py
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'bot.py' in ' '.join(cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def start_bot(self) -> bool:
        """Start the Discord bot"""
        if self.is_bot_running():
            print("Bot is already running!")
            return False
            
        try:
            print("Starting Discord bot...")
            self.process = subprocess.Popen(
                ['python', str(self.bot_script)],
                cwd=self.bot_script.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Wait a moment and check if it started successfully
            time.sleep(3)
            if self.process.poll() is None:
                print("Bot started successfully!")
                return True
            else:
                stdout, stderr = self.process.communicate()
                print(f"Bot failed to start:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            print(f"Error starting bot: {e}")
            return False
    
    def stop_bot(self) -> bool:
        """Stop the Discord bot"""
        stopped = False
        
        # Kill our tracked process
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=10)
            stopped = True
            
        # Kill any other bot.py processes
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'bot.py' in ' '.join(cmdline):
                    proc.terminate()
                    stopped = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if stopped:
            print("Bot stopped successfully!")
        else:
            print("No bot process found to stop")
            
        return stopped
    
    def restart_bot(self) -> bool:
        """Restart the Discord bot"""
        print("Restarting bot...")
        self.stop_bot()
        time.sleep(2)
        return self.start_bot()
    
    def get_status(self) -> dict:
        """Get detailed bot status"""
        return {
            'running': self.is_bot_running(),
            'script_exists': self.bot_script.exists(),
            'working_directory': str(self.bot_script.parent)
        }

if __name__ == "__main__":
    manager = BotManager()
    
    import sys
    if len(sys.argv) < 2:
        print("Usage: python bot_manager.py [start|stop|restart|status]")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "start":
        manager.start_bot()
    elif command == "stop":
        manager.stop_bot()
    elif command == "restart":
        manager.restart_bot()
    elif command == "status":
        status = manager.get_status()
        print(f"Bot running: {'YES' if status['running'] else 'NO'}")
        print(f"Script exists: {'YES' if status['script_exists'] else 'NO'}")
        print(f"Working directory: {status['working_directory']}")
    else:
        print("Unknown command. Use: start, stop, restart, or status")