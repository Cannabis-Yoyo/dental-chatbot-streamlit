# Utils module
import streamlit as st

def _auto_hide_nav():
    hide_css = """
    <style>
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavSeparator"] {
            display: none !important;
        }
    </style>
    """
    st.markdown(hide_css, unsafe_allow_html=True)

_auto_hide_nav()
