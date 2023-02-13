import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import plotly.io as pio

pio.templates.default = "plotly_white"

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


def initialize_states():
    """
    Initializes session state variables
    """

    # # # --- Initialising SessionState ---
    # makes the avg_means data persist
    if "files" not in st.session_state:
        st.session_state.files = False
    # checks whether Load data was clicked
    if "load_data" not in st.session_state:
        st.session_state.load_data = False
    if "sig_data" not in st.session_state:
        st.session_state.sig_data = False
    if "sig_odors" not in st.session_state:
        st.session_state.sig_odors = False

    if "plots_list" not in st.session_state:
        st.session_state.plots_list = False
    if "selected_sample" not in st.session_state:
        st.session_state.selected_sample = False

    st.session_state.files = st.file_uploader(
        label="Choose files",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )


def import_data():
    """
    Loads data from uploaded .xlsx files, drops non-significant response data,
    and returns only significant data and list of significant odors
    """

    # makes list to hold all significant odors
    all_sig_odors = []

    # makes dict to hold data from all significant odors
    sig_data_dict = {}

    # adds progress bar
    load_bar = stqdm(st.session_state.files, desc="Loading ")
    for file in load_bar:
        # reads avg means into dict, with sheet names/sample # as keys, df
        # as values
        exp_name = (
            file.name.split("_")[0]
            + "_"
            + file.name.split("_")[1]
            + "_"
            + file.name.split("_")[2]
        )
        load_bar.set_description(f"Loading data from {exp_name}", refresh=True)

        data_dict = pd.read_excel(
            file,
            sheet_name=None,
            header=1,
            index_col=0,
            na_values="FALSE",
            dtype="object",
        )

        sig_data_df = pd.DataFrame()

        # drop non-significant colums from each df using NaN values
        for data_df in data_dict.values():
            data_df.dropna(axis=1, inplace=True)

            # extracts measurements to plot
            data_df = data_df.loc[
                [
                    "Blank-subtracted DeltaF/F(%)",
                    "Area under curve",
                    "Latency (s)",
                    "Time to peak (s)",
                ]
            ]

            sig_data_df = pd.concat([sig_data_df, data_df], axis=1)

            # gets list of remaining significant odors
            sig_odors = data_df.columns.values.tolist()

            all_sig_odors.append(sig_odors)

        sig_data_dict[exp_name] = sig_data_df

    return all_sig_odors, sig_data_dict


def main():
    set_webapp_params()
    initialize_states()

    if st.session_state.files or st.session_state.load_data:
        if st.button("Load data"):
            st.session_state.load_data = True

            odors_list, st.session_state.sig_data = import_data()

            st.info(
                f"Response data loaded successfully for "
                f"{len(st.session_state.files)} experiments."
            )

            # flatten list of odors
            flat_odors_list = [
                odor for sublist in odors_list for odor in sublist
            ]

            # gets unique significant odors and puts them in order
            st.session_state.sig_odors = list(dict.fromkeys(flat_odors_list))
            st.session_state.sig_odors.sort()

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
            if st.button("Plot data"):
                plots_list = {}

                line_color_scale = [
                    "#D00000",
                    "#FFBA08",
                    "#3F88C5",
                    "#032B43",
                    "#136F63",
                ]

                fill_color_scale = [
                    "#FF5C5C",
                    "#FFE299",
                    "#A1C5E3",
                    "#B1DFFC",
                    "#85EADD",
                ]

                # adds progress bar
                odor_bar = stqdm(st.session_state.sig_odors, desc="Plotting ")
                for odor in odor_bar:
                    odor_fig = make_subplots(
                        rows=1,
                        cols=4,
                        horizontal_spacing=0.1,
                        x_title=odor,
                    )

                    for exp_ct, experiment in enumerate(
                        st.session_state.sig_data.keys()
                    ):
                        # gets the data for the specific odor for that exp
                        exp_odor_df = st.session_state.sig_data[experiment][
                            odor
                        ]

                        # plots one measurement per subplot
                        for measure_ct, measure in enumerate(
                            exp_odor_df.index.values
                        ):
                            odor_fig.add_trace(
                                go.Box(
                                    x=[experiment]
                                    * len(exp_odor_df.loc[measure].values),
                                    y=exp_odor_df.loc[measure].values.tolist(),
                                    line=dict(color="rgba(0,0,0,0)"),
                                    fillcolor="rgba(0,0,0,0)",
                                    boxpoints="all",
                                    pointpos=0,
                                    marker_color=fill_color_scale[exp_ct],
                                    marker=dict(
                                        line=dict(
                                            color=line_color_scale[exp_ct],
                                            width=2,
                                        ),
                                        size=12,
                                    ),
                                    name=experiment,
                                ),
                                row=1,
                                col=measure_ct + 1,
                            )

                            # add horizontal line for mean
                            line_increment = (
                                1 / (len(st.session_state.sig_data.keys()))
                            ) / 2

                            start = 0.05

                            odor_fig.add_shape(
                                type="line",
                                line=dict(
                                    color=line_color_scale[exp_ct], width=4
                                ),
                                # xref="paper",
                                # x0=exp_ct * line_increment,
                                # x1=(exp_ct * line_increment) + line_increment,
                                xref="paper",
                                x0=start + (exp_ct * line_increment),
                                x1=start
                                + (exp_ct * line_increment)
                                + line_increment,
                                y0=exp_odor_df.loc[measure].values.mean(),
                                y1=exp_odor_df.loc[measure].values.mean(),
                                row=1,
                                col=measure_ct + 1,
                            )

                            #  below is code from stack overflow to hide duplicate legends
                            names = set()
                            odor_fig.for_each_trace(
                                lambda trace: trace.update(showlegend=False)
                                if (trace.name in names)
                                else names.add(trace.name)
                            )

                            odor_fig.update_xaxes(showticklabels=False)

                            odor_fig.update_yaxes(
                                title_text=measure,
                                rangemode="tozero",
                                row=1,
                                col=measure_ct + 1,
                            )

                            # if measure == "Latency (s)":
                            #     odor_fig.update_yaxes(
                            #         rangemode="tozero",
                            #         row=1,
                            #         col=4,
                            #     )
                    odor_fig.update_layout(
                        legend_title_text="Experiment ID<br />",
                    )
                    odor_fig.show()
                    pdb.set_trace()

                    # fig = px.line(
                    #     avg_means_df,
                    #     x="Frame",
                    #     y=avg_means_df.columns[odors_to_plot],
                    #     labels={
                    #         "value": "Mean amplitude",
                    #         "variable": "Odor Number",
                    #     },
                    # )

                    # bar.set_description(f"Plotting {sample}", refresh=True)
                    # plots_list[sample] = fig

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
