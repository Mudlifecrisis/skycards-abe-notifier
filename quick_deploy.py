
import subprocess

def deploy_oauth_fix():
    try:
        # SSH and deploy OAuth2 fix
        cmd = [
            'ssh', '-o', 'ConnectTimeout=10', 
            'TheDrizzle@192.168.1.78',
            'cd /volume1/docker/skycards/skycards-bot && sudo docker-compose restart'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print('SUCCESS: OAuth2 fix deployed and container restarted')
            return True
        else:
            print(f'FAILED: {result.stderr}')
            return False
            
    except Exception as e:
        print(f'ERROR: {e}')
        return False

if __name__ == '__main__':
    deploy_oauth_fix()
