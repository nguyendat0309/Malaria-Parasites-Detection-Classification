"""
Setup script for Blood Cell Analysis Application.
Downloads dependencies and model weights.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def get_base_dir():
    """Get the base directory of the application."""
    if getattr(sys, 'frozen', False):
        # Running as compiled
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def print_header():
    """Print setup header."""
    print("=" * 60)
    print("  🔬 Blood Cell Analysis - Setup Wizard")
    print("=" * 60)
    print()


def create_directories():
    """Create necessary directories."""
    base = get_base_dir()
    dirs = [
        os.path.join(base, "Data", "Input"),
        os.path.join(base, "Data", "Output"),
        os.path.join(base, "Weights", "Yolo"),
        os.path.join(base, "Weights", "ConvNext", "1Phase"),
        os.path.join(base, "Weights", "ConvNext", "2Phase"),
    ]
    
    print("📁 Creating directories...")
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"   ✓ Created: {d}")
    print()


def install_requirements():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    print("   This may take a few minutes...")
    print()
    
    base = get_base_dir()
    req_file = os.path.join(base, "requirements.txt")
    
    if not os.path.exists(req_file):
        print("   ⚠️ requirements.txt not found!")
        return False
    
    try:
        # Upgrade pip first
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], stdout=subprocess.DEVNULL)
        
        # Install requirements
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", req_file
        ])
        print()
        print("   ✓ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to install dependencies: {e}")
        print("   Please try running manually:")
        print(f"   pip install -r {req_file}")
        return False


def check_weights():
    """Check if model weights are present."""
    base = get_base_dir()
    weights = {
        "YOLO": os.path.join(base, "Weights", "Yolo", "yolo11l.pt"),
        "1-Phase Classifier": os.path.join(base, "Weights", "ConvNext", "1Phase", "1Phase.pth"),
        "2-Phase Stage 1": os.path.join(base, "Weights", "ConvNext", "2Phase", "Phase1.pth"),
        "2-Phase Stage 2": os.path.join(base, "Weights", "ConvNext", "2Phase", "Phase2.pth"),
    }
    
    print("🔍 Checking model weights...")
    all_present = True
    
    for name, path in weights.items():
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"   ✓ {name}: Found ({size_mb:.1f} MB)")
        else:
            print(f"   ❌ {name}: Missing")
            all_present = False
    
    print()
    return all_present


def download_weights():
    """Download model weights from Google Drive."""
    print("📥 Attempting to download model weights...")
    print()
    
    base = get_base_dir()
    weights_dir = os.path.join(base, "Weights")
    
    # Google Drive folder ID (from the shared link)
    folder_url = "https://drive.google.com/drive/folders/1tMoGcmDaeWYd7ZKRwL7prrVXOGkxaHLX"
    
    try:
        import gdown
        
        print(f"   Downloading from: {folder_url}")
        print("   This may take several minutes depending on your connection...")
        print()
        
        # Download folder
        gdown.download_folder(
            url=folder_url,
            output=weights_dir,
            quiet=False,
            use_cookies=False
        )
        
        print()
        print("   ✓ Download complete!")
        return True
        
    except ImportError:
        print("   ⚠️ gdown not installed. Installing now...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
            import gdown
            gdown.download_folder(url=folder_url, output=weights_dir, quiet=False)
            return True
        except Exception as e:
            print(f"   ❌ Failed to install gdown: {e}")
            
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
    
    print()
    print("   Please download weights manually from:")
    print(f"   {folder_url}")
    print()
    print("   And place them in the following structure:")
    print("   Weights/")
    print("   ├── Yolo/")
    print("   │   └── yolo11l.pt")
    print("   └── ConvNext/")
    print("       ├── 1Phase/")
    print("       │   └── 1Phase.pth")
    print("       └── 2Phase/")
    print("           ├── Phase1.pth")
    print("           └── Phase2.pth")
    
    return False


def verify_installation():
    """Verify that all components are working."""
    print("🔧 Verifying installation...")
    
    errors = []
    
    # Check PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
        print("   ✓ PyQt6: OK")
    except ImportError as e:
        print(f"   ❌ PyQt6: {e}")
        errors.append("PyQt6")
    
    # Check PyTorch
    try:
        import torch
        cuda = "CUDA available" if torch.cuda.is_available() else "CPU only"
        print(f"   ✓ PyTorch: OK ({cuda})")
    except ImportError as e:
        print(f"   ❌ PyTorch: {e}")
        errors.append("PyTorch")
    
    # Check ultralytics
    try:
        from ultralytics import YOLO
        print("   ✓ Ultralytics (YOLO): OK")
    except ImportError as e:
        print(f"   ❌ Ultralytics: {e}")
        errors.append("Ultralytics")
    
    # Check timm
    try:
        import timm
        print("   ✓ timm: OK")
    except ImportError as e:
        print(f"   ❌ timm: {e}")
        errors.append("timm")
    
    print()
    
    if errors:
        print(f"   ⚠️ Missing components: {', '.join(errors)}")
        return False
    
    print("   ✓ All components verified!")
    return True


def main():
    """Main setup routine."""
    print_header()
    
    # Step 1: Create directories
    create_directories()
    
    # Step 2: Install requirements
    print("-" * 60)
    if not install_requirements():
        print("\n⚠️ Some dependencies may not be installed.")
        print("   The application may run with limited functionality.\n")
    
    # Step 3: Check weights
    print("-" * 60)
    weights_ok = check_weights()
    
    # Step 4: Download weights if missing
    if not weights_ok:
        print("-" * 60)
        response = input("Would you like to download missing weights? (y/n): ").strip().lower()
        if response == 'y':
            download_weights()
            check_weights()
    
    # Step 5: Verify installation
    print("-" * 60)
    verify_installation()
    
    # Done
    print("=" * 60)
    print("  Setup Complete!")
    print("=" * 60)
    print()
    print("  To run the application:")
    print("    python main.py")
    print("  Or double-click: run_app.bat")
    print()
    
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
