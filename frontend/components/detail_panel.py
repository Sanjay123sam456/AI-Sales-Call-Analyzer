import re
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path


def score_color(s) -> str:
    v = s * 10 if s <= 10 else s
    return "#4CAF50" if v >= 80 else "#F59E0B" if v >= 60 else "#E74C3C"


def _radar(scores: dict) -> None:
    labels = [k.replace("_", " ").title() for k in scores]
    values = list(scores.values())
    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]], theta=labels + [labels[0]],
        fill="toself", fillcolor="rgba(76,175,80,0.1)",
        line=dict(color="#4CAF50", width=1.5),
        marker=dict(size=4, color="#4CAF50"),
        hovertemplate="%{theta}: <b>%{r}/10</b><extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0,10], tickvals=[2,4,6,8,10],
                           gridcolor="#222", linecolor="#222",
                           tickfont=dict(color="#444", size=10)),
            angularaxis=dict(gridcolor="#222", linecolor="#222",
                            tickfont=dict(color="#aaa", size=11)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10,b=10,l=20,r=20), height=240,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _parse_transcript(path: Path) -> list:
    if not path or not path.exists(): return []
    text   = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", text.strip())
    lines  = []
    for block in blocks:
        parts = [l.strip() for l in block.splitlines() if l.strip()]
        if len(parts) < 3: continue
        ts = re.match(r"\[(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})\]", parts[0])
        sp = re.match(r"(Advisor|Customer)\s*\(([^)]+)\):", parts[1])
        if not ts or not sp: continue
        lines.append({"timestamp": ts.group(1), "role": sp.group(1),
                      "name": sp.group(2).strip(), "text": " ".join(parts[2:])})
    return lines


def render_detail_panel(call: dict, transcript_path: Path) -> None:
    ev  = call["evaluation"]
    sc  = call["score"]
    col = score_color(sc)

    close_col, head_col = st.columns([1, 5])
    with close_col:
        if st.button("✕ close", key="close_detail"):
            st.session_state.selected_call = None
            st.rerun()
    with head_col:
        st.markdown(
            f"<span style='color:#555;font-size:13px;font-family:Courier New,monospace'>inspecting </span>"
            f"<span style='color:#4CAF50;font-size:14px;font-weight:700;font-family:Courier New,monospace'>"
            f"{call['call_id']}</span>", unsafe_allow_html=True,
        )

    st.markdown(
        f"<div style='padding:8px 0;border-bottom:1px solid #222;margin-bottom:10px;font-family:Courier New,monospace'>"
        f"<span style='color:{col};font-size:32px;font-weight:700'>{sc}</span>"
        f"<span style='color:#555;font-size:14px'>/100</span>&nbsp;&nbsp;&nbsp;"
        f"<span style='color:#555;font-size:12px'>"
        f"advisor: <span style='color:#E8E8E8'>{call['advisor']}</span>"
        f" &nbsp;·&nbsp; customer: <span style='color:#E8E8E8'>{call['customer']}</span>"
        f"</span></div>", unsafe_allow_html=True,
    )

    tabs = st.tabs(["[ overview ]", "[ scores ]", "[ transcript ]", "[ flags ]"])

    # ── Overview — Design D: Timeline ────────────────────────────────────────
    with tabs[0]:
        # Audio player
        audio_path = call.get("audio_path")
        if audio_path and Path(str(audio_path)).exists():
            st.markdown(
                "<div style='font-size:10px;color:#555;font-family:Courier New,monospace;"
                "margin-bottom:4px'>🎙 RECORDING</div>", unsafe_allow_html=True,
            )
            with open(audio_path, "rb") as f:
                ext = Path(str(audio_path)).suffix.lstrip(".")
                st.audio(f.read(), format=f"audio/{ext}")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Stat mini cards row
        sentiment = ev.get("customer_sentiment", "—")
        outcome   = ev.get("call_outcome", "—")
        lang      = call.get("lang", "en")
        fc        = call["flag_count"]

        sent_col = "#4CAF50" if "positive" in sentiment.lower() else "#F59E0B" if "neutral" in sentiment.lower() else "#E74C3C"
        flag_col = "#E74C3C" if fc else "#4CAF50"

        st.markdown(f"""
        <div style="display:flex;gap:8px;margin-bottom:12px">
            <div style="background:#111;border:1px solid #222;border-radius:4px;padding:8px 12px;flex:1;text-align:center">
                <div style="font-size:9px;color:#555;margin-bottom:3px">SENTIMENT</div>
                <div style="font-size:14px;color:{sent_col};font-family:Courier New,monospace">{sentiment.split(';')[0][:20]}</div>
            </div>
            <div style="background:{'#2e0808' if fc else '#0d1f10'};border:1px solid {'#4d1010' if fc else '#1a3d1e'};border-radius:4px;padding:8px 12px;text-align:center;min-width:60px">
                <div style="font-size:9px;color:#555;margin-bottom:3px">FLAGS</div>
                <div style="font-size:18px;font-weight:700;color:{flag_col};font-family:Courier New,monospace">{fc if fc else '✓'}</div>
            </div>
            <div style="background:#111;border:1px solid #222;border-radius:4px;padding:8px 12px;text-align:center;min-width:60px">
                <div style="font-size:9px;color:#555;margin-bottom:3px">LANG</div>
                <div style="font-size:13px;color:#F59E0B;font-family:Courier New,monospace">{lang}</div>
            </div>
        </div>
        <div style="font-size:14px;color:#888;line-height:1.7;background:#111;border:1px solid #222;
                    border-radius:4px;padding:8px 10px;margin-bottom:12px;font-family:Courier New,monospace">
            <span style="font-size:11px;color:#555;display:block;margin-bottom:4px">OUTCOME</span>
            {outcome}
        </div>
        """, unsafe_allow_html=True)

        # Summary with always-visible scrollbar
        summary = ev.get("summary", "")
        if summary:
            st.markdown(
                f"<div style='font-size:10px;color:#555;font-family:Courier New,monospace;margin-bottom:4px'>SUMMARY</div>"
                f"<div style='font-size:14px;color:#888;line-height:1.8;background:#111;border:1px solid #222;"
                f"border-radius:4px;padding:10px;max-height:90px;overflow-y:scroll;"
                f"scrollbar-width:thin;scrollbar-color:#333 #111;font-family:Courier New,monospace'>{summary}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # Timeline — strengths + improvements chronologically
        strengths    = ev.get("strengths", [])
        improvements = ev.get("improvements", [])
        red_flags    = ev.get("red_flags", [])

        timeline_items = []
        for s in strengths:
            timeline_items.append({"type": "strength", "title": s.get("title",""), "ts": s.get("timestamp",""), "detail": s.get("evidence","")})
        for i in improvements:
            timeline_items.append({"type": "improve", "title": i.get("title",""), "ts": i.get("timestamp",""), "detail": i.get("suggestion","")})
        for f in red_flags:
            timeline_items.append({"type": "flag", "title": f.get("statement", f.get("title","")), "ts": f.get("timestamp",""), "detail": f.get("reason","")})

        if timeline_items:
            st.markdown(
                "<div style='font-size:10px;color:#555;font-family:Courier New,monospace;margin-bottom:6px'>TIMELINE</div>",
                unsafe_allow_html=True,
            )
            items_html = ""
            for item in timeline_items:
                if item["type"] == "strength":
                    bc, ic, label = "#4CAF50", "#4CAF50", "✓"
                elif item["type"] == "improve":
                    bc, ic, label = "#F59E0B", "#F59E0B", "→"
                else:
                    bc, ic, label = "#E74C3C", "#E74C3C", "⚠"

                items_html += f"""
                <div style="display:flex;gap:10px;padding:6px 0;border-left:2px solid {bc};padding-left:10px;margin-bottom:6px">
                    <span style="font-size:10px;color:#555;width:100px;flex-shrink:0;font-family:Courier New,monospace">{item['ts']}</span>
                    <div>
                        <div style="font-size:14px;color:{ic};font-family:Courier New,monospace">{label} {item['title']}</div>
                        <div style="font-size:11px;color:#555;font-family:Courier New,monospace;margin-top:2px">{item['detail'][:80]}{'...' if len(item['detail'])>80 else ''}</div>
                    </div>
                </div>"""

            st.markdown(
                f"<div style='max-height:200px;overflow-y:scroll;padding-right:6px;"
                f"scrollbar-width:thin;scrollbar-color:#333 #0D0D0D'>{items_html}</div>",
                unsafe_allow_html=True,
            )

    # ── Scores ────────────────────────────────────────────────────────────────
    with tabs[1]:
        scores = ev.get("category_scores", {})
        if scores:
            _radar(scores)
            bars = "".join(
                f"<div style='display:flex;align-items:center;gap:10px;margin:5px 0;font-family:Courier New,monospace'>"
                f"<span style='width:140px;font-size:12px;color:#555'>{k.replace('_',' ')}</span>"
                f"<div style='width:110px;height:6px;background:#222;border-radius:2px'>"
                f"<div style='width:{v*10}%;height:6px;background:{score_color(v)};border-radius:2px'></div></div>"
                f"<span style='font-size:13px;font-weight:700;color:{score_color(v)}'>{v}</span></div>"
                for k, v in scores.items()
            )
            st.markdown(f"<div style='max-height:180px;overflow-y:auto;padding-right:4px'>{bars}</div>", unsafe_allow_html=True)

    # ── Transcript ────────────────────────────────────────────────────────────
    with tabs[2]:
        lines = _parse_transcript(transcript_path)
        if not lines:
            st.markdown("<span style='color:#555;font-size:13px;font-family:Courier New,monospace'>no transcript found</span>", unsafe_allow_html=True)
        else:
            bubbles = "".join(
                f"<div style='display:flex;justify-content:{'flex-start' if l['role']=='Advisor' else 'flex-end'};margin-bottom:10px'>"
                f"<div style='max-width:88%;padding:8px 12px;border-radius:6px;"
                f"background:{'#1a2a1a' if l['role']=='Advisor' else '#1a1a2a'};"
                f"border-left:2px solid {'#4CAF50' if l['role']=='Advisor' else '#38BDF8'}'>"
                f"<div style='font-size:11px;color:{'#4CAF50' if l['role']=='Advisor' else '#38BDF8'};margin-bottom:4px;font-family:Courier New,monospace'>{l['name']} · {l['timestamp']}</div>"
                f"<div style='font-size:13px;color:#ccc;line-height:1.5;font-family:Courier New,monospace'>{l['text']}</div>"
                f"</div></div>"
                for l in lines
            )
            st.markdown(f"<div style='max-height:400px;overflow-y:scroll;padding-right:6px;scrollbar-width:thin;scrollbar-color:#333 #0D0D0D'>{bubbles}</div>", unsafe_allow_html=True)

    # ── Flags ─────────────────────────────────────────────────────────────────
    with tabs[3]:
        red_flags = ev.get("red_flags", [])
        if not red_flags:
            st.markdown("<span style='color:#4CAF50;font-size:14px;font-family:Courier New,monospace'>✓ no flags — clean call</span>", unsafe_allow_html=True)
        else:
            items = ""
            for flag in red_flags:
                sev     = flag.get("severity","Medium")
                is_high = sev.lower() == "high"
                bc      = "#E74C3C" if is_high else "#F59E0B"
                bg      = "#1a0a0a" if is_high else "#1a1500"
                stmt    = flag.get("statement", flag.get("title",""))
                reason  = flag.get("reason", flag.get("description",""))
                ts      = flag.get("timestamp","")
                items += (
                    f"<div style='border-left:3px solid {bc};background:{bg};padding:10px 12px;"
                    f"margin-bottom:10px;border-radius:0 5px 5px 0;font-family:Courier New,monospace'>"
                    f"<div style='font-size:11px;font-weight:700;color:{bc};margin-bottom:4px'>{sev.upper()} · {ts}</div>"
                    f"<div style='font-size:13px;color:#ccc;margin-bottom:4px'>{stmt}</div>"
                    f"<div style='font-size:12px;color:#555'>{reason}</div></div>"
                )
            st.markdown(f"<div style='max-height:400px;overflow-y:scroll;padding-right:6px;scrollbar-width:thin;scrollbar-color:#333 #0D0D0D'>{items}</div>", unsafe_allow_html=True)