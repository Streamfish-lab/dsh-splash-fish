@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo   没有找到 Python。先装一个：
  echo      https://www.python.org/downloads/
  echo   安装时记得勾上 "Add Python to PATH"，装完关掉窗口重开。
  echo.
  pause
  exit /b
)

if "%~1"=="" (
  echo.
  echo   把图片文件直接拖到这个 BAT 上面松手，就会开始生成。
  echo.
  echo   图片越接近 16:9 越好，长边 1600 以上最好。
  echo   第一次用需要装 Python 和 Pillow：
  echo       pip install pillow
  echo.
  pause
  exit /b
)

python "tools\make_from_image.py" "%~1"

echo.
pause
