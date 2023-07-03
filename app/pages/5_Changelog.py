import streamlit as st


def show_changelog():
    # suppose that ChangeLog.md is located at the same folder as Streamlit app
    with open("../..CHANGELOG.md", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # display entries
    st.markdown("".join(lines))


show_changelog()
