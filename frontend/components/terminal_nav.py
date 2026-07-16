import streamlit as st


def render_nav(all_calls: list) -> str:
    avg         = round(sum(c["score"] for c in all_calls) / len(all_calls)) if all_calls else 0
    total_flags = sum(c["flag_count"] for c in all_calls)
    need_attn   = len([c for c in all_calls if c["score"] < 60])

    st.markdown(f"""
    <div style="background:#111;border-bottom:1px solid #333;padding:10px 16px;
                display:flex;align-items:center;margin-bottom:8px;
                font-family:'Courier New',monospace">
        <span style="color:#4CAF50;font-size:15px;font-weight:700;margin-right:2px">Sales</span>
        <span style="color:#E8E8E8;font-size:15px;font-weight:700;margin-right:28px">CallIQ</span>
        <span style="color:#555;font-size:13px">
            {len(all_calls)} calls &nbsp;·&nbsp;
            <span style="color:#F59E0B">avg {avg}</span> &nbsp;·&nbsp;
            <span style="color:#E74C3C">{total_flags} flags</span> &nbsp;·&nbsp;
            <span style="color:#E74C3C">{need_attn} need attention</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, spacer = st.columns([1, 1, 6])
    with col1:
        if st.button(
            "[ overview ]",
            use_container_width=True,
            type="primary" if st.session_state.page == "overview" else "secondary",
        ):
            st.session_state.page = "overview"
            st.session_state.selected_call = None
            st.rerun()
    with col2:
        if st.button(
            "[ upload_call ]",
            use_container_width=True,
            type="primary" if st.session_state.page == "upload" else "secondary",
        ):
            st.session_state.page = "upload"
            st.session_state.selected_call = None
            st.rerun()

    return st.session_state.page