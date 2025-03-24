@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: 관리자 권한 확인 및 요청
NET SESSION >nul 2>&1
if %errorLevel% neq 0 (
    echo 이 스크립트는 관리자 권한이 필요합니다.
    echo 관리자 권한으로 다시 실행합니다...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

echo ===== 폴더 잠금 해제 도구 =====
echo.
echo 이 도구는 폴더 잠금 프로그램으로 잠긴 폴더의 접근 권한을 복구합니다.
echo 비밀번호를 잊어버린 경우 이 도구를 사용하여 폴더에 다시 접근할 수 있습니다.
echo.

:: 폴더 경로 입력 받기
set /p FOLDER_PATH="복구할 폴더의 전체 경로를 입력하세요: "

:: 입력된 경로가 존재하는지 확인
if not exist "%FOLDER_PATH%" (
    echo.
    echo 오류: 입력한 경로가 존재하지 않습니다.
    echo 경로를 확인하고 다시 시도해주세요.
    goto :error
)

:: 입력된 경로가 폴더인지 확인
for %%I in ("%FOLDER_PATH%") do set ATTRIB=%%~aI
if not "%ATTRIB:~0,1%"=="d" (
    echo.
    echo 오류: 입력한 경로가 폴더가 아닙니다.
    echo 폴더 경로를 입력해주세요.
    goto :error
)

echo.
echo 입력한 폴더 경로: %FOLDER_PATH%
echo.
echo 이 폴더의 접근 권한을 복구하시겠습니까?
echo 진행하려면 아무 키나 누르세요. 취소하려면 창을 닫으세요...
pause > nul

echo.
echo 폴더 권한 복구를 시작합니다...
echo.

:: 1단계: takeown으로 폴더 소유권 획득
echo 1단계: 폴더 소유권 획득 중...
takeown /f "%FOLDER_PATH%" /r /d y
if %errorLevel% neq 0 (
    echo 오류: 폴더 소유권 획득 실패
    goto :error
)

:: 2단계: icacls로 권한 초기화
echo 2단계: 폴더 권한 초기화 중...
icacls "%FOLDER_PATH%" /reset /t /c /l
if %errorLevel% neq 0 (
    echo 오류: 폴더 권한 초기화 실패
    goto :error
)

:: 3단계: 현재 사용자에게 모든 권한 부여
echo 3단계: 사용자 권한 복구 중...
icacls "%FOLDER_PATH%" /grant "%USERNAME%":(F) /t /c /l
if %errorLevel% neq 0 (
    echo 오류: 사용자 권한 부여 실패
    goto :error
)

:: 4단계: Administrators 그룹에 모든 권한 부여
echo 4단계: 관리자 그룹 권한 복구 중...
icacls "%FOLDER_PATH%" /grant "Administrators":(F) /t /c /l
if %errorLevel% neq 0 (
    echo 오류: 관리자 그룹 권한 부여 실패
    goto :error
)

:: 5단계: 숨김 속성 제거
echo 5단계: 폴더 숨김 속성 제거 중...
attrib -h "%FOLDER_PATH%" /s /d
if %errorLevel% neq 0 (
    echo 경고: 폴더 숨김 속성 제거 실패 ^(무시 가능^)
)

echo.
echo 폴더 권한 복구가 완료되었습니다!
echo 이제 폴더에 정상적으로 접근할 수 있습니다.
echo.
goto :end

:error
echo.
echo 오류가 발생했습니다. 관리자 권한으로 실행했는지 확인하고 다시 시도해주세요.
echo.

:end
echo 종료하려면 아무 키나 누르세요...
pause > nul
