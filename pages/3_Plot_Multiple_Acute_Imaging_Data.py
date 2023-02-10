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
    st.set_page_config(page_title="Plot Multiple Acute Imaging Data")
    st.title("Plot data from multiple acute imaging sessions")

    st.markdown(
        "Please select the .xlsx files containing the response properties that you "
        "want to plot. The files should be named in the format "
        "YYMMDD--123456-7-8_ROIX_analysis.xlsx."
    )


def main():
    set_webapp_params()

    # # # --- Initialising SessionState ---
    # makes the avg_means data persist
    if "data" not in st.session_state:
        st.session_state.data = False
    # checks whether Load data was clicked
    if "load_data" not in st.session_state:
        st.session_state.load_data = False
    if "plots_list" not in st.session_state:
        st.session_state.plots_list = False
    if "selected_sample" not in st.session_state:
        st.session_state.selected_sample = False

    uploaded_files = st.file_uploader(
        label="Choose files",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )

    if uploaded_files or st.session_state.load_data:
        if st.button("Load data"):
            st.session_state.load_data = True

            # makes a dict to hold data from uploaded files
            files_data_dict = {}

            for file in uploaded_files:
                pdb.set_trace()
                # reads avg means into dict, with sheet names/sample # as keys, df
                # as values
                data_dict = pd.read_excel(file, sheet_name=None)
                # st.info(
                #     f"Response data loaded successfully for {len(avg_means_dict)} samples"
                #     "."
                # )
                # uploaded_files[0].name.split('_')
                # st.session_state.data = avg_means_dict

                # # the below tries to get list of odor #s from column names
                # first_sample_df = next(iter(st.session_state.data.values()))

                # st.session_state.odor_list = [
                #     x for x in first_sample_df.columns.values if type(x) == int
                # ]

                # # if load data is clicked again, doesn't display plots/slider
                # st.session_state.plots_list = False

        # if data has been loaded, always show plotting buttons
        if st.session_state.load_data:
            if st.checkbox("Select specific odors to plot"):
                odors_to_plot = st.multiselect(
                    label="Odors to plot",
                    options=st.session_state.odor_list,
                    label_visibility="collapsed",
                )

            else:
                odors_to_plot = st.session_state.odor_list

            if st.button("Plot data"):
                plots_list = {}

                # adds progress bar
                bar = stqdm(st.session_state.data.items(), desc="Plotting ")
                for sample, avg_means_df in bar:
                    fig = px.line(
                        avg_means_df,
                        x="Frame",
                        y=avg_means_df.columns[odors_to_plot],
                        labels={
                            "value": "Mean amplitude",
                            "variable": "Odor Number",
                        },
                    )

                    bar.set_description(f"Plotting {sample}", refresh=True)
                    plots_list[sample] = fig

                st.info("All plots generated.")
                st.session_state.plots_list = plots_list

            # display slider and plots if plots have already been generated
            # even if Plot data isn't clicked again
            if st.session_state.plots_list:
                st.session_state.selected_sample = st.select_slider(
                    "Select sample number to display its "
                    "corresponding plot:",
                    options=st.session_state.data.keys(),
                )

                if st.session_state.selected_sample:
                    st.plotly_chart(
                        st.session_state.plots_list[
                            st.session_state.selected_sample
                        ]
                    )

    # pdb.set_trace()


if __name__ == "__main__":
    main()
