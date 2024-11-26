import os
import sys
import tkinter as tk
from tkinter import messagebox, filedialog
import win32con
import win32file
import win32security
import win32api
import ntsecuritycon as con
from cryptography.fernet import Fernet
import json
from pathlib import Path
import ctypes

class FolderLocker:
    def __init__(self):
        # 관리자 권한 확인 및 요청
        if not self.check_admin_rights():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
            
        self.window = tk.Tk()
        self.window.title("폴더 잠금 프로그램")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        
        # 설정 파일 경로
        self.config_file = Path.home() / ".folder_locker_config.json"
        self.key_file = Path.home() / ".folder_locker_key"
        
        # 암호화 키 생성 또는 로드
        self.load_or_create_key()
        
        # 저장된 설정 로드
        self.locked_folders = self.load_config()
        
        # 이전 형식의 데이터를 새로운 형식으로 자동 변환
        if self.locked_folders and isinstance(self.locked_folders, list):
            if all(isinstance(item, str) for item in self.locked_folders):
                self.locked_folders = [{
                    'path': path,
                    'password': self.fernet.encrypt(b'default_password').decode()  # 임시 비밀번호
                } for path in self.locked_folders]
                # 변환된 데이터 저장
                self.save_config()
        
        self.create_widgets()
        
    def check_admin_rights(self):
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    def load_or_create_key(self):
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        else:
            with open(self.key_file, 'rb') as f:
                key = f.read()
        self.fernet = Fernet(key)
        
    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    # 데이터가 리스트가 아닌 경우 빈 리스트로 초기화
                    if not isinstance(data, list):
                        return []
                    return data
            except:
                return []
        return []
        
    def save_config(self):
        # 리스트가 아닌 경우 빈 리스트로 초기화
        if not isinstance(self.locked_folders, list):
            self.locked_folders = []
            
        with open(self.config_file, 'w') as f:
            json.dump(self.locked_folders, f)
            
    def create_widgets(self):
        # 메인 프레임
        main_frame = tk.Frame(self.window, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        # 버튼들
        tk.Button(main_frame, text="폴더 잠금", command=self.lock_folder,
                 width=20, height=2).pack(pady=10)
        tk.Button(main_frame, text="폴더 잠금 해제", command=self.unlock_folder,
                 width=20, height=2).pack(pady=10)
        tk.Button(main_frame, text="잠긴 폴더 목록", command=self.show_locked_folders,
                 width=20, height=2).pack(pady=10)
        tk.Button(main_frame, text="목록 초기화", command=self.reset_locked_folders,
                 width=20, height=2).pack(pady=10)
                 
    def lock_folder(self):
        try:
            # 현재 사용자의 SID 얻기
            current_user = win32api.GetUserName()
            user_sid = win32security.LookupAccountName(None, current_user)[0]
            
            # 시스템 SID 얻기
            system_sid = win32security.LookupAccountName(None, "SYSTEM")[0]
            administrators_sid = win32security.LookupAccountName(None, "Administrators")[0]
            
            # 폴더 선택 전에 임시로 모든 권한 획득
            folder_path = filedialog.askdirectory(title="잠글 폴더를 선택하세요")
            if not folder_path:
                return
                
            # 이미 잠긴 폴더인지 확인
            if any(folder.get('path') == folder_path for folder in self.locked_folders):
                messagebox.showerror("오류", "이미 잠긴 폴더입니다.")
                return
                
            # 선택한 폴더가 시스템 폴더인지 확인
            system_folders = [os.environ['SYSTEMROOT'], os.environ['PROGRAMFILES'], os.environ['PROGRAMFILES(X86)']]
            if any(folder_path.lower().startswith(sys_folder.lower()) for sys_folder in system_folders):
                messagebox.showerror("오류", "시스템 폴더는 잠글 수 없습니다.")
                return
                
            # 비밀번호 설정 창
            password_window = tk.Toplevel(self.window)
            password_window.title("비밀번호 설정")
            password_window.geometry("300x150")
            
            tk.Label(password_window, text="비밀번호 설정:").pack(pady=10)
            password_entry = tk.Entry(password_window, show="*")
            password_entry.pack(pady=5)
            
            def confirm_password():
                password = password_entry.get()
                if len(password) < 4:
                    messagebox.showerror("오류", "비밀번호는 최소 4자 이상이어야 합니다.")
                    return
                    
                try:
                    # 비밀번호 암호화
                    encrypted_password = self.fernet.encrypt(password.encode()).decode()
                    
                    # 폴더 권한 제한
                    self.restrict_folder_access(folder_path)
                    
                    # 설정 저장
                    self.locked_folders.append({
                        'path': folder_path,
                        'password': encrypted_password
                    })
                    self.save_config()
                    
                    messagebox.showinfo("성공", "폴더가 성공적으로 잠겼습니다!")
                    password_window.destroy()
                    self.window.quit()  # 메인 창 종료
                    
                except Exception as e:
                    messagebox.showerror("오류", f"폴더를 잠그는 중 오류가 발생했습니다: {str(e)}")
                    # 오류 발생 시 권한 복구 시도
                    try:
                        self.restore_folder_access(folder_path)
                    except:
                        pass
                    
            tk.Button(password_window, text="확인", command=confirm_password).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("오류", f"작업 중 오류가 발생했습니다: {str(e)}")
            
    def unlock_folder(self):
        folder_path = filedialog.askdirectory(title="잠금 해제할 폴더를 선택하세요")
        
        # 잠긴 폴더 찾기
        folder_info = None
        for folder in self.locked_folders:
            if isinstance(folder, dict) and folder.get('path') == folder_path:
                folder_info = folder
                break
                
        if not folder_info:
            messagebox.showerror("오류", "잠긴 폴더가 아니거나 선택된 폴더가 없습니다.")
            return
            
        # 비밀번호 확인 창
        password_window = tk.Toplevel(self.window)
        password_window.title("비밀번호 확인")
        password_window.geometry("300x150")
        
        tk.Label(password_window, text="비밀번호 입력:").pack(pady=10)
        password_entry = tk.Entry(password_window, show="*")
        password_entry.pack(pady=5)
        
        def confirm_password():
            try:
                password = password_entry.get()
                
                # 저장된 비밀번호 복호화
                stored_password = self.fernet.decrypt(folder_info['password'].encode()).decode()
                
                if password == stored_password:
                    try:
                        # 폴더 잠금 해제
                        self.restore_folder_access(folder_path)
                        
                        # 목록에서 제거
                        self.locked_folders.remove(folder_info)
                        self.save_config()
                        
                        messagebox.showinfo("성공", "폴더 잠금이 해제되었습니다!")
                        password_window.destroy()
                        self.window.quit()  # 메인 창 종료
                        
                    except Exception as e:
                        messagebox.showerror("오류", f"폴더 잠금 해제 중 오류가 발생했습니다: {str(e)}")
                else:
                    messagebox.showerror("오류", "비밀번호가 일치하지 않습니다.")
                    
            except Exception as e:
                messagebox.showerror("오류", f"비밀번호 확인 중 오류가 발생했습니다: {str(e)}")
                
        tk.Button(password_window, text="확인", command=confirm_password).pack(pady=10)
        
    def show_locked_folders(self):
        if not self.locked_folders:
            messagebox.showinfo("알림", "잠긴 폴더가 없습니다.")
            return
            
        # 잠긴 폴더 목록 창
        list_window = tk.Toplevel(self.window)
        list_window.title("잠긴 폴더 목록")
        list_window.geometry("400x300")
        
        tk.Label(list_window, text="현재 잠긴 폴더 목록:", pady=10).pack()
        
        for folder in self.locked_folders:
            tk.Label(list_window, text=folder.get('path'), wraplength=350).pack(pady=5)
            
    def restrict_folder_access(self, folder_path):
        try:
            # 관리자 권한 확인
            if not self.check_admin_rights():
                raise Exception("이 작업을 수행하려면 관리자 권한이 필요합니다. 프로그램을 관리자 권한으로 다시 실행해주세요.")

            # 폴더 경로 정규화 및 검증
            folder_path = os.path.abspath(folder_path)
            if not os.path.exists(folder_path):
                raise Exception(f"폴더를 찾을 수 없습니다: {folder_path}")
            if not os.path.isdir(folder_path):
                raise Exception(f"선택한 경로가 폴더가 아닙니다: {folder_path}")
                
            print(f"폴더 접근 제한 시작: {folder_path}")
            
            # 1. takeown으로 현재 소유권 확보
            import subprocess
            
            print("1. 현재 소유권 확보 중...")
            
            # takeown 명령 실행 (shell=False로 변경하고 경로를 직접 전달)
            result = subprocess.run(
                ['takeown', '/f', folder_path, '/r', '/d', 'y'],
                capture_output=True,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                print(f"takeown 명령 출력: {result.stdout}")
                print(f"takeown 오류 출력: {result.stderr}")
                raise Exception(f"소유권 획득 실패: {error_msg}")
            
            # 2. icacls로 권한 초기화
            print("2. 권한 초기화 중...")
            result = subprocess.run(
                ['icacls', folder_path, '/reset', '/t', '/c', '/l'],
                capture_output=True,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                raise Exception(f"권한 초기화 실패: {error_msg}")
            
            # 3. SYSTEM 계정에 모든 권한 부여
            print("3. SYSTEM 권한 설정 중...")
            result = subprocess.run(
                ['icacls', folder_path, '/grant', 'SYSTEM:(F)', '/t', '/c', '/l'],
                capture_output=True,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                raise Exception(f"SYSTEM 권한 설정 실패: {error_msg}")
            
            # 4. 현재 사용자와 Administrators의 권한 제거
            print("4. 사용자 권한 제한 중...")
            current_user = os.getenv("USERNAME")
            
            # 현재 사용자 권한 제거
            result = subprocess.run(
                ['icacls', folder_path, '/deny', f'{current_user}:(F)', '/t', '/c', '/l'],
                capture_output=True,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                raise Exception(f"사용자 권한 제한 실패: {error_msg}")
            
            # Administrators 권한 제거
            result = subprocess.run(
                ['icacls', folder_path, '/deny', 'Administrators:(F)', '/t', '/c', '/l'],
                capture_output=True,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                raise Exception(f"관리자 권한 제한 실패: {error_msg}")
            
            print("5. 폴더 숨김 처리 중...")
            try:
                # 현재 속성 가져오기
                current_attributes = win32api.GetFileAttributes(folder_path)
                # 숨김 속성 추가
                new_attributes = current_attributes | win32con.FILE_ATTRIBUTE_HIDDEN
                # 새로운 속성 설정
                win32api.SetFileAttributes(folder_path, new_attributes)
                print("폴더 숨김 처리 완료")
            except Exception as attr_error:
                print(f"폴더 숨김 처리 실패 (무시됨): {str(attr_error)}")
                print("참고: 폴더 숨김 실패는 보안에 영향을 주지 않습니다.")
            
            print("폴더 잠금 완료")
            
        except Exception as e:
            # 오류 발생 시 권한 복구 시도
            print("오류 발생, 권한 복구 시도 중...")
            try:
                # 권한 복구
                subprocess.run([
                    'icacls',
                    folder_path,
                    '/grant', f'{os.getenv("USERNAME")}:(F)',
                    '/t', '/c', '/l'
                ], capture_output=True)
                
                subprocess.run([
                    'icacls',
                    folder_path,
                    '/grant', 'Administrators:(F)',
                    '/t', '/c', '/l'
                ], capture_output=True)
            except:
                pass
            
            raise Exception(f"폴더 접근 제한 중 오류 발생: {str(e)}")
            
    def restore_folder_access(self, folder_path):
        try:
            print(f"폴더 권한 복구 시도: {folder_path}")
            
            # takeown 명령으로 소유권 획득
            import subprocess
            
            print("1. 폴더 소유권 획득 중...")
            subprocess.run([
                'takeown',
                '/f', folder_path,
                '/r', '/d', 'y'
            ], capture_output=True)
            
            print("2. icacls 명령으로 권한 재설정 중...")
            # 현재 사용자에게 모든 권한 부여
            subprocess.run([
                'icacls',
                folder_path,
                '/grant', f'{os.getenv("USERNAME")}:(F)',
                '/t', '/c', '/l'
            ], capture_output=True)
            
            # Administrators 그룹에 모든 권한 부여
            subprocess.run([
                'icacls',
                folder_path,
                '/grant', 'Administrators:(F)',
                '/t', '/c', '/l'
            ], capture_output=True)
            
            print("3. Windows API로 추가 권한 설정 중...")
            # 현재 사용자의 SID 얻기
            current_user = win32api.GetUserName()
            user_sid = win32security.LookupAccountName(None, current_user)[0]
            
            # Administrators 그룹의 SID 얻기
            administrators_sid = win32security.LookupAccountName(None, "Administrators")[0]

            # 새로운 보안 설명자 생성
            sd = win32security.SECURITY_DESCRIPTOR()
            
            # DACL 생성
            dacl = win32security.ACL()
            
            # 모든 계정에 완전한 권한 부여
            for sid in [user_sid, administrators_sid]:
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.GENERIC_ALL | con.FILE_ALL_ACCESS,
                    sid
                )
            
            # 보안 설명자에 DACL 설정
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            
            # 소유자를 현재 사용자로 변경
            sd.SetSecurityDescriptorOwner(user_sid, 0)
            
            # 4. 폴더와 파일 속성 정상화
            print("4. 파일 속성 정상화 중...")
            try:
                # 폴더 속성 초기화
                win32api.SetFileAttributes(folder_path, win32con.FILE_ATTRIBUTE_NORMAL)
                
                # 모든 하위 항목 처리
                for root, dirs, files in os.walk(folder_path):
                    # 각 폴더 처리
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            win32api.SetFileAttributes(dir_path, win32con.FILE_ATTRIBUTE_NORMAL)
                        except:
                            pass
                    
                    # 각 파일 처리
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        try:
                            win32api.SetFileAttributes(file_path, win32con.FILE_ATTRIBUTE_NORMAL)
                        except:
                            pass
            except Exception as attr_error:
                print(f"속성 변경 중 오류 발생: {str(attr_error)}")
            
            print("권한 복구 완료")
            
        except Exception as e:
            raise Exception(f"폴더 권한 복구 중 오류 발생: {str(e)}")
            
    def master_unlock(self, target_folder):
        try:
            print(f"마스터 키로 폴더 권한 복구 시도: {target_folder}")
            
            # takeown 명령으로 소유권 획득
            import subprocess
            
            print("1. takeown 명령으로 폴더 소유권 획득 중...")
            subprocess.run([
                'takeown',
                '/f', target_folder,
                '/r', '/d', 'y'
            ], capture_output=True)
            
            print("2. icacls 명령으로 권한 재설정 중...")
            # 현재 사용자에게 모든 권한 부여
            subprocess.run([
                'icacls',
                target_folder,
                '/grant', f'{os.getenv("USERNAME")}:(F)',
                '/t', '/c', '/l'
            ], capture_output=True)
            
            # Administrators 그룹에 모든 권한 부여
            subprocess.run([
                'icacls',
                target_folder,
                '/grant', 'Administrators:(F)',
                '/t', '/c', '/l'
            ], capture_output=True)
            
            print("3. Windows API로 추가 권한 설정 중...")
            # 현재 사용자의 SID 얻기
            current_user = win32api.GetUserName()
            user_sid = win32security.LookupAccountName(None, current_user)[0]
            
            # Administrators 그룹의 SID 얻기
            administrators_sid = win32security.LookupAccountName(None, "Administrators")[0]

            # 새로운 보안 설명자 생성
            sd = win32security.SECURITY_DESCRIPTOR()
            
            # DACL 생성
            dacl = win32security.ACL()
            
            # 현재 사용자에게 모든 권한 부여
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, user_sid)
            
            # Administrators 그룹에 모든 권한 부여
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, administrators_sid)
            
            # SYSTEM 계정에 모든 권한 부여
            system_sid = win32security.LookupAccountName(None, "SYSTEM")[0]
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION, con.FILE_ALL_ACCESS, system_sid)
            
            # 보안 설명자에 DACL 설정
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            
            # 폴더와 모든 하위 항목에 새로운 보안 설정 적용
            for root, dirs, files in os.walk(target_folder):
                try:
                    # 폴더에 보안 설정 적용
                    win32security.SetFileSecurity(
                        root,
                        win32security.DACL_SECURITY_INFORMATION,
                        sd
                    )
                    
                    # 파일들에 보안 설정 적용
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            win32security.SetFileSecurity(
                                file_path,
                                win32security.DACL_SECURITY_INFORMATION,
                                sd
                            )
                        except Exception as file_error:
                            print(f"파일 권한 복구 실패: {file_path} - {str(file_error)}")
                            
                except Exception as dir_error:
                    print(f"폴더 권한 복구 실패: {root} - {str(dir_error)}")
            
            # 숨김 속성 제거
            win32api.SetFileAttributes(target_folder, win32con.FILE_ATTRIBUTE_NORMAL)
            
        except Exception as e:
            print(f"마스터 키 복구 중 오류 발생: {str(e)}")
            return False

    def reset_locked_folders(self):
        try:
            # 확인 대화상자 표시
            if not messagebox.askyesno("확인", "정말로 잠긴 폴더 목록을 초기화하시겠습니까?\n\n주의: 이 작업은 실제 폴더의 잠금을 해제하지 않습니다."):
                return
                
            # 목록 초기화
            self.locked_folders = []
            
            # 설정 파일 업데이트
            self.save_config()
            
            messagebox.showinfo("성공", "잠긴 폴더 목록이 초기화되었습니다.")
            
        except Exception as e:
            messagebox.showerror("오류", f"목록 초기화 중 오류가 발생했습니다: {str(e)}")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = FolderLocker()
    app.run()
