@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================
echo   地图采集系统 - PyInstaller 打包
echo ============================================
echo.

call venv\Scripts\activate.bat

echo [1/2] 清理旧打包文件...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo [2/2] 开始打包...
pyinstaller backend.spec --noconfirm

echo.
if exist dist\backend\backend.exe (
    echo ============================================
    echo   打包成功！
    echo   输出目录: %cd%\dist\backend\
    echo   可执行文件: dist\backend\backend.exe
    echo.
    echo   使用方式:
    echo     cd dist\backend
    echo     backend.exe
    echo     backend.exe --port 8090
    echo     backend.exe --host 0.0.0.0 --port 8090
    echo.
    echo   注意: 请将 .env 文件放在 backend.exe 同级目录
    echo ============================================
) else (
    echo 打包失败，请检查错误信息！
)

pause
