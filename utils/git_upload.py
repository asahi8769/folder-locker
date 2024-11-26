import os
import requests
import subprocess
import json
from dotenv import load_dotenv
from datetime import datetime

def check_repo_exists(token, repo_name):
    """GitHub API를 사용하여 레포지토리 존재 여부 확인"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(
        f"https://api.github.com/user/repos",
        headers=headers
    )
    
    if response.status_code == 200:
        repos = response.json()
        return any(repo["name"] == repo_name for repo in repos)
    else:
        raise Exception("Failed to check repository existence")

def create_github_repo(token, repo_name, description):
    """GitHub API를 사용하여 새 레포지토리 생성"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": repo_name,
        "description": description,
        "private": False,
        "auto_init": False
    }
    
    response = requests.post(
        "https://api.github.com/user/repos",
        headers=headers,
        data=json.dumps(data)
    )
    
    if response.status_code == 201:
        return response.json()["clone_url"]
    else:
        raise Exception(f"Repository creation failed: {response.json()['message']}")

def get_repo_url(token, repo_name):
    """GitHub API를 사용하여 레포지토리 URL 가져오기"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    user_response = requests.get(
        "https://api.github.com/user",
        headers=headers
    )
    
    if user_response.status_code != 200:
        raise Exception("Failed to get user information")
        
    username = user_response.json()["login"]

    
    response = requests.get(
        f"https://api.github.com/repos/{username}/{repo_name}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()["clone_url"]
    else:
        raise Exception("Failed to get repository URL")

def upload_to_github():
    """코드베이스를 GitHub에 업로드"""
    try:
        load_dotenv()
        token = os.getenv('GITHUB_TOKEN')
        default_repo_name = os.getenv('PROJECT_NAME')
        
        if not token:
            raise Exception("GitHub 토큰을 찾을 수 없습니다. .env 파일을 확인해주세요.")
            
        repo_name = input(f"레포지토리 이름을 입력해주시겠습니까? (기본값: {default_repo_name}): ").strip()
        if not repo_name:
            repo_name = default_repo_name

        # 프로젝트 루트 디렉토리로 이동
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(project_root)
        
        # Git 초기화
        if not os.path.exists(".git"):
            subprocess.run(["git", "init"], check=True)
        
        # 레포지토리 존재 여부 확인
        repo_exists = check_repo_exists(token, repo_name)
        
        if repo_exists:
            print(f"레포지토리 '{repo_name}'이(가) 이미 존재합니다.")
            choice = input("기존 레포지토리에 덮어쓰시겠습니까? (y/N): ").strip().lower()
            if choice != 'y':
                return False
            repo_url = get_repo_url(token, repo_name)
        else:
            # 새 레포지토리 생성
            repo_url = create_github_repo(token, repo_name)

        # 현재 시간을 포함한 커밋 메시지 생성
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        commit_message = f"Upload: {timestamp}"
        
        # Git 커밋 및 푸시
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "branch", "-M", "master"], check=True)
        
        # remote 확인 및 설정
        try:
            subprocess.run(["git", "remote", "remove", "origin"], check=False)
        except:
            pass
        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
        
        # 강제 푸시 (기존 레포지토리인 경우)
        if repo_exists:
            subprocess.run(["git", "push", "-f", "-u", "origin", "master"], check=True)
        else:
            subprocess.run(["git", "push", "-u", "origin", "master"], check=True)
        
        print(f"\n성공적으로 업로드되었습니다!")
        print(f"레포지토리 URL: {repo_url}")
        return True
        
    except Exception as e:
        print(f"업로드 실패: {str(e)}")
        return False

if __name__ == "__main__":
    upload_to_github()