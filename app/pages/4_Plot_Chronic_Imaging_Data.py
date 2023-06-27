from src.utils import (
    make_pick_folder_button,
    pop_folder_selector,
    get_odor_data,
    sort_measurements_df,
    check_sig_odors,
)

from src.experiment import ExperimentFile

from src.plotting import set_color_scales

import streamlit as st
import pandas as pd
from math import nan
from datetime import datetime
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go


import plotly.io as pio

pio.templates.default = "plotly_white"

from stqdm import stqdm


def set_webapp_params():
    """
    Sets the name of the Streamlit app along with other things
    """
    st.set_page_config(page_title="Plot Chronic Imaging Data")
    st.title("Plot data from chronic imaging sessions")

    st.markdown(
        "Please select the folder where you want to save the summary "
        ".xlsx file"
    )

    clicked = make_pick_folder_button()

    if clicked:
        st.session_state.dir_path = pop_folder_selector()

    if st.session_state.dir_path:
        st.write("Summary .xlsx file will be saved to:")
        st.info(st.session_state.dir_path)

    st.markdown(
        "Please select the .xlsx files containing the response properties that you "
        "want to plot. The files should be named in the format "
        "YYMMDD--123456-7-8_ROIX_analysis.xlsx."
    )

    st.session_state.files = st.file_uploader(
        label="Choose files",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )


def initialize_states():
    """
    Initializes session state variables
    """

    # # # --- Initialising SessionState ---
    if "dir_path" not in st.session_state:
        st.session_state.dir_path = False
    # makes the avg_means data persist
    if "files" not in st.session_state:
        st.session_state.files = False
    # checks whether Load data was clicked
    if "pg4_load_data" not in st.session_state:
        st.session_state.pg4_load_data = False
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

    if "pg4_plots_list" not in st.session_state:
        st.session_state.pg4_plots_list = False
    if "selected_odor" not in st.session_state:
        st.session_state.selected_odor = False

    # measures to plot
    st.session_state.measures = [
        "Blank-subtracted DeltaF/F(%)",
        "Blank sub AUC",
        "Latency (s)",
        "Time to peak (s)",
    ]


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

    # makes df for each measurement, for summary csv
    blank_sub_df = pd.DataFrame()
    auc_df = pd.DataFrame()
    latency_df = pd.DataFrame()
    ttpeak_df = pd.DataFrame()

    df_list = [blank_sub_df, auc_df, latency_df, ttpeak_df]

    # adds progress bar
    load_bar = stqdm(st.session_state.files, desc="Loading ")
    for file in load_bar:
        timepoint = ExperimentFile(file, df_list, chronic=True)
        all_exps.append(timepoint.exp_name)

        load_bar.set_description(
            f"Loading data from {timepoint.exp_name}", refresh=True
        )
        timepoint.import_excel()
        timepoint.sort_data()

        timepoint.make_plotting_dfs()

        all_sig_odors.append(timepoint.sig_odors)

        if not timepoint.sig_data_df.empty:
            sig_data_dict[timepoint.exp_name] = timepoint.sig_data_df
        if timepoint.sig_data_df.empty:
            nosig_exps.append(timepoint.exp_name)

    sort_measurements_df(
        st.session_state.dir_path,
        "compiled_dataset_analysis.xlsx",
        df_list,
        timepoint.sample_type,
        st.session_state.measures,
        chronic=True,
        animal_id=st.session_state.animal_id,
    )

    return nosig_exps, all_sig_odors, sig_data_dict, all_exps


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
    # fills non-sig sessions with 0 or nan depending on measure

    if measure == "Blank-subtracted DeltaF/F(%)" or measure == "Blank sub AUC":
        avgs = [0] * len(st.session_state.sorted_dates)
    elif measure == "Latency (s)" or measure == "Time to peak (s)":
        avgs = [nan] * len(st.session_state.sorted_dates)

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

        # only adds mean value to list for plotting if
        # there is more than one pt per exp
        if isinstance(exp_odor_df.loc[measure], pd.Series):
            avgs[interval_ct - 1] = exp_odor_df.loc[measure].values.mean()

    # makes x-axis values for mean trace
    x_vals = list(range(1, len(st.session_state.sorted_dates) + 1))

    # adds mean line
    measure_fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=avgs,
            mode="lines",
            line=dict(color="orange", dash="dot"),
            name="Mean",
        )
    )

    # adds mean point dots for latency and time to peak
    if measure == "Latency (s)" or measure == "Time to peak (s)":
        measure_fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=avgs,
                mode="markers",
                marker=dict(color="orange"),
                name="Single Mean",
            )
        )

    return measure_fig


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

    color_scale = set_color_scales("chronic")

    # adds progress bar
    odor_bar = stqdm(st.session_state.sig_odors, desc="Plotting ")

    for odor in odor_bar:
        odor_data = get_odor_data(odor, "chronic", st.session_state.sig_data)
        sig_odor_exps = odor_data[0]
        total_sessions = odor_data[1]

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

    st.session_state.pg4_plots_list = plots_list


def display_plots():
    """
    Displays the plots for the selected odor
    """
    for measure in st.session_state.measures:
        st.plotly_chart(
            st.session_state.pg4_plots_list[st.session_state.selected_odor][
                measure
            ]
        )


def main():
    initialize_states()
    set_webapp_params()

    # checks that all the uploaded files are correct
    for file in st.session_state.files:
        if "_analysis" not in file.name:
            st.error(
                "Please make sure all uploaded files end in '_analysis.xlsx'"
            )
            st.session_state.files = False
            st.session_state.pg4_load_data = False

    if st.session_state.files or st.session_state.pg4_load_data:
        if st.button("Load data"):
            st.session_state.pg4_load_data = True

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

            st.session_state.sig_odors = check_sig_odors(odors_list)

            # if load data is clicked again, doesn't display plots/slider
            st.session_state.pg4_plots_list = False

        # select interval type if load data has been clicked
        if st.session_state.pg4_load_data:
            st.session_state.interval = st.radio(
                "Select timepoint interval:", ("Day", "Week", "Session")
            )

        # if data has been loaded, always show plotting buttons
        if st.session_state.pg4_load_data and len(
            st.session_state.nosig_exps
        ) != len(st.session_state.files):
            if st.button("Plot data"):
                generate_plots()

            # display slider and plots if plots have already been generated
            # even if Plot data isn't clicked again
            if st.session_state.pg4_plots_list:
                st.session_state.selected_odor = st.selectbox(
                    "Select odor number to display its corresponding plots:",
                    options=st.session_state.sig_odors,
                )

                if st.session_state.selected_odor:
                    display_plots()


if __name__ == "__main__":
    main()
