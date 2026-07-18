import streamlit as st


def render_nav(all_calls: list) -> str:
    avg         = round(sum(c["score"] for c in all_calls)/len(all_calls)) if all_calls else 0
    total_flags = sum(c["flag_count"] for c in all_calls)
    need_attn   = len([c for c in all_calls if c["score"] < 60])

    # Compact top bar — logo + stats on one line
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:10px 0 8px;border-bottom:1px solid #E3E8EF;margin-bottom:10px">
        <span style="font-size:15px;font-weight:700;color:#0A2540;letter-spacing:-.3px;
                     font-family:Inter,sans-serif">
            <span style="color:#635BFF">Sales</span>CallIQ
        </span>
        <span style="font-size:11px;color:#697386;font-family:Inter,sans-serif">
            {len(all_calls)} calls &nbsp;·&nbsp;
            <span style="color:#D97706">Avg {avg}</span> &nbsp;·&nbsp;
            <span style="color:#E25950">{total_flags} flags</span> &nbsp;·&nbsp;
            <span style="color:#E25950">{need_attn} need attention</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Nav buttons — same row as KPIs
    nav1, nav2, kpi1, kpi2, kpi3, kpi4 = st.columns([1, 1, 1, 1, 1, 1])

    with nav1:
        is_ov = st.session_state.page == "overview"
        if st.button("Overview", use_container_width=True,
                     type="primary" if is_ov else "secondary"):
            st.session_state.page = "overview"
            st.session_state.selected_call = None
            st.rerun()

    with nav2:
        is_up = st.session_state.page == "upload"
        if st.button("Upload Call", use_container_width=True,
                     type="primary" if is_up else "secondary"):
            st.session_state.page = "upload"
            st.session_state.selected_call = None
            st.rerun()

    def kpi_box(col, label, val, color, sub, sub_color="#697386"):
        col.markdown(
            f"<div style='padding:6px 8px 6px 16px;border-left:1px solid #E3E8EF;font-family:Inter,sans-serif'>"
            f"<div style='font-size:9px;font-weight:600;color:#697386;text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px'>{label}</div>"
            f"<div style='font-size:18px;font-weight:700;color:{color};letter-spacing:-1px;line-height:1'>{val}</div>"
            f"<div style='font-size:10px;color:{sub_color};margin-top:1px'>{sub}</div>"
            f"</div>",
            unsafe_allow_html=True)

    kpi_box(kpi1, "Calls", len(all_calls), "#0A2540", "Total analyzed")
    kpi_box(kpi2, "Avg Score", f"{avg}", "#D97706" if avg < 80 else "#1EA672",
            "Needs improvement" if avg < 80 else "On track",
            "#D97706" if avg < 80 else "#1EA672")
    kpi_box(kpi3, "Flags", total_flags, "#E25950" if total_flags else "#1EA672",
            "Issues found", "#E25950" if total_flags else "#1EA672")
    kpi_box(kpi4, "Attention", need_attn, "#E25950" if need_attn else "#1EA672",
            "Below 60", "#E25950" if need_attn else "#697386")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    return st.session_state.page