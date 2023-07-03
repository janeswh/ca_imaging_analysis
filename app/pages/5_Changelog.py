import streamlit as st
from pathlib import Path
import os


def show_changelog():
    # suppose that ChangeLog.md is located at the same folder as Streamlit app
    path = Path(__file__).parents[1]
    with open(os.path.join(path, "CHANGELOG.md"), "r", encoding="utf-8") as f:
        lines = f.readlines()

    # display entries
    st.markdown("".join(lines))


show_changelog()
