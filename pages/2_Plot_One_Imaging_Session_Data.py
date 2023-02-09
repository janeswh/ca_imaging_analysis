import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from stqdm import stqdm
import pdb


def set_webapp_params():
    """
    Sets the name of the Streamlit app along with other things
    """
    st.set_page_config(page_title="Plot One Imaging Session Data")
    st.title("Plot data from one imaging session")

    st.markdown(
        "Please select the .xlsx file containing the mean amplitudes that you "
        "want to plot. The file should be named in the format "
        "YYMMDD--123456-7-8_ROIX_avg_means.xlsx."
    )


def main():
    set_webapp_params()

    # # # --- Initialising SessionState ---
    if "browsed" not in st.session_state:
        st.session_state.browsed = False
    if "plots_list" not in st.session_state:
        st.session_state.plots_list = False
    if "selected_sample" not in st.session_state:
        st.session_state.selected_sample = False

    uploaded_file = st.file_uploader(
        label="Choose a file", label_visibility="collapsed"
    )

    if uploaded_file:
        # reads avg means into dict, with sheet names/sample # as keys, df
        # as values
        avg_means_dict = pd.read_excel(uploaded_file, sheet_name=None)
        st.info(
            f"Avg means loaded successfully for {len(avg_means_dict)} samples"
            "."
        )

        st.session_state.browsed = True

        if st.button("Plot data"):
            # or st.session_state.selected_sample:
            # if plots haven't been generated yet, generate them
            # if st.session_state.plots_list is False:
            plots_list = {}

            # adds progress bar
            bar = stqdm(avg_means_dict.items(), desc="Plotting ")
            for sample, avg_means_df in bar:
                fig = px.line(
                    avg_means_df,
                    x="Frame",
                    y=avg_means_df.columns[1:],
                    labels={
                        "value": "Mean amplitude",
                        "variable": "Odor Number",
                    },
                )

                bar.set_description(f"Plotting {sample}", refresh=True)
                plots_list[sample] = fig

            st.info("All plots generated.")
            st.session_state.plots_list = plots_list

        if st.session_state.plots_list:
            st.session_state.selected_sample = st.select_slider(
                "Select sample number to display its " "corresponding plot:",
                options=avg_means_dict.keys(),
            )

            if st.session_state.selected_sample:
                st.plotly_chart(
                    st.session_state.plots_list[
                        st.session_state.selected_sample
                    ]
                )

        # st.session_state.plots_list = False

    # pdb.set_trace()


if __name__ == "__main__":
    main()
