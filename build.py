import subprocess
import os
import sys
import shutil

def build_frontend():
    """Build the frontend for production"""
    print("Building frontend...")
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend'))
    
    # Install dependencies
    subprocess.run(['npm', 'install'], check=True)
    
    # Build for production
    subprocess.run(['npm', 'run', 'build'], check=True)
    
    # Copy build to backend static directory
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'static')
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'build')
    
    # Create static directory if it doesn't exist
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # Copy files
    for item in os.listdir(build_dir):
        src = os.path.join(build_dir, item)
        dst = os.path.join(static_dir, item)
        
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    
    print("Frontend build complete")

def main():
    """Main entry point"""
    # Build frontend
    build_frontend()
    
    print("\n" + "="*50)
    print("Build complete!")
    print("You can now run the system with: python start.py")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()