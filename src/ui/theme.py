"""Design tokens + stylesheet for the whole app.

Design rule that fixes the old dark-theme bug: **no component hard-codes a colour.**
Every colour comes from a CSS variable (``--ink``, ``--surface`` …). Light and dark are just two
sets of values for the same variables, so text and its background can never drift apart.
Streamlit's own widgets (buttons, inputs, dropdowns, uploader, expanders, chat, tabs, tooltips …)
are re-styled from the same variables, and data tables / alerts are rendered by our own HTML
components rather than Streamlit's canvas/pre-coloured widgets.
"""
from typing import Dict

LIGHT: Dict[str, str] = {
    "scheme": "light",
    "bg": "#f2f7f4", "glow-a": "rgba(139,195,74,.10)", "glow-b": "rgba(47,143,104,.09)",
    "surface": "#ffffff", "surface-alt": "#f1f6f3", "surface-hover": "#e6f0ea",
    "ink": "#16302a", "ink-soft": "#334a40", "muted": "#51645c",
    "line": "#d6e3dc", "line-strong": "#b3c9bd",
    "accent": "#1d6a4d", "accent-soft": "#dcefe5", "accent-ink": "#14503a",
    "link": "#0d6444",
    "btn-bg": "#ffffff", "btn-ink": "#16302a", "btn-line": "#c2d5ca", "btn-hover": "#eaf3ee",
    "input-bg": "#ffffff", "input-line": "#b9cdc2",
    "info-bg": "#e8f2fc", "info-ink": "#0d3b66", "info-line": "#b3d2ee",
    "ok-bg": "#e3f4ea", "ok-ink": "#0f4f2e", "ok-line": "#a2d4b5",
    "warn-bg": "#fff3d9", "warn-ink": "#5a3b00", "warn-line": "#e0ac45",
    "danger-bg": "#fdeaea", "danger-ink": "#7a1212", "danger-line": "#e3a0a0",
    "neutral-bg": "#e9eeeb", "neutral-ink": "#34463e",
    "shadow": "0 8px 24px rgba(20,50,40,.06)", "shadow-hover": "0 14px 32px rgba(20,70,49,.12)",
    "code-bg": "#edf3ef", "skeleton": "#e1ebe5", "nav-bg": "rgba(242,247,244,.92)",
}

DARK: Dict[str, str] = {
    "scheme": "dark",
    "bg": "#0a1310", "glow-a": "rgba(80,160,100,.10)", "glow-b": "rgba(47,143,104,.08)",
    "surface": "#13231d", "surface-alt": "#0f1c17", "surface-hover": "#1c3329",
    "ink": "#e9f5ef", "ink-soft": "#cfe2d8", "muted": "#adc4b9",
    "line": "#284539", "line-strong": "#3b5e4f",
    "accent": "#52c394", "accent-soft": "#1b3a2d", "accent-ink": "#bdebd5",
    "link": "#86e0b4",
    "btn-bg": "#18302a", "btn-ink": "#e9f5ef", "btn-line": "#37594b", "btn-hover": "#214037",
    "input-bg": "#0f1c17", "input-line": "#3a5c4e",
    "info-bg": "#0f2a3d", "info-ink": "#d0e9fb", "info-line": "#2c5c80",
    "ok-bg": "#12301f", "ok-ink": "#cdf2dc", "ok-line": "#2f6a47",
    "warn-bg": "#35290a", "warn-ink": "#ffe8b5", "warn-line": "#a67a14",
    "danger-bg": "#3b1818", "danger-ink": "#ffd9d9", "danger-line": "#8d3b3b",
    "neutral-bg": "#1e302a", "neutral-ink": "#cfe0d7",
    "shadow": "0 8px 24px rgba(0,0,0,.35)", "shadow-hover": "0 14px 32px rgba(0,0,0,.5)",
    "code-bg": "#0c1612", "skeleton": "#1a2e26", "nav-bg": "rgba(10,19,16,.92)",
}

TEXT_SCALE = {"Small": "93.75%", "Default": "100%", "Large": "112.5%"}


def _vars(tokens: Dict[str, str]) -> str:
    body = ";".join(f"--{k}:{v}" for k, v in tokens.items() if k != "scheme")
    return f":root{{{body};color-scheme:{tokens['scheme']}}}"


# --------------------------------------------------------------------------------------------
# Component + widget rules. Only var(--…) colours are used below (plus the fixed brand gradient
# for the hero banner and primary buttons, which always carry white text).
# --------------------------------------------------------------------------------------------
BASE_CSS = r"""
/* ---------- chrome: hide Streamlit's own header so our navigation is the header ---------- */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stAppDeployButton"], #MainMenu, footer { display:none !important; }
html { scroll-behavior:smooth; }
html, body, .stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background-color:var(--bg) !important; color:var(--ink);
}
.stApp { background-image:radial-gradient(ellipse at 8% 4%,var(--glow-a),transparent 32%),radial-gradient(ellipse at 96% 22%,var(--glow-b),transparent 30%) !important; background-attachment:fixed; }
[data-testid="stMainBlockContainer"], .block-container { max-width:1180px; padding:.6rem 1.25rem 4rem !important; }
::selection { background:var(--accent-soft); color:var(--ink); }

/* ---------- typography ---------- */
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] :is(p,li,span,strong,em,td,th,blockquote,h1,h2,h3,h4,h5,h6),
[data-testid="stHeading"] :is(h1,h2,h3,h4,h5,h6,span), h1,h2,h3,h4,h5,h6,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *, label, label :is(p,span,div),
[data-testid="stCheckbox"] *, [data-testid="stToggle"] *, [data-testid="stRadio"] label *, [data-testid="stRadio"] [role="radiogroup"] *,
[data-testid="stExpander"] summary *, [data-testid="stSpinner"] * { color:var(--ink) !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *, [data-testid="stImageCaption"],
[data-testid="stFileUploaderDropzoneInstructions"] *, small { color:var(--muted) !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *, [data-testid="stMarkdownContainer"] *, [data-testid="stElementContainer"]:has([data-testid="stCaptionContainer"]) { opacity:1 !important; }
[data-testid="stCaptionContainer"] a { color:var(--link) !important; }
h1,h2,h3 { letter-spacing:-.022em; }
[data-testid="stMarkdownContainer"] a, a { color:var(--link) !important; text-decoration:underline; text-underline-offset:2px; }
[data-testid="stMarkdownContainer"] code { background:var(--code-bg) !important; color:var(--ink) !important; border:1px solid var(--line); border-radius:6px; padding:.05em .35em; }
[data-testid="stMarkdownContainer"] hr, hr { border-color:var(--line) !important; }
[data-testid="stMarkdownContainer"] blockquote { border-left:4px solid var(--line-strong) !important; background:var(--surface-alt); padding:.4rem .9rem; border-radius:0 10px 10px 0; }
[data-testid="stMarkdownContainer"] ul, [data-testid="stMarkdownContainer"] ol { margin-bottom:.4rem; }
[data-testid="stMarkdownContainer"] li { margin:.15rem 0; }
[data-testid="stMarkdownContainer"] table { border-collapse:collapse; }
[data-testid="stMarkdownContainer"] :is(td,th) { border:1px solid var(--line) !important; padding:.35rem .6rem; }

/* ---------- buttons ---------- */
[data-testid^="stBaseButton-"]:not([data-testid="stBaseButton-header"]):not([data-testid="stBaseButton-headerNoPadding"]), [data-testid="stPopoverButton"] {
  border-radius:12px; font-weight:600; transition:transform .16s ease, box-shadow .16s ease, background-color .16s ease; }
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"], [data-testid="stBaseButton-tertiary"], [data-testid="stBaseButton-minimal"], [data-testid="stPopoverButton"] {
  background:var(--btn-bg) !important; color:var(--btn-ink) !important; border:1px solid var(--btn-line) !important; }
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-secondaryFormSubmit"]:hover, [data-testid="stBaseButton-tertiary"]:hover, [data-testid="stPopoverButton"]:hover {
  background:var(--btn-hover) !important; border-color:var(--accent) !important; transform:translateY(-1px); box-shadow:var(--shadow); }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background:linear-gradient(110deg,#1b6a4c,#25805e) !important; color:#fff !important; border:1px solid #1b6a4c !important; box-shadow:0 4px 12px rgba(27,106,76,.22); }
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover { filter:brightness(1.1); transform:translateY(-1px); }
[data-testid^="stBaseButton-"]:not([data-testid="stBaseButton-header"]) *, [data-testid="stPopoverButton"] * { color:inherit !important; }
[data-testid^="stBaseButton-"]:disabled { opacity:.5 !important; transform:none !important; box-shadow:none !important; cursor:not-allowed; }
[data-testid^="stBaseButton-"]:focus-visible, input:focus-visible, textarea:focus-visible, summary:focus-visible { outline:3px solid var(--accent) !important; outline-offset:2px; }

/* ---------- text inputs, text areas, selects, date pickers ---------- */
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"], [data-testid="stNumberInputContainer"],
[data-testid="stSelectbox"] [role="group"], [data-testid="stMultiSelect"] [role="group"], [data-testid="stTimeInput"] [role="group"], [data-testid="stDateInputField"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div, [data-testid="stMultiSelect"] [data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="base-input"] {
  background-color:var(--input-bg) !important; border:1px solid var(--input-line) !important; border-radius:12px !important; }
[data-testid="stTextInputRootElement"]:focus-within, [data-testid="stTextAreaRootElement"]:focus-within, [data-testid="stSelectbox"] [role="group"]:focus-within,
[data-testid="stMultiSelect"] [role="group"]:focus-within, [data-testid="stDateInputField"]:focus-within { border-color:var(--accent) !important; box-shadow:0 0 0 1px var(--accent); }
input, textarea, [data-testid="stSelectbox"] input, [data-testid="stMultiSelect"] input {
  background-color:transparent !important; color:var(--ink) !important; -webkit-text-fill-color:var(--ink) !important; caret-color:var(--ink); }
input::placeholder, textarea::placeholder { color:var(--muted) !important; -webkit-text-fill-color:var(--muted) !important; opacity:1; }
[data-testid="stSelectbox"] [role="group"] button, [data-testid="stMultiSelect"] [role="group"] button, [data-testid="stDateInput"] button, [data-testid="stNumberInputContainer"] button {
  background:transparent !important; color:var(--muted) !important; border:none !important; box-shadow:none !important; }
[data-testid="stSelectbox"] svg, [data-testid="stMultiSelect"] svg, [data-testid="stDateInput"] svg, [data-testid="stNumberInputContainer"] svg { fill:currentColor !important; color:var(--muted) !important; }
[data-tag], [data-baseweb="tag"] { background:var(--accent-soft) !important; color:var(--accent-ink) !important; border:1px solid var(--line-strong) !important; border-radius:999px !important; }
[data-tag] *, [data-baseweb="tag"] * { color:var(--accent-ink) !important; }
[data-testid="stDateInputField"] [role="spinbutton"], [data-testid="stDateInputField"] span { background:transparent !important; color:var(--ink) !important; }
[data-testid="stDateInputField"] [role="spinbutton"]:focus { background:var(--accent-soft) !important; border-radius:6px; outline:none; }
[data-testid="stDateInputField"] [aria-hidden="true"] { color:var(--muted) !important; }
[data-testid="stTextInputRootElement"][aria-disabled="true"], input:disabled, textarea:disabled { opacity:.6; }

/* dropdown / popover surfaces (rendered in a portal outside .stApp, so selectors are global) */
[data-testid="stSelectboxVirtualDropdown"], [role="listbox"], [data-baseweb="popover"] > div, [data-baseweb="menu"], ul[role="listbox"],
[data-testid="stPopoverBody"], [data-testid="stDateInputCalendar"], [data-baseweb="calendar"], div[role="dialog"], [data-testid="stDialog"] > div {
  background:var(--surface) !important; color:var(--ink) !important; border-color:var(--line) !important; }
[data-testid="stPopoverBody"], div[role="dialog"] { border:1px solid var(--line) !important; border-radius:16px !important; box-shadow:var(--shadow-hover) !important; }
[role="option"], [role="option"] *, [data-baseweb="menu"] li, [data-baseweb="menu"] li * { color:var(--ink) !important; background-color:transparent; }
[role="option"]:hover, [role="option"][data-focused="true"], [role="option"][data-focused], [data-baseweb="menu"] li:hover { background-color:var(--surface-hover) !important; }
[role="option"][aria-selected="true"], [role="option"][data-selected="true"] { background-color:var(--accent-soft) !important; }
[data-testid="stDateInputCalendar"] *, [data-baseweb="calendar"] *, [role="dialog"] [role="grid"] *, [role="dialog"] [role="gridcell"] * { color:var(--ink) !important; }
[data-testid="stDateInputCalendar"] button, [data-baseweb="calendar"] button, [role="dialog"] [role="gridcell"] { background:transparent !important; }
[role="gridcell"][aria-selected="true"], [role="gridcell"][data-selected="true"], [data-baseweb="calendar"] [aria-selected="true"] { background:var(--accent) !important; border-radius:50%; }
[role="gridcell"][aria-selected="true"] *, [role="gridcell"][data-selected="true"] *, [data-baseweb="calendar"] [aria-selected="true"] * { color:#fff !important; }
[role="gridcell"][aria-disabled="true"], [role="gridcell"][data-disabled="true"] { opacity:.4; }
div[role="dialog"] header, div[role="dialog"] h1, div[role="dialog"] h2, div[role="dialog"] h3 { color:var(--ink) !important; }
[data-testid="stTooltipContent"], [data-baseweb="tooltip"] { background:var(--surface) !important; color:var(--ink) !important; border:1px solid var(--line); box-shadow:var(--shadow); }
[data-testid="stTooltipContent"] * { color:var(--ink) !important; }

/* ---------- checkbox / toggle / radio ---------- */
[data-testid="stCheckbox"] label span[role="checkbox"], [data-baseweb="checkbox"] > div:first-child { border-color:var(--line-strong) !important; background-color:var(--input-bg); }
[data-testid="stCheckbox"] label:has(input:checked) span[role="checkbox"] { background-color:var(--accent) !important; border-color:var(--accent) !important; }
[data-testid="stToggle"] label > div:first-of-type { background-color:var(--muted); }
[data-testid="stToggle"] label:has(input:checked) > div:first-of-type { background-color:var(--accent) !important; }
[data-testid="stRadio"] [role="radiogroup"] label { padding:.15rem .55rem; border-radius:10px; }
[data-testid="stRadio"] [role="radiogroup"] label:hover { background:var(--surface-hover); }

/* ---------- file uploader & camera ---------- */
[data-testid="stFileUploaderDropzone"] { background:var(--surface-alt) !important; border:1.5px dashed var(--line-strong) !important; border-radius:16px !important; }
[data-testid="stFileUploaderDropzone"]:hover { border-color:var(--accent) !important; background:var(--surface-hover) !important; }
[data-testid="stFileUploaderDropzone"] * { color:var(--ink); }
[data-testid="stFileUploaderDropzoneInstructions"] * { color:var(--muted) !important; }
[data-testid="stFileUploaderFile"], [data-testid="stFileUploaderFileData"] { background:transparent !important; }
[data-testid="stFileChip"] { background:var(--surface) !important; border:1px solid var(--line-strong) !important; border-radius:12px !important; }
[data-testid="stFileChip"] *, [data-testid="stFileChipName"] { color:var(--ink) !important; }
[data-testid="stFileChip"] small, [data-testid="stFileChip"] [class*="Size"], [data-testid="stFileChipSize"] { color:var(--muted) !important; }
[data-testid="stFileChipDeleteBtn"] button, [data-testid="stFileChip"] button { background:transparent !important; border:none !important; color:var(--muted) !important; }
[data-testid="stFileUploaderFile"] *, [data-testid="stFileUploaderFileName"] { color:var(--ink) !important; }
[data-testid="stFileUploaderPagination"] * { color:var(--muted) !important; }
[data-testid="stCameraInput"] { background:var(--surface-alt) !important; border:1px solid var(--line) !important; border-radius:16px !important; overflow:hidden; }
[data-testid="stCameraInput"] * { color:var(--ink); }
[data-testid="stCameraInputWebcamStyledBox"], [data-testid="stCameraInputWebcamComponent"] { background:var(--surface-alt) !important; }
[data-testid="stCameraInputWebcamStyledBox"] * { color:var(--muted) !important; }
[data-testid="stCameraInput"] [data-testid="stBaseButton-secondary"] { border-radius:0 0 14px 14px !important; }

/* ---------- containers: expanders, bordered blocks, status, tabs, chat ---------- */
[data-testid="stExpander"], [data-testid="stStatus"] { background:var(--surface) !important; border:1px solid var(--line) !important; border-radius:16px !important; overflow:hidden; }
[data-testid="stExpander"] details, [data-testid="stStatus"] details { background:transparent !important; border:none !important; }
[data-testid="stExpander"] summary, [data-testid="stStatus"] summary { background:transparent !important; color:var(--ink) !important; font-weight:600; }
[data-testid="stExpander"] summary:hover, [data-testid="stStatus"] summary:hover { background:var(--surface-hover) !important; }
[data-testid="stExpander"] summary svg, [data-testid="stStatus"] summary svg { fill:currentColor; }
[data-testid="stExpanderDetails"] { background:transparent !important; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line) !important; }
[class*="st-key-card_"] { background:var(--surface) !important; border:1px solid var(--line) !important; border-radius:18px !important; padding:.4rem .35rem; box-shadow:var(--shadow); }

[data-testid="stTabs"] [role="tablist"] { border-bottom:1px solid var(--line) !important; gap:.25rem; }
[data-testid="stTabs"] button[role="tab"] { color:var(--muted) !important; background:transparent !important; border-radius:10px 10px 0 0; }
[data-testid="stTabs"] button[role="tab"] * { color:inherit !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:var(--accent-ink) !important; font-weight:700; border-bottom:3px solid var(--accent) !important; }
[data-testid="stTabs"] button[role="tab"]:hover { background:var(--surface-hover) !important; color:var(--ink) !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background:var(--accent) !important; }
[data-testid="stTabs"] [data-baseweb="tab-border"] { background:var(--line) !important; }

[data-testid="stChatMessage"] { background:var(--surface) !important; border:1px solid var(--line); border-radius:16px; padding:.9rem 1rem; }
[data-testid="stChatMessage"] * { color:var(--ink); }
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] { background:var(--accent-soft) !important; }
[data-testid="stChatMessageAvatarUser"] *, [data-testid="stChatMessageAvatarAssistant"] * { color:var(--accent-ink) !important; }
[data-testid="stBottom"], [data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"], [data-testid="stChatInputContainer"] { background:var(--bg) !important; }
[data-testid="stChatInput"] { background:var(--input-bg) !important; border:1px solid var(--input-line) !important; border-radius:16px !important; }
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] [data-baseweb="textarea"], [data-testid="stChatInput"] [data-baseweb="base-input"] { background:transparent !important; border:none !important; }
[data-testid="stChatInput"] textarea { color:var(--ink) !important; -webkit-text-fill-color:var(--ink) !important; }
[data-testid="stChatInput"] button { background:var(--accent) !important; color:#fff !important; border:none !important; }
[data-testid="stChatInput"] button svg { fill:#fff !important; color:#fff !important; }

[data-testid="stProgress"] [role="progressbar"], [data-testid="stProgress"] > div > div { background-color:var(--line) !important; }
[data-testid="stProgress"] [role="progressbar"] > div, [data-testid="stProgress"] > div > div > div { background-color:var(--accent) !important; }
[data-testid="stSkeleton"], [data-testid="stSkeleton"] * { background-color:var(--skeleton) !important; }
[data-testid="stToast"], [data-testid="stToastContainer"] > div { background:var(--surface) !important; color:var(--ink) !important; border:1px solid var(--line); box-shadow:var(--shadow-hover); }
[data-testid="stToast"] * { color:var(--ink) !important; }
[data-testid="stCode"], pre { background:var(--code-bg) !important; border:1px solid var(--line); border-radius:12px; }
[data-testid="stCode"] *, pre * { color:var(--ink) !important; }
[data-testid="stImage"] img { border-radius:12px; }
[data-testid="stForm"] { background:var(--surface) !important; border:1px solid var(--line) !important; border-radius:18px !important; }
[data-testid="stException"], [data-testid="stException"] * { color:var(--danger-ink) !important; }
[data-testid="stException"] { background:var(--danger-bg) !important; border:1px solid var(--danger-line); border-radius:12px; }
iframe[height="0"] { display:none; }
[data-testid="stElementContainer"]:has(> iframe[height="0"]), [data-testid="stElementContainer"]:has(iframe[height="0"]) { display:none !important; }

/* ---------- navigation (sticky, horizontally scrollable on small screens) ---------- */
[class*="st-key-topnav"] { position:sticky; top:0; z-index:100; padding:.55rem 0 .5rem; margin-bottom:.5rem; background:var(--nav-bg); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px); border-bottom:1px solid var(--line); }
[class*="st-key-topnav"] [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; overflow-x:auto; gap:.4rem !important; scrollbar-width:thin; padding-bottom:2px; }
[class*="st-key-topnav"] [data-testid="stColumn"] { flex:1 0 auto !important; width:auto !important; min-width:max-content !important; }
[class*="st-key-topnav"] button { min-height:2.55rem; padding:.3rem .85rem; white-space:nowrap; width:100%; }
[class*="st-key-topnav"] [data-testid="stBaseButton-secondary"] { border-color:transparent !important; background:transparent !important; }
[class*="st-key-topnav"] [data-testid="stBaseButton-secondary"]:hover { background:var(--surface-hover) !important; border-color:var(--line) !important; }

/* ---------- reusable components ---------- */
.cha-hero { position:relative; overflow:hidden; isolation:isolate; border-radius:24px; padding:34px 34px 32px; margin:6px 0 20px; color:#fff;
  background:linear-gradient(115deg,#0f3b2e 0%,#1b654a 56%,#2a8862 100%); background-size:160% 160%; box-shadow:0 18px 45px rgba(15,60,45,.22);
  animation:cha-drift 10s ease-in-out infinite alternate; }
.cha-hero::before { content:""; position:absolute; z-index:-1; width:330px; height:330px; right:-95px; top:-155px; border-radius:50%; border:1px solid rgba(255,255,255,.17); box-shadow:0 0 0 28px rgba(255,255,255,.035),0 0 0 58px rgba(255,255,255,.025); }
.cha-hero::after { content:"🌿"; position:absolute; right:5%; bottom:-15%; font-size:clamp(5rem,10vw,9rem); opacity:.2; transform:rotate(-12deg); pointer-events:none; }
.cha-hero h1, .cha-hero p, .cha-hero b, .cha-hero span { color:#fff !important; }
.cha-hero h1 { margin:0; padding:0; font-size:clamp(1.9rem,4vw,2.6rem); line-height:1.15; }
.cha-hero p { margin:.55rem 0 0; max-width:820px; line-height:1.6; opacity:.96; }
.cha-page-title { display:flex; align-items:center; gap:.7rem; margin:.4rem 0 .15rem; }
.cha-page-title .ico { font-size:1.9rem; line-height:1; }
.cha-page-title h1 { margin:0; padding:0; font-size:clamp(1.55rem,3vw,2.05rem); line-height:1.2; color:var(--ink) !important; }
.cha-page-sub { color:var(--muted) !important; margin:0 0 1rem; line-height:1.55; }
.cha-section { margin:1.4rem 0 .5rem; font-size:1.25rem; font-weight:700; letter-spacing:-.015em; color:var(--ink) !important; }
.cha-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:14px; margin:6px 0 14px; }
.cha-grid.stats { grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); }
.cha-card { background:var(--surface); border:1px solid var(--line); border-radius:18px; padding:18px 20px; box-shadow:var(--shadow); transition:transform .2s ease, box-shadow .2s ease, border-color .2s ease; color:var(--ink); }
.cha-card:hover { transform:translateY(-3px); box-shadow:var(--shadow-hover); border-color:var(--line-strong); }
.cha-card h3 { margin:0 0 .35rem; font-size:1.05rem; color:var(--ink) !important; }
.cha-card p { margin:0; color:var(--muted) !important; line-height:1.55; font-size:.95rem; }
.cha-card.flat:hover { transform:none; }
.cha-stat { text-align:left; }
.cha-stat .n { font-size:2rem; font-weight:800; letter-spacing:-.03em; color:var(--accent-ink) !important; line-height:1.1; }
.cha-stat .l { color:var(--muted) !important; font-size:.9rem; margin-top:.2rem; }
.cha-chip { display:inline-block; padding:4px 12px; border-radius:999px; font-weight:700; font-size:.82rem; line-height:1.4; border:1px solid transparent; white-space:nowrap; }
.cha-chip.ok { background:var(--ok-bg); color:var(--ok-ink) !important; border-color:var(--ok-line); }
.cha-chip.info { background:var(--info-bg); color:var(--info-ink) !important; border-color:var(--info-line); }
.cha-chip.warn { background:var(--warn-bg); color:var(--warn-ink) !important; border-color:var(--warn-line); }
.cha-chip.danger { background:var(--danger-bg); color:var(--danger-ink) !important; border-color:var(--danger-line); }
.cha-chip.neutral { background:var(--neutral-bg); color:var(--neutral-ink) !important; border-color:var(--line); }
.cha-callout { border-radius:14px; padding:12px 16px; margin:.6rem 0; border:1px solid; border-left-width:5px; line-height:1.55; }
.cha-callout, .cha-callout * { font-size:.95rem; }
.cha-callout b.t { display:block; margin-bottom:2px; }
.cha-callout.info { background:var(--info-bg); border-color:var(--info-line); color:var(--info-ink) !important; }
.cha-callout.ok { background:var(--ok-bg); border-color:var(--ok-line); color:var(--ok-ink) !important; }
.cha-callout.warn { background:var(--warn-bg); border-color:var(--warn-line); color:var(--warn-ink) !important; }
.cha-callout.danger { background:var(--danger-bg); border-color:var(--danger-line); color:var(--danger-ink) !important; }
.cha-callout.info *, .cha-callout.info p { color:var(--info-ink) !important; } .cha-callout.ok *, .cha-callout.ok p { color:var(--ok-ink) !important; }
.cha-callout.warn *, .cha-callout.warn p { color:var(--warn-ink) !important; } .cha-callout.danger *, .cha-callout.danger p { color:var(--danger-ink) !important; }
.cha-callout a { color:inherit !important; font-weight:700; }
.cha-table-wrap { overflow-x:auto; border:1px solid var(--line); border-radius:14px; background:var(--surface); margin:.4rem 0 1rem; }
.cha-table { width:100%; border-collapse:collapse; font-size:.93rem; color:var(--ink); }
.cha-table th { text-align:left; padding:10px 14px; background:var(--surface-alt); color:var(--muted) !important; font-weight:700; font-size:.8rem; letter-spacing:.03em; text-transform:uppercase; border-bottom:1px solid var(--line); white-space:nowrap; }
.cha-table td { padding:10px 14px; border-bottom:1px solid var(--line); color:var(--ink) !important; vertical-align:top; }
.cha-table tr:last-child td { border-bottom:none; }
.cha-table tbody tr:hover td { background:var(--surface-hover); }
.cha-kv { display:grid; grid-template-columns:max-content 1fr; gap:.35rem 1rem; margin:.3rem 0; }
.cha-kv dt { color:var(--muted) !important; font-weight:600; } .cha-kv dd { margin:0; color:var(--ink) !important; }
.cha-result { background:var(--surface); border:1px solid var(--line); border-left:6px solid var(--accent); border-radius:18px; padding:20px 22px; box-shadow:var(--shadow); margin:.4rem 0 1rem; }
.cha-result .cond { font-size:1.55rem; font-weight:800; letter-spacing:-.02em; color:var(--ink) !important; margin:.1rem 0 .6rem; line-height:1.25; }
.cha-result .meta { color:var(--muted) !important; font-size:.92rem; margin-top:.6rem; }
.cha-result.sev-high { border-left-color:#d64545; } .cha-result.sev-moderate { border-left-color:#e0a329; } .cha-result.sev-low { border-left-color:#2f9e6d; }
.cha-step { display:flex; gap:12px; align-items:flex-start; margin:.5rem 0; color:var(--ink); }
.cha-step .num { flex:0 0 auto; width:30px; height:30px; border-radius:50%; background:var(--accent-soft); color:var(--accent-ink) !important; font-weight:800; display:flex; align-items:center; justify-content:center; }
.cha-step .txt { padding-top:3px; color:var(--ink) !important; }
.cha-muted { color:var(--muted) !important; }
.cha-footer { text-align:center; color:var(--muted) !important; font-size:.88rem; padding:1.4rem 0 .4rem; border-top:1px solid var(--line); margin-top:2.2rem; }
.cha-badge-dot { display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:6px; vertical-align:baseline; }
@keyframes cha-drift { from { background-position:0% 50%; } to { background-position:100% 50%; } }
@keyframes cha-rise { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
[data-testid="stMainBlockContainer"] { animation:cha-rise .35s ease both; }
@media (max-width: 760px) {
  [data-testid="stMainBlockContainer"], .block-container { padding:.4rem .8rem 4rem !important; }
  .cha-hero { padding:24px 20px; border-radius:20px; }
  [class*="st-key-topnav"] button { padding:.3rem .6rem; font-size:.85rem; }
  .cha-kv { grid-template-columns:1fr; gap:0; } .cha-kv dd { margin-bottom:.45rem; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation:none !important; transition:none !important; scroll-behavior:auto !important; } }
"""

REDUCE_MOTION_CSS = "*, *::before, *::after { animation:none !important; transition:none !important; scroll-behavior:auto !important; }"


def build_css(theme: str = "System", text_size: str = "Default", reduce_motion: bool = False) -> str:
    """Return the complete <style> block for the chosen appearance settings."""
    if theme == "Dark":
        palette = _vars(DARK)
    elif theme == "Light":
        palette = _vars(LIGHT)
    else:  # System: light by default, dark when the OS/browser prefers dark
        palette = _vars(LIGHT) + "@media (prefers-color-scheme: dark){" + _vars(DARK) + "}"
    scale = TEXT_SCALE.get(text_size, "100%")
    parts = [palette, f"html{{font-size:{scale} !important}}", BASE_CSS]
    if reduce_motion:
        parts.append(REDUCE_MOTION_CSS)
    return "<style>" + "\n".join(parts) + "</style>"
