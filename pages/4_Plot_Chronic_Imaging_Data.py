import streamlit as st
import pandas as pd
from math import nan
from datetime import datetime
from collections import defaultdict
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
    st.set_page_config(page_title="Plot Chronic Imaging Data")
    st.title("Plot data from chronic imaging sessions")

    st.markdown(
        "Please select the .xlsx files containing the response properties that you "
        "want to plot. The files should be named in the format "
        "YYMMDD--123456-7-8_ROIX_analysis.xlsx."
    )


def set_color_scales():
    """
    Creates fixed color scales used for plotting
    """

    #  this creates color scales for 6 animals with 2 ROIs each
    colorscale = {
        "marker": {
            1: "#a2ffff",
            2: "#7ee9ff",
            3: "#57caff",
            4: "#24acff",
            5: "#008ee3",
            6: "#0072c4",
            7: "#0057a5",
            8: "#003e87",
            9: "#00266b",
            10: "rgba(0, 15, 79, 0.5)"
            # 10: "#000f4f",
        },
        "lines": "#000f4f",
    }

    return colorscale


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
    if "animal_id" not in st.session_state:
        st.session_state.animal_id = False
    if "interval" not in st.session_state:
        st.session_state.interval = False
    if "sig_data" not in st.session_state:
        st.session_state.sig_data = False
    if "sorted_dates" not in st.session_state:
        st.session_state.sorted_dates = False
    if "sig_odors" not in st.session_state:
        st.session_state.sig_odors = False
    if "nosig_exps" not in st.session_state:
        st.session_state.no_sig_exps = False

    # assigns a color to each exp session with significant responses
    if "sig_exp_colors" not in st.session_state:
        st.session_state.sig_exp_colors = False

    if "plots_list" not in st.session_state:
        st.session_state.plots_list = False
    if "selected_odor" not in st.session_state:
        st.session_state.selected_odor = False

    # measures to plot
    st.session_state.measures = [
        "Blank-subtracted DeltaF/F(%)",
        "Area under curve",
        "Latency (s)",
        "Time to peak (s)",
    ]

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
    # makes list to hold all file names for ordering
    all_exps = []

    # makes list to hold exp names with no significant data
    nosig_exps = []
    # makes list to hold all significant odors
    all_sig_odors = []

    # makes dict to hold data from all significant odors
    sig_data_dict = {}

    # gets animal and ROI ID
    st.session_state.animal_id = (
        f"{st.session_state.files[0].name.split('_')[1]}_"
        f"{st.session_state.files[0].name.split('_')[2]}"
    )

    # sort files by date
    sorted_files = sorted(
        st.session_state.files,
        key=lambda file: datetime.strptime(file.name.split("_")[0], "%y%m%d"),
    )

    st.session_state.files = sorted_files

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
        all_exps.append(exp_name)

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

        if not sig_data_df.empty:
            sig_data_dict[exp_name] = sig_data_df
        if sig_data_df.empty:
            nosig_exps.append(exp_name)

    return nosig_exps, all_sig_odors, sig_data_dict, all_exps


def get_odor_data(odor):
    """
    Collects the data for odors with significant responses
    """

    # makes list of experiments that have sig responses for
    # the odor
    sig_odor_exps = []

    for experiment in st.session_state.sig_data.keys():
        if odor in st.session_state.sig_data[experiment]:
            sig_odor_exps.append(experiment)

    total_sessions = len(sig_odor_exps)

    return sig_odor_exps, total_sessions


def get_plot_params(all_roi_counts):
    """
    Counts the number of ROIs (columns) and animals plotted for each odor
    """

    # determines whether plot has groups for multiple ROI
    # also counts total number of columns - if groups are present,
    # animals with one ROI still have two columns

    if 2 in all_roi_counts:
        plot_groups = True
        zeroes = all_roi_counts.count(0)
        total_cols = (len(all_roi_counts) - zeroes) * 2

    else:
        plot_groups = False
        total_cols = sum(all_roi_counts)

    return plot_groups, total_cols


def position_mean_line(total_sessions, interval_ct):
    """
    Sets the positioning values for mean lines depending on whether each
    animal has multiple ROIs.
    """

    start = (1 / total_sessions) / 3.5
    line_width = (1 / total_sessions) / 3
    between_group_interval = (1 / total_sessions) / 1.4

    session1_x0 = start
    session1_x1 = start + line_width

    # sets positioning variable depending on total sessions and exp count

    # # this is for the very first data point
    if interval_ct == 1:
        x0 = session1_x0
        x1 = session1_x1

    # for subsequent data points
    else:
        x0 = (
            session1_x1
            + (interval_ct * (between_group_interval))
            + (interval_ct - 1) * line_width
        )

        x1 = x0 + line_width

    return x0, x1


def plot_odor_measure_fig(
    total_sessions,
    sig_odor_exps,
    odor,
    measure,
    color_scale,
):
    """
    Plots the analysis values for specified odor and measurement
    """
    measure_fig = go.Figure()

    # generates list holding the mean values for plotting later
    avgs = [0] * len(st.session_state.sorted_dates)

    for exp_ct, sig_experiment in enumerate(sig_odor_exps):
        # gets the timepoint position of the experiment
        interval_ct = st.session_state.sorted_dates.index(sig_experiment) + 1

        exp_odor_df = st.session_state.sig_data[sig_experiment][odor]

        # checks whether values need to be put in artificial list
        if isinstance(exp_odor_df.loc[measure], pd.Series):
            x = [interval_ct] * len(exp_odor_df.loc[measure].values)
            y = exp_odor_df.loc[measure].values.tolist()
        else:
            x = [interval_ct]
            y = [exp_odor_df.loc[measure]]

        measure_fig.add_trace(
            go.Box(
                x=x,
                y=y,
                line=dict(color="rgba(0,0,0,0)"),
                fillcolor="rgba(0,0,0,0)",
                boxpoints="all",
                pointpos=0,
                marker_color=color_scale["marker"][interval_ct],
                marker=dict(
                    # opacity=0.5,
                    line=dict(
                        color=color_scale["lines"],
                        width=2,
                    ),
                    size=12,
                ),
                name=sig_experiment,
                legendgroup=exp_ct,
            ),
        )

        # only adds mean line if there is more than one pt per exp
        if isinstance(exp_odor_df.loc[measure], pd.Series):
            # adds mean value to list for plotting
            avgs[interval_ct - 1] = exp_odor_df.loc[measure].values.mean()
        #     measure_fig = add_mean_line(
        #         measure_fig,
        #         total_sessions,
        #         color_scale,
        #         measure,
        #         exp_odor_df,
        #         interval_ct,
        #     )

    # makes x-axis values for mean trace
    x_vals = list(range(1, len(st.session_state.sorted_dates) + 1))

    # only adds mean line if there is more than one significant session
    # if len(sig_odor_exps) > 1:
    measure_fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=avgs,
            mode="lines",
            line=dict(color="orange"),
            name="Mean",
        )
    )

    return measure_fig


def add_mean_line(
    fig, total_sessions, color_scale, measure, exp_odor_df, interval_ct
):
    """
    Adds mean line to each dataset
    """
    x0, x1 = position_mean_line(total_sessions, interval_ct)

    fig.add_shape(
        type="line",
        line=dict(
            color=color_scale["lines"],
            width=4,
        ),
        xref="x domain",
        x0=x0,
        x1=x1,
        y0=exp_odor_df.loc[measure].values.mean(),
        y1=exp_odor_df.loc[measure].values.mean(),
    )

    return fig


def format_fig(fig, measure):
    """
    Formats the legend, axes, and titles of the fig
    """
    #  below is code from stack overflow to hide duplicate legends
    names = set()
    fig.for_each_trace(
        lambda trace: trace.update(showlegend=False)
        if (trace.name in names)
        else names.add(trace.name)
    )

    fig.update_xaxes(
        showticklabels=True,
        title_text=f"<br />{st.session_state.interval}",
        tickvals=list(range(1, len(st.session_state.sorted_dates) + 1)),
        range=[0.5, len(st.session_state.sorted_dates) + 1],
    )

    fig.update_yaxes(
        title_text=measure,
    )

    if measure == "Time to peak (s)":
        fig.update_yaxes(
            rangemode="tozero",
        )

    fig.update_layout(
        # boxmode="group",
        # boxgap=0.4,
        title={
            "text": measure,
            "x": 0.4,
            "xanchor": "center",
        },
        legend_title_text="Experiment ID<br />",
        showlegend=True,
    )

    return fig


def generate_plots():
    """
    Creates plots for each odor
    """

    plots_list = defaultdict(dict)

    color_scale = set_color_scales()

    # adds progress bar
    odor_bar = stqdm(st.session_state.sig_odors, desc="Plotting ")

    for odor in odor_bar:
        sig_odor_exps, total_sessions = get_odor_data(odor)

        # plot_groups, total_cols = get_plot_params(all_roi_counts)

        for measure in st.session_state.measures:
            measure_fig = plot_odor_measure_fig(
                total_sessions,
                sig_odor_exps,
                odor,
                measure,
                color_scale,
            )

            measure_fig = format_fig(measure_fig, measure)

            plots_list[odor][measure] = measure_fig

        odor_bar.set_description(f"Plotting {odor}", refresh=True)

    st.info("All plots generated.")
    if len(st.session_state.nosig_exps) != 0:
        st.warning(
            "No plots have been generated for the "
            "following experiments due to the lack of significant "
            "odor responses: \n"
            f"{st.session_state.nosig_exps}"
        )

    st.session_state.plots_list = plots_list


def display_plots():
    """
    Displays the plots for the selected odor
    """
    for measure in st.session_state.measures:
        st.plotly_chart(
            st.session_state.plots_list[st.session_state.selected_odor][
                measure
            ]
        )


def check_sig_odors(odors_list):
    """
    Checks significant odor responses from loaded data and puts them in a list
    """
    # flatten list of odors
    flat_odors_list = [odor for sublist in odors_list for odor in sublist]

    if len(st.session_state.nosig_exps) == len(st.session_state.files):
        st.error(
            "None of the uploaded experiments have significant "
            " odor responses. Please upload data for experiments with "
            " significant responses to plot the response measurements."
        )
        # st.session_state.load_data = False
    else:
        # gets unique significant odors and puts them in order
        st.session_state.sig_odors = list(dict.fromkeys(flat_odors_list))
        st.session_state.sig_odors.sort()


def main():
    set_webapp_params()
    initialize_states()

    if st.session_state.files or st.session_state.load_data:
        if st.button("Load data"):
            st.session_state.load_data = True

            (
                st.session_state.nosig_exps,
                odors_list,
                st.session_state.sig_data,
                st.session_state.sorted_dates,
            ) = import_data()

            st.info(
                f"Response data loaded successfully for "
                f"{len(st.session_state.files)} experiments from "
                f"animal ID {st.session_state.animal_id}."
            )

            check_sig_odors(odors_list)

            # if load data is clicked again, doesn't display plots/slider
            st.session_state.plots_list = False

        # select interval type if load data has been clicked
        if st.session_state.load_data:
            st.session_state.interval = st.radio(
                "Select timepoint interval:", ("Day", "Week", "Session")
            )

        # if data has been loaded, always show plotting buttons
        if st.session_state.load_data and len(
            st.session_state.nosig_exps
        ) != len(st.session_state.files):
            if st.button("Plot data"):
                generate_plots()

            # display slider and plots if plots have already been generated
            # even if Plot data isn't clicked again
            if st.session_state.plots_list:
                st.session_state.selected_odor = st.selectbox(
                    "Select odor number to display its corresponding plots:",
                    options=st.session_state.sig_odors,
                )

                if st.session_state.selected_odor:
                    display_plots()


if __name__ == "__main__":
    main()
