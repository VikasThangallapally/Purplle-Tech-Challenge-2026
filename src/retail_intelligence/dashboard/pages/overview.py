import streamlit as st


def render_overview() -> None:
    st.metric("Conversion Rate", "0.0%")
    st.metric("Active Customers", 0)
