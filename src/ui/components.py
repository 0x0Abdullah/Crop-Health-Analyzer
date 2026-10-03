"""Small reusable UI building blocks. All colours come from CSS variables in theme.py."""
import html
from typing import Any, Dict, Iterable, List, Optional, Sequence

import streamlit as st


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def page_header(icon: str, title: str, subtitle: str = "") -> None:
    sub = f'<p class="cha-page-sub">{esc(subtitle)}</p>' if subtitle else ""
    st.html(f'<div class="cha-page-title"><span class="ico">{esc(icon)}</span><h1>{esc(title)}</h1></div>{sub}')


def section(title: str) -> None:
    st.html(f'<div class="cha-section">{esc(title)}</div>')


def callout(kind: str, text: str, title: Optional[str] = None, raw: bool = False) -> None:
    """kind: info | ok | warn | danger. ``raw=True`` allows trusted HTML in ``text``."""
    kind = kind if kind in ("info", "ok", "warn", "danger") else "info"
    body = text if raw else esc(text)
    head = f'<b class="t">{esc(title)}</b>' if title else ""
    st.html(f'<div class="cha-callout {kind}" role="note">{head}{body}</div>')


def chip(text: str, kind: str = "neutral") -> str:
    kind = kind if kind in ("ok", "info", "warn", "danger", "neutral") else "neutral"
    return f'<span class="cha-chip {kind}">{esc(text)}</span>'


def evidence_chip(level: str) -> str:
    l = (level or "").lower()
    kind = "ok" if "strong" in l else "info" if "moderate" in l else "warn" if "limited" in l else "neutral"
    return chip(level or "Insufficient evidence", kind)


def severity_chip(severity: str) -> str:
    s = (severity or "Unknown").capitalize()
    kind = {"High": "danger", "Moderate": "warn", "Low": "ok"}.get(s, "neutral")
    return chip(f"Severity: {s}", kind)


def html_table(rows: Sequence[Dict[str, Any]], columns: Sequence[str], labels: Optional[Dict[str, str]] = None,
               empty: str = "Nothing to show yet.", chips: Optional[Dict[str, Any]] = None) -> None:
    """Themed, escaped HTML table. ``chips`` maps column -> function(value)->chip html."""
    if not rows:
        st.html(f'<div class="cha-callout info">{esc(empty)}</div>')
        return
    labels = labels or {}
    head = "".join(f"<th>{esc(labels.get(c, c.replace('_', ' ').title()))}</th>" for c in columns)
    body = ""
    for r in rows:
        cells = ""
        for c in columns:
            v = r.get(c)
            cells += f"<td>{chips[c](v) if chips and c in chips else esc('—' if v in (None, '') else v)}</td>"
        body += f"<tr>{cells}</tr>"
    st.html(f'<div class="cha-table-wrap"><table class="cha-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def stat_grid(items: Iterable[Dict[str, Any]]) -> None:
    cards = "".join(f'<div class="cha-card cha-stat flat"><div class="n">{esc(i["value"])}</div><div class="l">{esc(i["label"])}</div></div>' for i in items)
    st.html(f'<div class="cha-grid stats">{cards}</div>')


def feature_grid(items: Iterable[Dict[str, str]]) -> None:
    cards = "".join(f'<div class="cha-card"><h3>{esc(i["icon"])} {esc(i["title"])}</h3><p>{esc(i["text"])}</p></div>' for i in items)
    st.html(f'<div class="cha-grid">{cards}</div>')


def steps(items: Iterable[str]) -> None:
    out = "".join(f'<div class="cha-step"><div class="num">{n}</div><div class="txt">{esc(t)}</div></div>' for n, t in enumerate(items, 1))
    st.html(out)


def bullet_list(items: Optional[List[str]]) -> None:
    """One markdown block (a single element) so bullets are tightly spaced."""
    items = [str(i).strip() for i in (items or []) if str(i).strip()]
    if items:
        st.markdown("\n".join(f"- {i}" for i in items))


def key_values(pairs: Sequence[tuple]) -> None:
    rows = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v) if v not in (None, '') else '—'}</dd>" for k, v in pairs)
    st.html(f'<dl class="cha-kv">{rows}</dl>')


def card_container(key: str):
    """Bordered container styled as a card (see ``[class*="st-key-card_"]`` in theme.py)."""
    return st.container(border=True, key=f"card_{key}")


def scroll_to_top(page: str = "") -> None:
    """Scroll Streamlit's main scroll area to the top (called after a page change). Best-effort."""
    js = ("<script>(function(){['[data-testid=\"stMain\"]','section.stMain','.main'].forEach(function(s){"
          "var e=document.querySelector(s);if(e&&e.scrollTo)e.scrollTo(0,0);});window.scrollTo(0,0);})();/*" + esc(page) + "*/</script>")
    try:
        st.html(js, unsafe_allow_javascript=True)
    except TypeError:  # Streamlit versions without unsafe_allow_javascript
        pass
