import streamlit as st
import pandas as pd
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tkinter as tk
from tkinter.filedialog import askdirectory
import plotly.io as pio

pio.templates.default = "plotly_white"

from stqdm import stqdm
import os
from pathlib import Path
from natsort import natsort_keygen, natsorted
import openpyxl
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


def set_color_scales():
    """
    Creates fixed color scales used for plotting
    """

    #  this creates color scales for 6 animals with 2 ROIs each
    colorscale = {
        "marker": {
            1: ["rgba(237, 174, 73, 0.5)", "rgba(244, 206, 144, 0.5)"],
            2: ["rgba(0, 61, 91, 0.5)", "rgba(0, 109, 163, 0.5)"],
            3: ["rgba(209, 73, 91, 0.5)", "rgba(222, 124, 137, 0.5)"],
            4: ["rgba(0, 121, 140, 0.5)", "rgba(0, 177, 204, 0.5)"],
            5: ["rgba(223, 124, 82, 0.5)", "rgba(233, 164, 134, 0.5)"],
            6: ["rgba(48, 99, 142, 0.5)", "rgba(73, 139, 193, 0.5)"],
            7: ["rgba(237, 174, 73, 0.5)", "rgba(244, 206, 144, 0.5)"],
            8: ["rgba(0, 61, 91, 0.5)", "rgba(0, 109, 163, 0.5)"],
            9: ["rgba(209, 73, 91, 0.5)", "rgba(222, 124, 137, 0.5)"],
            10: ["rgba(0, 121, 140, 0.5)", "rgba(0, 177, 204, 0.5)"],
            11: ["rgba(223, 124, 82, 0.5)", "rgba(233, 164, 134, 0.5)"],
            12: ["rgba(48, 99, 142, 0.5)", "rgba(73, 139, 193, 0.5)"],
        },
        "lines": {
            1: ["#95610F", "#EDAE49"],
            2: ["#001B29", "#003D5B"],
            3: ["#621822", "#D1495B"],
            4: ["#004752", "#00798C"],
            5: ["#793416", "#DF7C52"],
            6: ["#1A354C", "#30638E"],
            7: ["#95610F", "#EDAE49"],
            8: ["#001B29", "#003D5B"],
            9: ["#621822", "#D1495B"],
            10: ["#004752", "#00798C"],
            11: ["#793416", "#DF7C52"],
            12: ["#1A354C", "#30638E"],
        },
    }

    return colorscale


class Dataset(object):
    def __init__(self, animal_id, roi):
        self.files = st.session_state.files
        self.animal_id = animal_id
        self.roi = roi
        self.sample_type = None

        # makes df for each measurement, for summary csv
        self.blank_sub_df = pd.DataFrame()
        self.auc_df = pd.DataFrame()
        self.latency_df = pd.DataFrame()
        self.ttpeak_df = pd.DataFrame()

        # df_list = [blank_sub_df, auc_df, latency_df, ttpeak_df]

    def import_data(self):
        """
        Loads data from uploaded .xlsx files, drops non-significant response data,
        and returns only significant data and list of significant odors
        """

        # makes list to hold exp names with no significant data
        nosig_exps = []

        # makes list to hold all significant odors
        all_sig_odors = []

        # makes dict to hold data from all significant odors
        sig_data_dict = {}

        # make dict to hold significant data sorted by animal id
        sorted_sig_data_dict = defaultdict(dict)

        # makes df for each measurement, for summary csv
        blank_sub_df = pd.DataFrame()
        auc_df = pd.DataFrame()
        latency_df = pd.DataFrame()
        ttpeak_df = pd.DataFrame()

        df_list = [blank_sub_df, auc_df, latency_df, ttpeak_df]

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
            animal_id = file.name.split("_")[1]
            roi = exp_name.split("_")[2]

            load_bar.set_description(
                f"Loading data from {exp_name}", refresh=True
            )

            data_dict = pd.read_excel(
                file,
                sheet_name=None,
                header=1,
                index_col=0,
                na_values="FALSE",
                dtype="object",
            )

            make_measurement_dfs(data_dict, animal_id, roi, df_list)

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
            if not sig_data_df.empty:
                sorted_sig_data_dict[animal_id][exp_name] = sig_data_df
            if sig_data_df.empty:
                nosig_exps.append(exp_name)

        sheetname_list = [
            "Blank-subtracted DeltaFF(%)",
            "Area under curve",
            "Latency (s)",
            "Time to peak (s)",
        ]

        for df_ct, df in enumerate(df_list):
            df = df.reset_index().set_index(["Animal ID", "ROI", sample_type])
            df.sort_index(inplace=True)
            df = df.reindex(sorted(df.columns), axis=1)

            xlsx_fname = f"compiled_dataset_analysis.xlsx"
            xlsx_path = Path(st.session_state.dir_path, xlsx_fname)

            sheetname = sheetname_list[df_ct]

            if os.path.isfile(xlsx_path):  # if it does, write to existing file
                # if sheet already exists, overwrite it
                with pd.ExcelWriter(
                    xlsx_path, mode="a", if_sheet_exists="replace"
                ) as writer:
                    df.to_excel(writer, sheetname)
            else:  # otherwise, write to new file
                df.to_excel(xlsx_path, sheetname)
        pdb.set_trace()

        return nosig_exps, all_sig_odors, sig_data_dict, sorted_sig_data_dict


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
    if "pg3_load_data" not in st.session_state:
        st.session_state.pg3_load_data = False
    if "sig_data" not in st.session_state:
        st.session_state.sig_data = False
    if "sorted_sig_data" not in st.session_state:
        st.session_state.sorted_sig_data = False
    if "sig_odors" not in st.session_state:
        st.session_state.sig_odors = False
    if "nosig_exps" not in st.session_state:
        st.session_state.nosig_exps = False

    # assigns a color to each exp session with significant responses
    if "sig_exp_colors" not in st.session_state:
        st.session_state.sig_exp_colors = False

    if "pg3_plots_list" not in st.session_state:
        st.session_state.pg3_plots_list = False
    if "selected_odor" not in st.session_state:
        st.session_state.selected_odor = False

    # measures to plot
    st.session_state.measures = [
        "Blank-subtracted DeltaF/F(%)",
        "Area under curve",
        "Latency (s)",
        "Time to peak (s)",
    ]


def import_data():
    """
    Loads data from uploaded .xlsx files, drops non-significant response data,
    and returns only significant data and list of significant odors
    """

    # makes list to hold exp names with no significant data
    nosig_exps = []

    # makes list to hold all significant odors
    all_sig_odors = []

    # makes dict to hold data from all significant odors
    sig_data_dict = {}

    # make dict to hold significant data sorted by animal id
    sorted_sig_data_dict = defaultdict(dict)

    # makes df for each measurement, for summary csv
    blank_sub_df = pd.DataFrame()
    auc_df = pd.DataFrame()
    latency_df = pd.DataFrame()
    ttpeak_df = pd.DataFrame()

    df_list = [blank_sub_df, auc_df, latency_df, ttpeak_df]

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
        animal_id = file.name.split("_")[1]
        roi = exp_name.split("_")[2]

        load_bar.set_description(f"Loading data from {exp_name}", refresh=True)

        data_dict = pd.read_excel(
            file,
            sheet_name=None,
            header=1,
            index_col=0,
            na_values="FALSE",
            dtype="object",
        )

        # make_measurement_dfs(data_dict, animal_id, roi, df_list)

        tuple_dict = {
            (outerKey, innerKey): values
            for outerKey, innerDict in data_dict.items()
            for innerKey, values in innerDict.items()
        }

        mega_df = pd.DataFrame(tuple_dict)
        sample_type = mega_df.columns[0][0].split(" ")[0]

        # Replaces values with "" for non-sig responses
        temp_mega_df = mega_df.T
        temp_mega_df.loc[
            temp_mega_df["Significant response?"] == False, "Area under curve"
        ] = ""
        temp_mega_df.loc[
            temp_mega_df["Significant response?"] == False,
            "Blank-subtracted DeltaF/F(%)",
        ] = ""

        mega_df = temp_mega_df.copy().T

        for measure_ct, measure in enumerate(st.session_state.measures):
            temp_measure_df = pd.DataFrame(mega_df.loc[measure]).T.stack().T
            temp_measure_df["Animal ID"] = animal_id
            temp_measure_df["ROI"] = roi

            # Renaming sample names for better sorting
            temp_measure_df.rename(
                index=lambda x: int(x.split(" ")[1]), inplace=True
            )
            temp_measure_df.index.rename(sample_type, inplace=True)

            concat_pd = pd.concat([df_list[measure_ct], temp_measure_df])
            df_list[measure_ct] = concat_pd

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
        if not sig_data_df.empty:
            sorted_sig_data_dict[animal_id][exp_name] = sig_data_df
        if sig_data_df.empty:
            nosig_exps.append(exp_name)

    sheetname_list = [
        "Blank-subtracted DeltaFF(%)",
        "Area under curve",
        "Latency (s)",
        "Time to peak (s)",
    ]

    for df_ct, df in enumerate(df_list):
        measure = st.session_state.measures[df_ct]
        df = df.reset_index().set_index(["Animal ID", "ROI", sample_type])
        df.sort_index(inplace=True)
        df = df.reindex(sorted(df.columns), axis=1)

        # drop odor 8/blank from df
        if (measure, "Odor 8") in df.columns:
            df.drop(columns=[(measure, "Odor 8")], inplace=True)

        xlsx_fname = f"compiled_dataset_analysis.xlsx"
        xlsx_path = Path(st.session_state.dir_path, xlsx_fname)

        sheetname = sheetname_list[df_ct]

        if os.path.isfile(xlsx_path):  # if it does, write to existing file
            # if sheet already exists, overwrite it
            with pd.ExcelWriter(
                xlsx_path, mode="a", if_sheet_exists="replace"
            ) as writer:
                df.to_excel(writer, sheetname)
        else:  # otherwise, write to new file
            df.to_excel(xlsx_path, sheetname)

    wb = openpyxl.load_workbook(xlsx_path)

    # Initialize formatting styles
    no_fill = openpyxl.styles.PatternFill(fill_type=None)
    side = openpyxl.styles.Side(border_style=None)
    # side = openpyxl.styles.Side(border_style="thin")
    no_border = openpyxl.styles.borders.Border(
        left=side,
        right=side,
        top=side,
        bottom=side,
    )

    # Loop through all cells in all worksheets
    for sheet in wb.worksheets:
        for row in sheet:
            for cell in row:
                # Apply colorless and borderless styles
                cell.fill = no_fill
                cell.border = no_border

    # Save workbook
    wb.save(xlsx_path)

    pdb.set_trace()

    return nosig_exps, all_sig_odors, sig_data_dict, sorted_sig_data_dict


def make_measurement_dfs(data_dict, animal_id, roi, df_list):
    """
    Collates the plotted measurements for the dataset into a big df

    """
    tuple_dict = {
        (outerKey, innerKey): values
        for outerKey, innerDict in data_dict.items()
        for innerKey, values in innerDict.items()
    }

    mega_df = pd.DataFrame(tuple_dict)
    sample_type = mega_df.columns[0][0].split(" ")[0]

    # Replaces values with "" for non-sig responses
    temp_mega_df = mega_df.T
    temp_mega_df.loc[
        temp_mega_df["Significant response?"] == False, "Area under curve"
    ] = ""
    temp_mega_df.loc[
        temp_mega_df["Significant response?"] == False,
        "Blank-subtracted DeltaF/F(%)",
    ] = ""

    mega_df = temp_mega_df.copy().T

    for measure_ct, measure in enumerate(st.session_state.measures):
        temp_measure_df = pd.DataFrame(mega_df.loc[measure]).T.stack().T
        temp_measure_df["Animal ID"] = animal_id
        temp_measure_df["ROI"] = roi

        # Renaming sample names for better sorting
        temp_measure_df.rename(
            index=lambda x: int(x.split(" ")[1]), inplace=True
        )
        temp_measure_df.index.rename(sample_type, inplace=True)

        concat_pd = pd.concat([df_list[measure_ct], temp_measure_df])
        df_list[measure_ct] = concat_pd


def get_odor_data(odor):
    """
    Collects the data for odors with significant responses
    """

    # makes list of experiments that have sig responses for
    # the odor
    sig_odor_exps = {}

    # makes list of number of ROIs per animal
    all_roi_counts = []

    for animal_id in st.session_state.sorted_sig_data:
        animal_exp_list = []

        for exp_ct, experiment in enumerate(
            st.session_state.sorted_sig_data[animal_id].keys()
        ):
            if odor in st.session_state.sorted_sig_data[animal_id][experiment]:
                animal_exp_list.append(experiment)
                sig_odor_exps[animal_id] = animal_exp_list

        roi_count = len(animal_exp_list)
        all_roi_counts.append(roi_count)

    total_animals = len(sig_odor_exps)

    return sig_odor_exps, all_roi_counts, total_animals


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


def position_mean_line(
    total_animals, total_cols, plot_groups, animal_ct, exp_ct
):
    """
    Sets the positioning values for mean lines depending on whether each
    animal has multiple ROIs.
    """

    if plot_groups:
        start = (1 / total_cols) / 1.6
        line_width = (1 / total_animals) / 6
        within_group_interval = (1 / total_animals) / 8
        between_group_interval = (1 / total_animals) / 1.95

    else:
        start = (1 / total_animals) / 3.5
        line_width = (1 / total_animals) / 3
        between_group_interval = (1 / total_animals) / 1.4

    animal1_roi1_x0 = start
    animal1_roi1_x1 = start + line_width

    if plot_groups:
        animal1_roi2_x0 = animal1_roi1_x1 + within_group_interval
        animal1_roi2_x1 = animal1_roi2_x0 + line_width

    # sets positioning variable depending on animal and exp count

    # # this is for the very first data point
    if animal_ct == 0:
        if exp_ct == 0:
            x0 = animal1_roi1_x0
            x1 = animal1_roi1_x1
        else:
            x0 = animal1_roi2_x0
            x1 = animal1_roi2_x1

    # for the first data point in subsequent animals
    else:
        if exp_ct == 0:
            if plot_groups:
                x0 = (
                    animal1_roi2_x1
                    + (animal_ct * (between_group_interval))
                    + (animal_ct - 1)
                    * ((line_width * 2) + within_group_interval)
                )
            else:
                x0 = (
                    animal1_roi1_x1
                    + (animal_ct * (between_group_interval))
                    + (animal_ct - 1) * line_width
                )

        # if this is not exp_ct=0, then obviously plot_groups == True
        else:
            x0 = (
                animal1_roi2_x1
                + (animal_ct * (between_group_interval))
                + (animal_ct - 1) * ((line_width * 2) + within_group_interval)
                + line_width
                + within_group_interval
            )

        x1 = x0 + line_width

    return x0, x1


def plot_odor_measure_fig(
    sig_odor_exps,
    odor,
    measure,
    color_scale,
    total_animals,
    plot_groups,
    total_cols,
):
    """
    Plots the analysis values for specified odor and measurement
    """
    measure_fig = go.Figure()

    for animal_ct, animal_id in enumerate(sig_odor_exps.keys()):
        for exp_ct, sig_experiment in enumerate(sig_odor_exps[animal_id]):
            exp_odor_df = st.session_state.sorted_sig_data[animal_id][
                sig_experiment
            ][odor]

            measure_fig.add_trace(
                go.Box(
                    x=[animal_id] * len(exp_odor_df.loc[measure].values)
                    if isinstance(exp_odor_df.loc[measure], pd.Series)
                    else [animal_id],
                    y=exp_odor_df.loc[measure].values.tolist()
                    if isinstance(exp_odor_df.loc[measure], pd.Series)
                    else [exp_odor_df.loc[measure]],
                    line=dict(color="rgba(0,0,0,0)"),
                    fillcolor="rgba(0,0,0,0)",
                    boxpoints="all",
                    pointpos=0,
                    marker_color=color_scale["marker"][animal_ct + 1][exp_ct],
                    marker=dict(
                        # opacity=0.5,
                        line=dict(
                            color=color_scale["lines"][animal_ct + 1][exp_ct],
                            width=2,
                        ),
                        size=12,
                    ),
                    name=sig_experiment,
                    offsetgroup=exp_ct,
                    legendgroup=animal_ct,
                ),
            )

            # only adds mean line if there is more than one pt
            if isinstance(exp_odor_df.loc[measure], pd.Series):
                measure_fig = add_mean_line(
                    measure_fig,
                    total_animals,
                    total_cols,
                    plot_groups,
                    animal_ct,
                    exp_ct,
                    color_scale,
                    measure,
                    exp_odor_df,
                )

    return measure_fig


def add_mean_line(
    fig,
    total_animals,
    total_cols,
    plot_groups,
    animal_ct,
    exp_ct,
    color_scale,
    measure,
    exp_odor_df,
):
    """
    Adds mean line to each dataset
    """
    x0, x1 = position_mean_line(
        total_animals,
        total_cols,
        plot_groups,
        animal_ct,
        exp_ct,
    )

    fig.add_shape(
        type="line",
        line=dict(
            color=color_scale["lines"][animal_ct + 1][exp_ct],
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

    fig.update_xaxes(showticklabels=True, title_text="<br />Animal ID")

    fig.update_yaxes(
        title_text=measure,
    )

    if measure == "Time to peak (s)":
        fig.update_yaxes(
            rangemode="tozero",
        )

    fig.update_layout(
        boxmode="group",
        boxgap=0.4,
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
        (
            sig_odor_exps,
            all_roi_counts,
            total_animals,
        ) = get_odor_data(odor)

        plot_groups, total_cols = get_plot_params(all_roi_counts)

        for measure in st.session_state.measures:
            measure_fig = plot_odor_measure_fig(
                sig_odor_exps,
                odor,
                measure,
                color_scale,
                total_animals,
                plot_groups,
                total_cols,
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

    st.session_state.pg3_plots_list = plots_list


def display_plots():
    """
    Displays the plots for the selected odor
    """
    for measure in st.session_state.measures:
        st.plotly_chart(
            st.session_state.pg3_plots_list[st.session_state.selected_odor][
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


def make_pick_folder_button():
    """
    Makes the "Pick folder" button and checks whether it has been clicked.
    """
    clicked = st.button("Pick folder")
    return clicked


def pop_folder_selector():
    """
    Pops up a dialog to select folder. Won't pop up again when the script
    re-runs due to user interaction.
    """
    # Set up tkinter
    root = tk.Tk()
    root.withdraw()

    # Make folder picker dialog appear on top of other windows
    root.wm_attributes("-topmost", 1)

    dir_path = askdirectory(master=root)

    return dir_path


def main():
    set_webapp_params()
    initialize_states()

    save_csv = st.checkbox("Generate dataset summary .csv")

    if save_csv:
        clicked = make_pick_folder_button()

        if clicked:
            st.session_state.dir_path = pop_folder_selector()

        if st.session_state.dir_path:
            st.write("Summary .csv file will be saved to:")
            st.info(st.session_state.dir_path)

    st.session_state.files = st.file_uploader(
        label="Choose files",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )

    # pdb.set_trace()

    # checks that all the uploaded files are correct
    for file in st.session_state.files:
        if "_analysis" not in file.name:
            st.error(
                "Please make sure all uploaded files end in '_analysis.xlsx'"
            )
            st.session_state.files = False
            st.session_state.pg3_load_data = False

    if st.session_state.files or st.session_state.pg3_load_data:
        if st.button("Load data"):
            st.session_state.pg3_load_data = True

            (
                st.session_state.nosig_exps,
                odors_list,
                st.session_state.sig_data,
                st.session_state.sorted_sig_data,
            ) = import_data()

            st.info(
                f"Response data loaded successfully for "
                f"{len(st.session_state.files)} experiments."
            )

            check_sig_odors(odors_list)
            make_summary_csv()

            # if load data is clicked again, doesn't display plots/slider
            st.session_state.pg3_plots_list = False

        # if data has been loaded, always show plotting buttons
        if st.session_state.pg3_load_data and len(
            st.session_state.nosig_exps
        ) != len(st.session_state.files):
            if st.button("Plot data"):
                generate_plots()

            # display slider and plots if plots have already been generated
            # even if Plot data isn't clicked again
            if st.session_state.pg3_plots_list:
                st.session_state.selected_odor = st.selectbox(
                    "Select odor number to display its corresponding plots:",
                    options=st.session_state.sig_odors,
                )

                if st.session_state.selected_odor:
                    display_plots()


if __name__ == "__main__":
    main()
