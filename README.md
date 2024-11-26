# 폴더 잠금 프로그램

Windows 환경에서 특정 폴더에 대한 접근을 제한하고 비밀번호로 보호하는 프로그램입니다.

## 기술적 작동 원리

### 1. 폴더 잠금 메커니즘

#### 1.1 권한 획득 프로세스
1. **관리자 권한 확인**
   - `ctypes.windll.shell32.IsUserAnAdmin()`을 사용하여 관리자 권한 검증
   - 관리자 권한이 없을 경우 자동으로 권한 상승 요청

2. **소유권 획득**
   - Windows `takeown` 명령어를 사용하여 대상 폴더의 소유권 획득
   - `/f` 플래그로 대상 지정, `/r`로 하위 폴더 포함, `/d y`로 자동 승인
   ```cmd
   takeown /f [folder_path] /r /d y
   ```

3. **권한 초기화 및 재설정**
   - `icacls` 명령어를 사용하여 기존 권한 초기화
   - SYSTEM 계정에 전체 권한 부여
   - 현재 사용자 및 Administrators 그룹의 접근 권한 제거
   ```cmd
   icacls [folder_path] /reset /t /c /l
   icacls [folder_path] /grant SYSTEM:(F) /t /c /l
   icacls [folder_path] /deny [USERNAME]:(F) /t /c /l
   icacls [folder_path] /deny Administrators:(F) /t /c /l
   ```

#### 1.2 보안 구현
1. **Windows 보안 API 활용**
   - `win32security`, `win32api`, `win32con` 라이브러리 사용
   - 파일 시스템 수준의 접근 제어 구현

2. **폴더 속성 관리**
   - `win32api.SetFileAttributes`로 폴더 숨김 속성 설정
   - `FILE_ATTRIBUTE_HIDDEN` 플래그 사용

### 2. 잠금 해제 메커니즘

#### 2.1 권한 복구 프로세스
1. **소유권 재획득**
   - `takeown` 명령어로 폴더 소유권 획득
   
2. **권한 재설정**
   - `icacls` 명령어로 원래 사용자 권한 복구
   - 현재 사용자와 Administrators 그룹에 전체 권한 부여
   ```cmd
   icacls [folder_path] /grant [USERNAME]:(F) /t /c /l
   icacls [folder_path] /grant Administrators:(F) /t /c /l
   ```

### 3. 데이터 저장 및 관리

#### 3.1 설정 저장
- 모든 설정 파일은 사용자의 홈 디렉토리에 숨김 파일로 저장됨
  - `~/.folder_locker_config.json`: 잠긴 폴더 목록과 암호화된 비밀번호 저장
  - `~/.folder_locker_key`: 비밀번호 암호화/복호화에 사용되는 키 저장
- 비밀번호는 암호화되어 저장되므로 파일을 직접 열어봐도 원본 비밀번호를 알 수 없음
- 설정 파일이 홈 디렉토리에 저장되어 프로그램을 어디서 실행하더라도 같은 설정 사용 가능
- JSON 형식으로 잠긴 폴더 목록 저장
- 파일 경로와 관련 메타데이터 유지

#### 3.2 오류 처리
- 각 명령어 실행 단계별 예외 처리
- 실패 시 자동 롤백 메커니즘 구현
- 상세한 오류 로깅 및 사용자 피드백 제공

## 주요 기능

- 폴더 잠금/잠금 해제
- 비밀번호 기반 보안
- GUI 인터페이스
- 암호화된 설정 저장
- Windows 시스템 권한 관리

## 시스템 요구사항

- Windows 운영체제
- Python 3.6 이상
- 관리자 권한
- 필수 Python 패키지:
  - pywin32
  - tkinter (Python 기본 패키지)

## 보안 고려사항

1. **권한 관리**
   - 관리자 권한으로만 실행 가능
   - SYSTEM 계정만 폴더 접근 가능하도록 설정
   - 모든 사용자(관리자 포함)의 직접 접근 차단

2. **제한사항**
   - 시스템 폴더나 중요 Windows 폴더는 잠글 수 없음
   - 실행 중인 프로세스가 사용 중인 폴더는 잠금 실패 가능

3. **복구 메커니즘**
   - 잠금 실패 시 자동 롤백
   - 권한 복구 기능 내장

## 주의사항

1. 프로그램은 반드시 관리자 권한으로 실행해야 합니다.
2. 시스템 폴더나 중요 Windows 폴더는 잠그지 마십시오.
3. 잠금 해제 시 사용할 비밀번호를 반드시 기억해두세요.
4. 폴더 잠금 전에 중요 데이터는 백업을 권장합니다.

cryptography==41.0.7
pywin32==306
tkinter  # Python 기본 패키지
pyinstaller==6.3.0  # EXE 빌드용## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 프로그램 실행:
```bash
python folder_locker.py
```

## 사용 방법

1. "폴더 잠금" 버튼을 클릭하여 잠글 폴더를 선택하고 비밀번호를 설정합니다.
2. "폴더 잠금 해제" 버튼을 클릭하여 잠긴 폴더를 선택하고 비밀번호를 입력하여 잠금을 해제합니다.
3. "잠긴 폴더 목록" 버튼을 클릭하여 현재 잠긴 폴더들의 목록을 확인할 수 있습니다.
