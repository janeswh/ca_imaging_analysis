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

    st.session_state.odor_colors = {
        "Odor 1": "#1A6FF2",
        "Odor 2": "#444655",
        "Odor 3": "#A9AABC",
        "Odor 4": "#E41E4F",
        "Odor 5": "#FF6580",
        "Odor 6": "#29E990",
        "Odor 7": "#AA53C1",
        "Odor 8": "#00C7FF",
    }


def main():
    set_webapp_params()

    # # # --- Initialising SessionState ---
    # makes the avg_means data persist
    if "data" not in st.session_state:
        st.session_state.data = False
    # checks whether Load data was clicked
    if "load_data" not in st.session_state:
        st.session_state.load_data = False
    if "odor_list" not in st.session_state:
        st.session_state.load_data = False
    if "plots_list" not in st.session_state:
        st.session_state.plots_list = False
    if "selected_sample" not in st.session_state:
        st.session_state.selected_sample = False

    uploaded_file = st.file_uploader(
        label="Choose a file", label_visibility="collapsed"
    )

    if uploaded_file or st.session_state.load_data:
        if st.button("Load data"):
            st.session_state.load_data = True

            # reads avg means into dict, with sheet names/sample # as keys, df
            # as values
            avg_means_dict = pd.read_excel(uploaded_file, sheet_name=None)
            st.info(
                f"Avg means loaded successfully for {len(avg_means_dict)} samples"
                "."
            )
            st.session_state.data = avg_means_dict

            # the below tries to get list of odor #s from column names
            first_sample_df = next(iter(st.session_state.data.values()))

            st.session_state.odor_list = [
                x for x in first_sample_df.columns.values if type(x) == int
            ]

            # if load data is clicked again, doesn't display plots/slider
            st.session_state.plots_list = False

        # if data has been loaded, always show plotting buttons
        if st.session_state.load_data:
            if st.checkbox("Select specific odors to plot"):
                odors_to_plot = st.multiselect(
                    label="Odors to plot",
                    options=st.session_state.odor_list,
                    label_visibility="collapsed",
                )
                if len(odors_to_plot) == 0:
                    odors_to_plot = st.session_state.odor_list

            else:
                odors_to_plot = st.session_state.odor_list

            if st.button("Plot data"):
                plots_list = {}

                # adds progress bar
                bar = stqdm(st.session_state.data.items(), desc="Plotting ")
                for sample, avg_means_df in bar:
                    fig = go.Figure()

                    # fig = px.line(
                    #     avg_means_df,
                    #     x="Frame",
                    #     y=avg_means_df.columns[odors_to_plot],
                    #     labels={
                    #         "value": "Mean amplitude",
                    #         "variable": "Odor Number",
                    #     },
                    # )

                    for odor in odors_to_plot:
                        fig.add_trace(
                            go.Scatter(
                                x=avg_means_df["Frame"],
                                y=avg_means_df[odor],
                                line=dict(
                                    color=st.session_state.odor_colors[
                                        f"Odor {odor}"
                                    ]
                                ),
                                name=odor,
                            )
                        )

                    fig.update_xaxes(
                        title_text="Frame",
                    )

                    fig.update_yaxes(
                        title_text="Mean amplitude",
                    )

                    fig.update_layout(legend_title_text="Odor Number<br />")

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
