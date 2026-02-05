#!/usr/bin/env python3
"""
FFmpeg Installation and Validation Utility for RASO Platform

This utility handles FFmpeg installation, validation, and provides system-specific
installation guidance for production video generation.
"""

import os
import sys
import subprocess
import platform
import shutil
import zipfile
import requests
from pathlib import Path
from typing import Tuple, Optional


class FFmpegInstaller:
    """Handles FFmpeg installation and validation."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.ffmpeg_path = None
        self.ffprobe_path = None
    
    def check_ffmpeg_availability(self) -> Tuple[bool, Optional[str]]:
        """
        Check if FFmpeg is available on the system.
        
        Returns:
            Tuple of (is_available, path_to_ffmpeg)
        """
        # Try to find ffmpeg in PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            self.ffmpeg_path = ffmpeg_path
            self.ffprobe_path = shutil.which("ffprobe")
            return True, ffmpeg_path
        
        # Try common installation locations
        common_paths = self._get_common_ffmpeg_paths()
        
        for path in common_paths:
            ffmpeg_exe = path / "ffmpeg.exe" if self.system == "windows" else path / "ffmpeg"
            if ffmpeg_exe.exists():
                self.ffmpeg_path = str(ffmpeg_exe)
                ffprobe_exe = path / "ffprobe.exe" if self.system == "windows" else path / "ffprobe"
                if ffprobe_exe.exists():
                    self.ffprobe_path = str(ffprobe_exe)
                return True, str(ffmpeg_exe)
        
        return False, None
    
    def _get_common_ffmpeg_paths(self) -> list:
        """Get common FFmpeg installation paths for different systems."""
        if self.system == "windows":
            return [
                Path("C:/ffmpeg/bin"),
                Path("C:/Program Files/ffmpeg/bin"),
                Path("C:/Program Files (x86)/ffmpeg/bin"),
                Path(os.path.expanduser("~/AppData/Local/ffmpeg/bin")),
                Path("./ffmpeg/bin"),  # Local installation
            ]
        elif self.system == "darwin":  # macOS
            return [
                Path("/usr/local/bin"),
                Path("/opt/homebrew/bin"),
                Path("/usr/bin"),
            ]
        else:  # Linux
            return [
                Path("/usr/bin"),
                Path("/usr/local/bin"),
                Path("/snap/bin"),
            ]
    
    def validate_ffmpeg_installation(self) -> Tuple[bool, dict]:
        """
        Validate FFmpeg installation and get version information.
        
        Returns:
            Tuple of (is_valid, info_dict)
        """
        if not self.ffmpeg_path:
            available, path = self.check_ffmpeg_availability()
            if not available:
                return False, {"error": "FFmpeg not found"}
        
        try:
            # Get FFmpeg version
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, {"error": f"FFmpeg execution failed: {result.stderr}"}
            
            # Parse version information
            version_info = self._parse_ffmpeg_version(result.stdout)
            
            # Check for required codecs
            codec_check = self._check_required_codecs()
            
            info = {
                "version": version_info,
                "path": self.ffmpeg_path,
                "ffprobe_path": self.ffprobe_path,
                "codecs": codec_check,
                "valid": True
            }
            
            return True, info
            
        except subprocess.TimeoutExpired:
            return False, {"error": "FFmpeg execution timed out"}
        except Exception as e:
            return False, {"error": f"FFmpeg validation failed: {str(e)}"}
    
    def _parse_ffmpeg_version(self, version_output: str) -> dict:
        """Parse FFmpeg version information."""
        lines = version_output.split('\n')
        version_line = lines[0] if lines else ""
        
        # Extract version number
        version = "unknown"
        if "ffmpeg version" in version_line:
            parts = version_line.split()
            if len(parts) >= 3:
                version = parts[2]
        
        return {
            "version": version,
            "full_output": version_output[:500]  # Truncate for brevity
        }
    
    def _check_required_codecs(self) -> dict:
        """Check if required codecs are available."""
        required_codecs = ["libx264", "aac", "mp4"]
        codec_status = {}
        
        try:
            # Check encoders
            result = subprocess.run(
                [self.ffmpeg_path, "-encoders"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            encoders_output = result.stdout
            
            codec_status["libx264"] = "libx264" in encoders_output
            codec_status["aac"] = "aac" in encoders_output
            
            # Check formats
            result = subprocess.run(
                [self.ffmpeg_path, "-formats"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            formats_output = result.stdout
            codec_status["mp4"] = "mp4" in formats_output
            
        except Exception as e:
            codec_status["error"] = str(e)
        
        return codec_status
    
    def install_ffmpeg_windows(self) -> Tuple[bool, str]:
        """
        Install FFmpeg on Windows by downloading and extracting.
        
        Returns:
            Tuple of (success, message)
        """
        if self.system != "windows":
            return False, "This method is only for Windows"
        
        try:
            # Create local ffmpeg directory
            ffmpeg_dir = Path("./ffmpeg")
            ffmpeg_dir.mkdir(exist_ok=True)
            
            # Download FFmpeg (using a stable release)
            download_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            zip_path = ffmpeg_dir / "ffmpeg.zip"
            
            print("Downloading FFmpeg...")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("Extracting FFmpeg...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(ffmpeg_dir)
            
            # Find the extracted directory and move binaries
            extracted_dirs = [d for d in ffmpeg_dir.iterdir() if d.is_dir() and d.name.startswith("ffmpeg")]
            if not extracted_dirs:
                return False, "Could not find extracted FFmpeg directory"
            
            extracted_dir = extracted_dirs[0]
            bin_dir = extracted_dir / "bin"
            
            if not bin_dir.exists():
                return False, "Could not find FFmpeg bin directory"
            
            # Move binaries to ffmpeg/bin
            target_bin_dir = ffmpeg_dir / "bin"
            if target_bin_dir.exists():
                shutil.rmtree(target_bin_dir)
            
            shutil.move(str(bin_dir), str(target_bin_dir))
            
            # Clean up
            zip_path.unlink()
            shutil.rmtree(extracted_dir)
            
            # Update paths
            self.ffmpeg_path = str(target_bin_dir / "ffmpeg.exe")
            self.ffprobe_path = str(target_bin_dir / "ffprobe.exe")
            
            # Validate installation
            is_valid, info = self.validate_ffmpeg_installation()
            if is_valid:
                return True, f"FFmpeg installed successfully at {self.ffmpeg_path}"
            else:
                return False, f"FFmpeg installation validation failed: {info.get('error', 'Unknown error')}"
                
        except Exception as e:
            return False, f"FFmpeg installation failed: {str(e)}"
    
    def get_installation_instructions(self) -> str:
        """Get system-specific installation instructions."""
        if self.system == "windows":
            return """
Windows FFmpeg Installation Instructions:

Option 1 - Using winget (Recommended):
  winget install Gyan.FFmpeg

Option 2 - Using Chocolatey:
  choco install ffmpeg

Option 3 - Manual Installation:
  1. Download from: https://www.gyan.dev/ffmpeg/builds/
  2. Extract to C:\\ffmpeg\\
  3. Add C:\\ffmpeg\\bin to your PATH environment variable

Option 4 - Automatic (run this script):
  python utils/ffmpeg_installer.py --install
"""
        elif self.system == "darwin":
            return """
macOS FFmpeg Installation Instructions:

Option 1 - Using Homebrew (Recommended):
  brew install ffmpeg

Option 2 - Using MacPorts:
  sudo port install ffmpeg

Option 3 - Manual Installation:
  Download from: https://evermeet.cx/ffmpeg/
"""
        else:
            return """
Linux FFmpeg Installation Instructions:

Ubuntu/Debian:
  sudo apt update
  sudo apt install ffmpeg

CentOS/RHEL/Fedora:
  sudo dnf install ffmpeg
  # or: sudo yum install ffmpeg

Arch Linux:
  sudo pacman -S ffmpeg

From source:
  https://ffmpeg.org/download.html#build-linux
"""


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FFmpeg Installation and Validation Utility")
    parser.add_argument("--check", action="store_true", help="Check FFmpeg availability")
    parser.add_argument("--validate", action="store_true", help="Validate FFmpeg installation")
    parser.add_argument("--install", action="store_true", help="Install FFmpeg (Windows only)")
    parser.add_argument("--instructions", action="store_true", help="Show installation instructions")
    
    args = parser.parse_args()
    
    installer = FFmpegInstaller()
    
    if args.check or not any([args.validate, args.install, args.instructions]):
        available, path = installer.check_ffmpeg_availability()
        if available:
            print(f"✅ FFmpeg found at: {path}")
        else:
            print("❌ FFmpeg not found")
            print("\nInstallation instructions:")
            print(installer.get_installation_instructions())
    
    if args.validate:
        is_valid, info = installer.validate_ffmpeg_installation()
        if is_valid:
            print("✅ FFmpeg validation successful")
            print(f"Version: {info['version']['version']}")
            print(f"Path: {info['path']}")
            print(f"Codecs: {info['codecs']}")
        else:
            print(f"❌ FFmpeg validation failed: {info.get('error', 'Unknown error')}")
    
    if args.install:
        if installer.system == "windows":
            success, message = installer.install_ffmpeg_windows()
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
        else:
            print("❌ Automatic installation is only supported on Windows")
            print("\nInstallation instructions:")
            print(installer.get_installation_instructions())
    
    if args.instructions:
        print(installer.get_installation_instructions())


if __name__ == "__main__":
    main()