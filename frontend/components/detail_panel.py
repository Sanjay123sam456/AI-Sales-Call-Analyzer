import re
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path


def score_color(s):
    v = s * 10 if s <= 10 else s
    return "#1EA672" if v >= 80 else "#D97706" if v >= 60 else "#E25950"


def _radar(scores):
    labels = [k.replace("_", " ").title() for k in scores]
    values = list(scores.values())
    fig = go.Figure(go.Scatterpolar(
        r=values + [values[0]], theta=labels + [labels[0]],
        fill="toself", fillcolor="rgba(99,91,255,0.08)",
        line=dict(color="#635BFF", width=2),
        marker=dict(size=5, color="#635BFF"),
        hovertemplate="%{theta}: <b>%{r}/10</b><extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0,10], tickvals=[2,4,6,8,10],
                           gridcolor="#E3E8EF", linecolor="#E3E8EF",
                           tickfont=dict(color="#697386", size=9, family="Inter")),
            angularaxis=dict(gridcolor="#E3E8EF", linecolor="#E3E8EF",
                            tickfont=dict(color="#0A2540", size=10, family="Inter")),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=20, r=20), height=220,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _parse_transcript(path):
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


def render_detail_panel(call, transcript_path):
    ev  = call["evaluation"]
    sc  = call["score"]
    col = score_color(sc)

    # Close button
    if st.button("← Back", key="close_detail"):
        st.session_state.selected_call = None
        st.rerun()

    # Score hero
    sentiment = ev.get("customer_sentiment", "—")
    outcome   = ev.get("call_outcome", "—")
    lang      = call.get("lang", "en")
    fc        = call["flag_count"]

    st.markdown(
        f"<div style='font-size:11px;color:#697386;margin-bottom:2px;font-family:Inter,sans-serif'>{call['call_id']}</div>"
        f"<div style='font-size:16px;font-weight:600;color:#0A2540;margin-bottom:8px;font-family:Inter,sans-serif'>{call['advisor']} × {call['customer']}</div>",
        unsafe_allow_html=True)

    sc_col, meta_col = st.columns([1, 2])
    with sc_col:
        st.markdown(
            f"<div style='font-size:48px;font-weight:700;color:{col};letter-spacing:-2px;line-height:1;font-family:Inter,sans-serif'>"
            f"{sc}<span style='font-size:14px;color:#B0B7C3;font-weight:400'>/100</span></div>",
            unsafe_allow_html=True)
    with meta_col:
        st.markdown(
            f"<div style='margin-top:10px'>"
            f"<div style='height:5px;background:#E3E8EF;border-radius:3px;overflow:hidden;margin-bottom:6px'>"
            f"<div style='width:{sc}%;height:5px;background:{col};border-radius:3px'></div></div>"
            f"<span style='font-size:11px;color:#697386;font-family:Inter,sans-serif'>LANG: "
            f"<span style='color:#D97706;font-weight:500'>{lang.upper()}</span></span>"
            f"</div>", unsafe_allow_html=True)

    # Stat cards — full text, no truncation
    sent_col = "#1EA672" if "positive" in sentiment.lower() else "#D97706" if "neutral" in sentiment.lower() else "#E25950"
    f_col    = "#E25950" if fc else "#1EA672"
    f_bg     = "#FFF1F0" if fc else "#ECFDF5"

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:12px 0;font-family:Inter,sans-serif">
        <div style="background:#F6F9FC;border:1px solid #E3E8EF;border-radius:8px;padding:10px 12px">
            <div style="font-size:9px;font-weight:600;color:#697386;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">Sentiment</div>
            <div style="font-size:12px;font-weight:500;color:{sent_col};word-wrap:break-word">{sentiment}</div>
        </div>
        <div style="background:{f_bg};border:1px solid #E3E8EF;border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:9px;font-weight:600;color:#697386;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">Flags</div>
            <div style="font-size:18px;font-weight:700;color:{f_col}">{fc if fc else '✓'}</div>
        </div>
        <div style="background:#F6F9FC;border:1px solid #E3E8EF;border-radius:8px;padding:10px 12px">
            <div style="font-size:9px;font-weight:600;color:#697386;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px">Outcome</div>
            <div style="font-size:11px;color:#0A2540;word-wrap:break-word;line-height:1.4">{outcome}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Audio
    audio_path = call.get("audio_path")
    if audio_path and Path(str(audio_path)).exists():
        st.markdown(
            "<div style='font-size:10px;font-weight:600;color:#697386;text-transform:uppercase;"
            "letter-spacing:.5px;margin-bottom:5px;font-family:Inter,sans-serif'>Recording</div>",
            unsafe_allow_html=True)
        with open(audio_path, "rb") as f:
            st.audio(f.read(), format=f"audio/{Path(str(audio_path)).suffix.lstrip('.')}")

    # Tabs
    tabs = st.tabs(["Timeline", "Scores", "Transcript", "Flags"])

    # ── Timeline ──────────────────────────────────────────────────────────────
    with tabs[0]:
        strengths    = ev.get("strengths", [])
        improvements = ev.get("improvements", [])
        red_flags    = ev.get("red_flags", [])
        timeline     = []
        for s in strengths:
            timeline.append({"type":"s","title":s.get("title",""),"ts":s.get("timestamp",""),"detail":s.get("evidence","")})
        for i in improvements:
            timeline.append({"type":"i","title":i.get("title",""),"ts":i.get("timestamp",""),"detail":i.get("suggestion","")})
        for f in red_flags:
            timeline.append({"type":"f","title":f.get("statement",f.get("title","")),"ts":f.get("timestamp",""),"detail":f.get("reason","")})

        summary = ev.get("summary", "")
        if summary:
            st.markdown(
                f"<div style='font-size:12px;color:#697386;line-height:1.7;background:#F6F9FC;"
                f"border:1px solid #E3E8EF;border-radius:8px;padding:12px;margin-bottom:14px;"
                f"font-family:Inter,sans-serif;word-wrap:break-word'>{summary}</div>",
                unsafe_allow_html=True)

        for item in timeline:
            if item["type"] == "s":   dc, ic = "#1EA672", "✓"
            elif item["type"] == "i": dc, ic = "#D97706", "→"
            else:                     dc, ic = "#E25950", "!"

            st.markdown(f"""
            <div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid #F6F9FC;font-family:Inter,sans-serif">
                <div style="width:18px;height:18px;border-radius:50%;border:2px solid {dc};
                    display:flex;align-items:center;justify-content:center;font-size:9px;
                    font-weight:700;color:{dc};flex-shrink:0;margin-top:2px">{ic}</div>
                <div style="flex:1;min-width:0">
                    <div style="font-size:13px;font-weight:500;color:#0A2540;word-wrap:break-word">{item['title']}</div>
                    <div style="font-size:11px;color:#B0B7C3;margin-top:1px">{item['ts']}</div>
                    <div style="font-size:12px;color:#697386;margin-top:3px;line-height:1.5;word-wrap:break-word">{item['detail']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Scores ────────────────────────────────────────────────────────────────
    with tabs[1]:
        scores = ev.get("category_scores", {})
        if scores:
            _radar(scores)
            bars = "".join(
                f"<div style='display:flex;align-items:center;gap:10px;margin:5px 0;font-family:Inter,sans-serif'>"
                f"<span style='width:130px;font-size:11px;color:#697386'>{k.replace('_',' ').title()}</span>"
                f"<div style='flex:1;height:4px;background:#E3E8EF;border-radius:2px'>"
                f"<div style='width:{v*10}%;height:4px;background:{score_color(v)};border-radius:2px'></div></div>"
                f"<span style='font-size:12px;font-weight:600;color:{score_color(v)};width:24px'>{v}</span></div>"
                for k, v in scores.items()
            )
            st.markdown(f"<div>{bars}</div>", unsafe_allow_html=True)

    # ── Transcript ────────────────────────────────────────────────────────────
    with tabs[2]:
        lines = _parse_transcript(transcript_path)
        if not lines:
            st.markdown("<span style='color:#697386;font-size:13px'>No transcript found</span>", unsafe_allow_html=True)
        else:
            for l in lines:
                is_adv = l["role"] == "Advisor"
                st.markdown(
                    f"<div style='display:flex;justify-content:{'flex-start' if is_adv else 'flex-end'};margin-bottom:10px'>"
                    f"<div style='max-width:90%;padding:8px 12px;border-radius:8px;"
                    f"background:{'#F6F9FC' if is_adv else '#0A2540'};"
                    f"border:1px solid {'#E3E8EF' if is_adv else '#0A2540'}'>"
                    f"<div style='font-size:10px;color:#697386;margin-bottom:3px;font-family:Inter,sans-serif'>{l['name']} · {l['timestamp']}</div>"
                    f"<div style='font-size:13px;color:{'#0A2540' if is_adv else '#fff'};line-height:1.5;font-family:Inter,sans-serif;word-wrap:break-word'>{l['text']}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True)

    # ── Flags ─────────────────────────────────────────────────────────────────
    with tabs[3]:
        red_flags = ev.get("red_flags", [])
        if not red_flags:
            st.markdown(
                "<div style='display:flex;align-items:center;gap:8px;background:#ECFDF5;"
                "border:1px solid #D1FAE5;border-radius:8px;padding:12px 16px;font-family:Inter,sans-serif'>"
                "<span style='font-size:18px'>✓</span>"
                "<span style='font-size:13px;font-weight:500;color:#1EA672'>No flags — clean call</span>"
                "</div>", unsafe_allow_html=True)
        else:
            for flag in red_flags:
                sev     = flag.get("severity", "Medium")
                is_high = sev.lower() == "high"
                bc      = "#E25950" if is_high else "#D97706"
                bg      = "#FFF1F0" if is_high else "#FFF8EC"
                brd     = "#FECACA" if is_high else "#FDE68A"
                stmt    = flag.get("statement", flag.get("title", ""))
                reason  = flag.get("reason", flag.get("description", ""))
                ts      = flag.get("timestamp", "")
                st.markdown(
                    f"<div style='background:{bg};border:1px solid {brd};border-left:3px solid {bc};"
                    f"border-radius:0 8px 8px 0;padding:12px 14px;margin-bottom:10px;font-family:Inter,sans-serif'>"
                    f"<div style='font-size:10px;font-weight:600;color:{bc};text-transform:uppercase;letter-spacing:.5px;margin-bottom:5px'>{sev} · {ts}</div>"
                    f"<div style='font-size:13px;font-weight:500;color:#0A2540;margin-bottom:4px;word-wrap:break-word'>{stmt}</div>"
                    f"<div style='font-size:12px;color:#697386;line-height:1.5;word-wrap:break-word'>{reason}</div></div>",
                    unsafe_allow_html=True)