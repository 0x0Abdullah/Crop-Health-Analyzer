"""Installer and PWA Direct Download component for Desktop and Mobile platforms."""
import streamlit as st

from src.config import APP_TITLE
from src.ui.components import callout, section
from src.utils.installer import (
    get_current_app_url,
    generate_mobile_shortcut_html,
    generate_mobile_url_shortcut,
    generate_windows_launcher_bat,
)


def render_pwa_installer_script() -> None:
    """Injects Web App Manifest metadata and PWA install prompt handler JavaScript."""
    pwa_html = """
    <script>
    (function() {
        if (window.__cha_pwa_injected) return;
        window.__cha_pwa_injected = true;
        window.deferredPwaPrompt = window.deferredPwaPrompt || null;

        // Register Web App Manifest dynamically if not present
        if (!document.querySelector('link[rel="manifest"]')) {
            const manifest = {
                "name": "Crop Health Analyzer",
                "short_name": "CropHealth",
                "description": "AI-assisted agricultural decision support app",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#F2F7F4",
                "theme_color": "#1D6A4D",
                "icons": [
                    {
                        "src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌱</text></svg>",
                        "sizes": "192x192 512x512",
                        "type": "image/svg+xml"
                    }
                ]
            };
            const stringManifest = JSON.stringify(manifest);
            const blob = new Blob([stringManifest], {type: 'application/json'});
            const manifestUrl = URL.createObjectURL(blob);
            const link = document.createElement('link');
            link.rel = 'manifest';
            link.href = manifestUrl;
            document.head.appendChild(link);
        }

        // Catch beforeinstallprompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            window.deferredPwaPrompt = e;
            const statusEl = document.getElementById('pwa-status-banner');
            if (statusEl) {
                statusEl.className = 'cha-callout ok';
                statusEl.innerHTML = '<b>✅ Direct System Installation Ready!</b> Click the button below to add the app directly to your desktop/phone app launcher.';
            }
        });
    })();

    function triggerNativePwaInstall() {
        if (window.deferredPwaPrompt) {
            window.deferredPwaPrompt.prompt();
            window.deferredPwaPrompt.userChoice.then((choice) => {
                if (choice.outcome === 'accepted') {
                    alert('🎉 Crop Health Analyzer is installing on your device!');
                }
                window.deferredPwaPrompt = null;
            });
        } else {
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
            if (isIOS) {
                alert("📱 iPhone/iPad Direct Installation:\\n\\n1. Tap the Share button in Safari (at the bottom or top bar).\\n2. Scroll down and tap 'Add to Home Screen'.\\n3. Confirm by tapping 'Add'.");
            } else {
                alert("📲 Direct Web App Install Instructions:\\n\\n- Chrome / Edge (Desktop/Android): Click the Install icon in the browser address bar or menu (⋮) → 'Install page as app'.\\n\\nOr download the Desktop / Mobile launcher packages below for 1-click launch!");
            }
        }
    }
    </script>
    """
    st.html(pwa_html)


def render_install_section() -> None:
    """Renders the comprehensive direct download & system installation section."""
    render_pwa_installer_script()
    app_url = get_current_app_url()

    section("📲 Direct App Installation & Download Center")
    st.write(
        "You can directly install **Crop Health Analyzer** on your desktop computer or mobile device so it runs like a native standalone application."
    )

    # 1-Click Interactive Native PWA Trigger
    st.html("""
    <div id="pwa-status-banner" class="cha-callout info">
        <b>📲 Direct Web App Installer</b><br>
        Click the button below to trigger direct 1-click installation to your system (Desktop or Mobile).
    </div>
    <div style="margin: 12px 0 24px 0;">
        <button onclick="triggerNativePwaInstall()" style="
            background: linear-gradient(135deg, #1D6A4D 0%, #154e38 100%);
            color: white;
            border: none;
            padding: 14px 28px;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(29,106,77,0.3);
            display: inline-flex;
            align-items: center;
            gap: 10px;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='none'">
            <span>⚡ Click to Install App Directly on System</span>
        </button>
    </div>
    """)

    # Downloadable Packages Split by Platform
    c_desk, c_mob = st.columns(2)

    with c_desk:
        with st.container(border=True):
            st.markdown("### 💻 Desktop Direct Download")
            st.caption("Windows desktop 1-click application launcher")

            # Direct Download: Windows 1-Click Launcher .bat
            win_bat = generate_windows_launcher_bat(app_url)
            st.download_button(
                label="⚡ Download Desktop App Launcher (.bat)",
                data=win_bat,
                file_name="CropHealthAnalyzer-Launcher.bat",
                mime="application/x-bat",
                key="btn_dl_win_bat",
                use_container_width=True,
                type="primary",
                help="Double-click this batch file directly to launch the application in standalone Desktop window mode.",
            )

            st.markdown(
                "- **Windows Desktop Launch:** Double-click the downloaded **`CropHealthAnalyzer-Launcher.bat`** file to run the app directly as a desktop application."
            )

    with c_mob:
        with st.container(border=True):
            st.markdown("### 📱 Mobile Direct Downloads")
            st.caption("Android, iPhone & iPad options")

            # Direct Download: Mobile Standalone HTML App Launcher
            mobile_html = generate_mobile_shortcut_html(app_url)
            st.download_button(
                label="📱 Download Mobile App Launcher (.html)",
                data=mobile_html,
                file_name="CropHealthAnalyzer-Mobile.html",
                mime="text/html",
                key="btn_dl_mobile_html",
                use_container_width=True,
                type="primary",
                help="Save to your phone and open in browser to add directly to Home Screen.",
            )

            # Direct Download: Mobile URL Shortcut
            mobile_url = generate_mobile_url_shortcut(app_url)
            st.download_button(
                label="🔗 Download Mobile Web Shortcut (.url)",
                data=mobile_url,
                file_name="CropHealthAnalyzer.url",
                mime="application/internet-shortcut",
                key="btn_dl_mobile_url",
                use_container_width=True,
                help="Direct web shortcut link file for mobile or desktop launchers.",
            )

            st.markdown(
                "- **Android (Chrome):** Click **⚡ Click to Install App Directly** above or use **Download Mobile App Launcher**.\n"
                "- **iPhone / iPad (Safari):** Tap Safari Share button → **Add to Home Screen**."
            )

    callout(
        "ok",
        "🔒 <b>Security & Code Privacy Guaranteed:</b> Downloaded desktop launchers and mobile shortcuts act strictly as secure client windows. All Python source code, AI models, knowledge databases, and environment variables stay 100% private and protected on your hosted server or GitHub private repository.",
        title="Privacy & Deployment Architecture",
        raw=True,
    )
