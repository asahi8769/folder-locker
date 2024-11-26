import os
import shutil
import zipfile
from datetime import datetime

def backup_project():
    """프로젝트 전체를 versions 폴더에 압축 백업"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        versions_dir = os.path.join(project_root, 'versions')
        os.makedirs(versions_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.zip'
        backup_path = os.path.join(versions_dir, backup_filename)
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_root):
                if 'versions' in dirs:
                    dirs.remove('versions')
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                if '.git' in dirs:
                    dirs.remove('.git')
                if '.env' in dirs:
                    dirs.remove('.env')
                    
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, project_root)
                    zipf.write(file_path, rel_path)
        
        return True, backup_path
        
    except Exception as e:
        return False, str(e)

if __name__ == '__main__':
    success, result = backup_project()
    if success:
        print(f"백업 완료: {result}")
    else:
        print(f"백업 실패: {result}")