import os
import subprocess
import sys

def build_exe():
    """exe 파일 빌드"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_script = os.path.join(project_root, "folder_locker.py")
    dist_dir = os.path.join(project_root, "dist")
    icon_path = os.path.join(project_root, "ico", "folder_lock.ico")
    
    command = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--uac-admin",
        "--name", "Folder Locker",
        "--clean",
        main_script
    ]
    
    try:
        if not os.path.exists(icon_path):
            from . import icon_converter
            icon_converter.convert_webp_to_ico()
            
        if os.path.exists(icon_path):
            command.insert(-2, f"--icon={icon_path}")
            
        subprocess.run(command, check=True)
        return True
        
    except Exception as e:
        print(f"빌드 실패: {str(e)}")
        return False

if __name__ == "__main__":
    build_exe()