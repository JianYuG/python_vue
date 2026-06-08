"""
地图采集系统 - 后端启动入口

此文件用于 PyInstaller 打包为可执行文件。
打包后运行: backend.exe 或 backend.exe --port 8090
"""
import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser(description='地图采集系统 - 后端服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8090, help='监听端口 (默认: 8090)')
    parser.add_argument('--reload', action='store_true', help='启用热重载 (仅开发使用)')
    args = parser.parse_args()

    # PyInstaller 打包后，需要将 _internal 目录加入 sys.path
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        os.chdir(os.path.dirname(sys.executable))
        sys.path.insert(0, base_path)

    import uvicorn
    uvicorn.run(
        'app.main:app',
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == '__main__':
    main()
