@echo off
cd /d %~dp0

echo 正在启动后端服务...
echo 虚拟环境: %cd%\venv
echo 服务地址: http://localhost:8090
echo API文档: http://localhost:8090/docs
echo.

call venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload

@REM cd e:\xm_bjyt\zself\python_vue\backend; .\venv\Scripts\python.exe run.py --reload
