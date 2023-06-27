from src.utils import (
    make_pick_folder_button,
    pop_folder_selector,
    flatten,
    save_to_excel,
)

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


def set_color_scales():
    """
    Creates fixed color scales used for plotting
    """

    #  this creates color scales for 6 animals with 2 ROIs each
    colorscale = {
        "marker": {
            1: "rgba(162, 255, 255, 0.5)",
            2: "rgba(126, 233, 255, 0.5)",
            3: "rgba(87, 202, 255, 0.5)",
            4: "rgba(36, 172, 255, 0.5)",
            5: "rgba(0, 142, 227, 0.5)",
            6: "rgba(0, 114, 196, 0.5)",
            7: "rgb(0, 87, 165, 0.5)",
            8: "rgba(0, 62, 135, 0.5)",
            9: "rgba(0, 38, 107, 0.5)",
            10: "rgba(0, 15, 79, 0.5)",
            11: "rgba(162, 255, 255, 0.5)",
            12: "rgba(126, 233, 255, 0.5)",
            13: "rgba(87, 202, 255, 0.5)",
            14: "rgba(36, 172, 255, 0.5)",
            15: "rgba(0, 142, 227, 0.5)",
            16: "rgba(0, 114, 196, 0.5)",
            17: "rgb(0, 87, 165, 0.5)",
            18: "rgba(0, 62, 135, 0.5)",
            19: "rgba(0, 38, 107, 0.5)",
            20: "rgba(0, 15, 79, 0.5)"
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
        "Area under curve",
        "Latency (s)",
        "Time to peak (s)",
    ]


class TimepointFile(object):
    def __init__(self, file, df_list):
        self.file = file
        self.sample_type = None
        self.exp_name = (
            file.name.split("_")[0]
            + "_"
            + file.name.split("_")[1]
            + "_"
            + file.name.split("_")[2]
        )
        self.animal_id = file.name.split("_")[1]
        self.date = file.name.split("_")[0]
        self.roi = self.exp_name.split("_")[2]

        self.data_dict = None
        self.tuple_dict = None
        self.mega_df = None
        self.sig_data_df = None
        self.sig_odors = None

        self.df_list = df_list

    def import_excel(self):
        """
        Imports each .xlsx file into dictionary
        """

        self.data_dict = pd.read_excel(
            self.file,
            sheet_name=None,
            header=1,
            index_col=0,
            na_values="FALSE",
            dtype="object",
        )

    def sort_data(self):
        """
        Converts imported dict into dataframe for each measurement
        """
        self.tuple_dict = {
            (outerKey, innerKey): values
            for outerKey, innerDict in self.data_dict.items()
            for innerKey, values in innerDict.items()
        }

        self.mega_df = pd.DataFrame(self.tuple_dict)
        self.sample_type = self.mega_df.columns[0][0].split(" ")[0]

        # Replaces values with "" for non-sig responses
        temp_mega_df = self.mega_df.T
        temp_mega_df.loc[
            temp_mega_df["Significant response?"] == False, "Area under curve"
        ] = ""
        temp_mega_df.loc[
            temp_mega_df["Significant response?"] == False,
            "Blank-subtracted DeltaF/F(%)",
        ] = ""

        self.mega_df = temp_mega_df.copy().T

        for measure_ct, measure in enumerate(st.session_state.measures):
            temp_measure_df = (
                pd.DataFrame(self.mega_df.loc[measure]).T.stack().T
            )
            temp_measure_df["Date"] = self.date

            # Renaming sample names for better sorting
            temp_measure_df.rename(
                index=lambda x: int(x.split(" ")[1]), inplace=True
            )
            temp_measure_df.index.rename(self.sample_type, inplace=True)

            concat_pd = pd.concat([self.df_list[measure_ct], temp_measure_df])
            self.df_list[measure_ct] = concat_pd

    def make_plotting_dfs(self):
        """
        Makes the dfs used for plotting measusrements
        """
        self.sig_data_df = pd.DataFrame()
        self.sig_odors = []

        # drop non-significant colums from each df using NaN values
        for data_df in self.data_dict.values():
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

            self.sig_data_df = pd.concat([self.sig_data_df, data_df], axis=1)

            # gets list of remaining significant odors
            if len(data_df.columns.values) == 0:
                pass
            else:
                df_sig_odors = data_df.columns.values.tolist()
                self.sig_odors.append(df_sig_odors)


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
        timepoint = TimepointFile(file, df_list)
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

    save_to_excel(
        st.session_state.dir_path,
        df_list,
        timepoint.sample_type,
        st.session_state.measures,
        chronic=True,
    )

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

    if (
        measure == "Blank-subtracted DeltaF/F(%)"
        or measure == "Area under curve"
    ):
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

    color_scale = set_color_scales()

    # adds progress bar
    odor_bar = stqdm(st.session_state.sig_odors, desc="Plotting ")

    for odor in odor_bar:
        sig_odor_exps, total_sessions = get_odor_data(odor)

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


def check_sig_odors(odors_list):
    """
    Checks significant odor responses from loaded data and puts them in a list
    """
    # flatten list of odors
    flat_odors_list = flatten(odors_list)

    # flat_odors_list = [odor for sublist in odors_list for odor in sublist]

    if len(st.session_state.nosig_exps) == len(st.session_state.files):
        st.error(
            "None of the uploaded experiments have significant "
            " odor responses. Please upload data for experiments with "
            " significant responses to plot the response measurements."
        )

    else:
        # gets unique significant odors and puts them in order
        st.session_state.sig_odors = list(dict.fromkeys(flat_odors_list))
        st.session_state.sig_odors.sort()


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

            check_sig_odors(odors_list)

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
