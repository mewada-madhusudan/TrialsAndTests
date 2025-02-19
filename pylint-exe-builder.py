import os
import sys
from typing import List
import shutil
import subprocess
import platform

def create_spec_file(output_dir: str) -> str:
    """Create a PyInstaller spec file for pylint."""
    spec_content = """# -*- mode: python -*-

block_cipher = None

a = Analysis(
    ['pylint_runner.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pylint',
        'astroid',
        'isort',
        'platformdirs',
        'tomlkit',
        'dill',
        'typing_extensions'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='pylint_runner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)
"""
    spec_path = os.path.join(output_dir, 'pylint_runner.spec')
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    return spec_path

def ensure_dependencies() -> None:
    """Ensure all required packages are installed."""
    required_packages = [
        'pyinstaller',
        'pylint',
        'astroid',
        'isort',
        'platformdirs',
        'tomlkit',
        'dill',
        'typing_extensions'
    ]
    
    for package in required_packages:
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {e}")
            sys.exit(1)

def build_executable(spec_path: str, output_dir: str) -> None:
    """Build the executable using PyInstaller."""
    try:
        # Run PyInstaller
        subprocess.run(
            ['pyinstaller', '--clean', spec_path],
            check=True,
            cwd=output_dir
        )
        
        # Move executable to output directory
        dist_dir = os.path.join(output_dir, 'dist')
        exe_name = 'pylint_runner.exe' if platform.system() == 'Windows' else 'pylint_runner'
        exe_path = os.path.join(dist_dir, exe_name)
        
        if os.path.exists(exe_path):
            dest_path = os.path.join(output_dir, exe_name)
            shutil.move(exe_path, dest_path)
            print(f"Executable created successfully: {dest_path}")
        else:
            print("Error: Executable not found in dist directory")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        sys.exit(1)

def cleanup(output_dir: str) -> None:
    """Clean up build artifacts."""
    paths_to_remove = ['build', 'dist', '__pycache__']
    for path in paths_to_remove:
        full_path = os.path.join(output_dir, path)
        if os.path.exists(full_path):
            shutil.rmtree(full_path)

def main():
    """Main function to build the pylint executable."""
    # Get output directory
    output_dir = os.getcwd()
    
    print("Starting pylint executable build process...")
    
    # Ensure we have all required dependencies
    print("Installing required dependencies...")
    ensure_dependencies()
    
    # Create spec file
    print("Creating PyInstaller spec file...")
    spec_path = create_spec_file(output_dir)
    
    # Build the executable
    print("Building executable...")
    build_executable(spec_path, output_dir)
    
    # Cleanup
    print("Cleaning up build files...")
    cleanup(output_dir)
    
    print("Build process completed successfully!")

if __name__ == "__main__":
    main()
