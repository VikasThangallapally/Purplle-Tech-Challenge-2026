import streamlit as st

from retail_intelligence.dashboard.pages.overview import render_overview


def main() -> None:
    st.set_page_config(page_title="Retail Store Intelligence", layout="wide")
    st.title("Retail Store Intelligence")
    render_overview()


if __name__ == "__main__":
    main()
