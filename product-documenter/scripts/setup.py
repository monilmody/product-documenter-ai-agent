import subprocess
import sys

def install_packages():
    """Install required packages"""
    packages = [
        'flask',
        'requests', 
        'python-dotenv',
        'openai'
    ]
    
    print("Installing required packages...")
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} already installed")
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed")

def create_files():
    """Create necessary files"""
    files = {
        'activity_tracker.py': '''# Your activity_tracker.py content here''',
        'learning_system.py': '''# Your learning_system.py content here''',
        '.env': '''OPENAI_API_KEY=your_key_here\nOPENAI_MODEL=gpt-3.5-turbo'''
    }
    
    for filename, content in files.items():
        try:
            with open(filename, 'r') as f:
                print(f"✅ {filename} already exists")
        except FileNotFoundError:
            print(f"📄 Creating {filename}...")
            with open(filename, 'w') as f:
                f.write(content)

if __name__ == "__main__":
    install_packages()
    create_files()
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your OpenAI API key")
    print("2. Run: python api_server.py")
    print("3. Open: http://localhost:8000")