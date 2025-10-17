#!/usr/bin/env python3
"""
Deploy help system update
Claude triggers this to update the help system automatically
"""
from auto_deploy import AutoDeployer

def deploy_help_update():
    """Deploy enhanced help system to NAS"""
    deployer = AutoDeployer()
    
    # Files to deploy for help system update
    files_to_deploy = [
        "bot.py"  # Contains the enhanced help system
    ]
    
    success = deployer.deploy_update(
        files=files_to_deploy,
        restart=True,
        description="Enhanced interactive help system with categories"
    )
    
    if success:
        print("\n🎉 Help system update deployed successfully!")
        print("Users can now use:")
        print("  • !help rare - Rare aircraft commands")
        print("  • !help airports - Airport management") 
        print("  • !help search - Mission search")
        print("  • !help system - System status")
        print("  • !help examples - Usage examples")
    else:
        print("\n❌ Help system deployment failed!")
        
    return success

if __name__ == "__main__":
    deploy_help_update()