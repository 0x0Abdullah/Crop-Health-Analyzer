import io
import zipfile
import streamlit as st

APP_NAME = "Crop Health Analyzer"
DEFAULT_URL = "http://localhost:8501"


def get_current_app_url() -> str:
    """Detects active host URL when deployed on Streamlit Cloud or hosted server."""
    try:
        headers = getattr(st.context, "headers", {})
        if headers:
            host = headers.get("x-forwarded-host") or headers.get("host") or "localhost:8501"
            proto = headers.get("x-forwarded-proto") or ("https" if "streamlit.app" in host else "http")
            return f"{proto}://{host}"
    except Exception:
        pass
    return DEFAULT_URL


def generate_windows_launcher_bat(url: str = DEFAULT_URL) -> bytes:
    """Generates a 1-click Windows batch script that opens the app in standalone desktop window mode.

    Contains NO application code or database files, ensuring your GitHub private repository
    and backend code remain 100% safe and secure on your server/deployment.
    """
    script = f"""@echo off
title {APP_NAME} Desktop Launcher
echo Launching {APP_NAME}...

REM If running locally in a developer environment
if exist ".venv\\Scripts\\python.exe" (
    call ".venv\\Scripts\\activate.bat"
    start "" python -m streamlit run app.py --server.headless=true
    timeout /t 3 >nul
)

REM Open in standalone desktop app window mode pointing to the hosted application URL
start "" chrome.exe --app="{url}" || start "" msedge.exe --app="{url}" || start "" "{url}"
exit /b 0
"""
    return script.encode("utf-8")


def generate_mobile_shortcut_html(url: str = DEFAULT_URL) -> bytes:
    """Generates a standalone web app HTML file for mobile devices to launch in full-screen PWA mode."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="{APP_NAME}">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#1D6A4D">
    <title>{APP_NAME}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #F2F7F4;
            color: #16302A;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
            text-align: center;
        }}
        .card {{
            background: white;
            padding: 28px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            max-width: 360px;
            width: 100%;
        }}
        .icon {{ font-size: 64px; margin-bottom: 12px; }}
        h2 {{ margin: 0 0 8px 0; color: #1D6A4D; }}
        p {{ margin: 0 0 20px 0; color: #4A635A; font-size: 0.95rem; line-height: 1.4; }}
        .btn {{
            display: inline-block;
            width: 100%;
            padding: 14px 0;
            background-color: #1D6A4D;
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 1rem;
            box-sizing: border-box;
            transition: background 0.2s;
        }}
        .btn:active {{ background-color: #154e38; }}
        .hint {{ font-size: 0.8rem; color: #738C82; margin-top: 16px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🌱</div>
        <h2>{APP_NAME}</h2>
        <p>Tap below to open the mobile app directly on your phone.</p>
        <a href="{url}" class="btn">🚀 Open App Now</a>
        <div class="hint">Tip: Tap your browser's share or menu icon and select <b>"Add to Home Screen"</b> to keep this app on your phone home screen!</div>
    </div>
    <script>
        // Auto-redirect if launched directly
        setTimeout(function() {{
            window.location.href = "{url}";
        }}, 800);
    </script>
</body>
</html>
"""
    return html_content.encode("utf-8")


def generate_mobile_url_shortcut(url: str = DEFAULT_URL) -> bytes:
    """Generates a standard .url Internet Shortcut file."""
    content = f"""[InternetShortcut]
URL={url}
IconIndex=0
HotKey=0
IDList=
"""
    return content.encode("utf-8")


def generate_desktop_app_zip(url: str = DEFAULT_URL) -> bytes:
    """Generates a complete ZIP package containing desktop installers, launcher scripts, and shortcut creators."""
    buffer = io.BytesIO()

    windows_launcher = f"""@echo off
title {APP_NAME} Desktop
echo Launching {APP_NAME}...
cd /d "%~dp0"

if exist ".venv\\Scripts\\python.exe" (
    call ".venv\\Scripts\\activate.bat"
    start "" python -m streamlit run app.py --server.headless=true
    timeout /t 3 >nul
)

start "" chrome.exe --app="{url}" || start "" msedge.exe --app="{url}" || start "" "{url}"
"""

    vbs_shortcut = """Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oShellLink = WshShell.CreateShortcut(strDesktop & "\\Crop Health Analyzer.lnk")
oShellLink.TargetPath = WScript.Arguments(0) & "\\Launch-Crop-Health-Analyzer.bat"
oShellLink.WorkingDirectory = WScript.Arguments(0)
oShellLink.Description = "Launch Crop Health Analyzer App"
oShellLink.Save
"""

    install_bat = f"""@echo off
title {APP_NAME} Desktop Setup
echo ===================================================
echo {APP_NAME} - Desktop Setup & Shortcut Creator
echo ===================================================
echo.
cd /d "%~dp0"

if not exist ".venv\\Scripts\\python.exe" (
    echo Creating Python virtual environment...
    py -3 -m venv .venv || python -m venv .venv
)

if exist ".venv\\Scripts\\activate.bat" (
    call ".venv\\Scripts\\activate.bat"
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo Creating Desktop Icon...
cscript //nologo Create-Desktop-Shortcut.vbs "%~dp0"

echo.
echo ===================================================
echo Setup complete! A shortcut link has been added to your Desktop.
echo Double-click 'Launch-Crop-Health-Analyzer.bat' or the Desktop shortcut to run.
echo ===================================================
pause
"""

    mac_linux_launcher = f"""#!/bin/bash
echo "Launching {APP_NAME}..."
cd "$(dirname "$0")"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

if command -v python3 &> /dev/null && [ -f "app.py" ]; then
    python3 -m streamlit run app.py --server.headless=true &
    sleep 3
fi

open "{url}" || xdg-open "{url}" || echo "Open {url} in your browser"
"""

    readme = f"""===================================================
{APP_NAME} - Desktop App Package
===================================================

QUICK START INSTRUCTIONS:

FOR WINDOWS:
1. Double-click 'Install-And-Create-Shortcut.bat' to set up the app and place a shortcut on your Desktop.
2. Double-click 'Launch-Crop-Health-Analyzer.bat' anytime to launch the app directly!

FOR MACOS / LINUX:
1. Open terminal in this folder.
2. Run: chmod +x Launch-Mac-Linux.sh && ./Launch-Mac-Linux.sh

DIRECT WEB APPLICATION URL:
{url}
"""

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Launch-Crop-Health-Analyzer.bat", windows_launcher)
        zf.writestr("Create-Desktop-Shortcut.vbs", vbs_shortcut)
        zf.writestr("Install-And-Create-Shortcut.bat", install_bat)
        zf.writestr("Launch-Mac-Linux.sh", mac_linux_launcher)
        zf.writestr("README.txt", readme)

    buffer.seek(0)
    return buffer.getvalue()
