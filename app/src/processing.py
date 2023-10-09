"""Contains functions for processing the data loaded from .xlsx files."""

import numpy as np
import pandas as pd
from collections import defaultdict
from stqdm import stqdm
import streamlit as st
from datetime import datetime

from src.utils import save_to_excel

from src.plotting import (
    get_acute_plot_params,
    plot_acute_odor_measure_fig,
    plot_chronic_odor_measure_fig,
    format_fig,
)

from src.experiment import ExperimentFile

import pdb


def load_avg_means(file: str) -> tuple[dict, list]:
    """Loads the average means from an experiment into a dictionary, with sheet
    names/sample # as keys, DataFrame as values.

    Args:
        file: The path to the .xlsx file containing the average means.

    Returns:
        avg_means_dict: Dict containing the average means from avg_means.xlsx
            file.
        odor_list: The list of odors found in the .xlsx file.
    """

    avg_means_dict = pd.read_excel(file, sheet_name=None)
    st.info(
        f"Avg means loaded successfully for {len(avg_means_dict)} " "samples."
    )

    # The below tries to get list of odor #s from column names
    first_sample_df = next(iter(avg_means_dict.values()))

    odor_list = [x for x in first_sample_df.columns.values if type(x) == int]

    return avg_means_dict, odor_list


def make_empty_containers(dataset_type: str) -> list:
    """Makes a list of empty lists and dicts to hold experimental data and the
    ids of significant vs. non-significant experiments and odors.

    Args:
        dataset_type: Whether the experiment is chronic or acute.

    Returns:
        A list containing experimental data and the ids of significant
        experiments and odors.
    """

    # makes list to hold all file names for ordering
    all_exps = []

    # makes list to hold exp names with no significant data
    nosig_exps = []

    # makes list to hold all significant odors
    all_sig_odors = []

    if dataset_type == "chronic":
        data_dict = {}
        dict_list = [nosig_exps, all_sig_odors, data_dict, all_exps]
    elif dataset_type == "acute":
        data_dict = defaultdict(dict)
        dict_list = [
            nosig_exps,
            all_sig_odors,
            data_dict,
        ]

    return dict_list


def load_file(
    file: str,
    df_list: list,
    dict_list: list,
    dataset_type: str,
) -> tuple[list, list, str]:
    """Creates an ExperimentFile object for each imported file, then processes
    the file for Excel saving and plotting.

    Args:
        file: streamlit.runtime.uploaded_file_manager.UploadedFile, csv file
        df_list: A list of DataFrames to hold the DataFrames for each
            analysis measurement.
        dict_list: A list of lists and dictionary that contains experimental
        data and the ids of significant experiments and odors.
        dataset_type: Chronic or acute experiment type.

    Returns:
        appended_df_list: A list of a list of DataFrames, one list for each
            measurement contained in analysis.xlsx. Values from each file are
            appended as new rows in the DataFrames via ExperimentFile.sort_data().
        appended_dict_list: A list of lists and dictionary containing experimental
            data and the ids of significant experiments and odors. Experiment
            and odor ids from each file are appended as new items in the list,
            and significant data are appended with the experiment name as keys
            in the dictionary, all done via ExperimentFile.sort_data().
        bar_text: The text to display on the progress bar.
    """

    if dataset_type == "acute":
        nosig_exps, all_sig_odors, data_dict = dict_list
    elif dataset_type == "chronic":
        nosig_exps, all_sig_odors, data_dict, all_exps = dict_list

    loaded_file = ExperimentFile(file, dataset_type)
    bar_text = f"Loading data from {loaded_file.exp_name}"

    excel_dict = loaded_file.import_excel()
    appended_df_list = loaded_file.sort_data(excel_dict, df_list)
    sig_odors, sig_data_df = loaded_file.make_plotting_dfs(excel_dict)

    all_sig_odors.append(sig_odors)

    if dataset_type == "chronic":
        all_exps.append(loaded_file.exp_name)

    if not sig_data_df.empty:
        if dataset_type == "acute":
            data_dict[loaded_file.animal_id][
                loaded_file.exp_name
            ] = sig_data_df
        elif dataset_type == "chronic":
            data_dict[loaded_file.exp_name] = sig_data_df
    if sig_data_df.empty:
        nosig_exps.append(loaded_file.exp_name)

    if dataset_type == "acute":
        appended_dict_list = nosig_exps, all_sig_odors, data_dict
    elif dataset_type == "chronic":
        appended_dict_list = nosig_exps, all_sig_odors, data_dict, all_exps

    return appended_df_list, appended_dict_list, bar_text


def import_all_excel_data(dataset_type: str, files: list) -> tuple[list, list]:
    """A wrapper for looping through all selected .xlsx files for importing
    and processing via load_file.

    New data for each .xlsx file are appended onto existing DataFrames and
    dictionary via ExperimentFile.sort_data(), called by load_file.

    Args:
        dataset_type: Chronic or acute experiment type.
        files: A list of .xlsx files uploaded to Streamlit.

    Returns:
        appended_df_list: A list of a list of DataFrames, one list for each
            measurement contained in analysis.xlsx
        appended_dict_list: A list of dictionaries containing experimental
            data and the ids of significant experiments and odors.
        bar_text: The text to display on the progress bar.
    """

    dict_list = make_empty_containers(dataset_type)

    # makes df for each measurement, for summary csv
    df_list = [pd.DataFrame() for x in range(5)]

    if dataset_type == "chronic":
        files = sort_files_by_date(files)

    # adds progress bar
    load_bar = stqdm(files, desc="Loading ")
    for file in load_bar:
        # Get and append new values for each .xlsx file
        appended_df_list, appended_dict_list, bar_text = load_file(
            file, df_list, dict_list, dataset_type
        )
        load_bar.set_description(bar_text, refresh=True)

        # Save new data to be passed in again via the next loop
        df_list = appended_df_list
        dict_list = appended_dict_list

    return dict_list, df_list


def sort_files_by_date(files: list) -> list:
    """Sorts the uploaded .xlsx files by date for processing.

    Args:
        files: A list of .xlsx files uploaded to Streamlit.

    Returns:
        The list of uploaded files, sorted by date.
    """

    sorted_files = sorted(
        files,
        key=lambda file: datetime.strptime(file.name.split("_")[0], "%y%m%d"),
    )

    return sorted_files


def get_odor_data(odor: str, dataset_type: str, data_dict: str):
    """Collects the data for odors with significant responses.

    Args:
        odor: The odor for which to collect data.
        dataset_type: Chronic or acute experiment type.
        data_dict: The dictionary containing all significant data for the
            dataset.

    Returns:
        If acute dataset, a list containing: a list of significant odor
            experiments, a list of the number of ROIs imaged, and the number
            of total animals imaged.
        If chronic dataset, returns a list of experiments with significant
            responses for the odor.
    """

    if dataset_type == "acute":
        # makes list of experiments that have sig responses for
        # the odor
        sig_odor_exps = {}

        # makes list of number of ROIs per animal
        all_roi_counts = []

        for animal_id in data_dict:
            animal_exp_list = []

            for experiment in data_dict[animal_id].keys():
                if odor in data_dict[animal_id][experiment]:
                    animal_exp_list.append(experiment)
                    sig_odor_exps[animal_id] = animal_exp_list

            roi_count = len(animal_exp_list)
            all_roi_counts.append(roi_count)

        total_animals = len(sig_odor_exps)

        data = [sig_odor_exps, all_roi_counts, total_animals]

    elif dataset_type == "chronic":
        # makes list of experiments that have sig responses for the odor
        sig_odor_exps = []

        for experiment in data_dict.keys():
            if odor in data_dict[experiment]:
                sig_odor_exps.append(experiment)

        data = sig_odor_exps

    return data


def sort_measurements_df(
    dir_path: str,
    xlsx_fname: str,
    df_list: list,
    sample_type: str,
    measures: list,
    dataset_type: str,
    animal_id: str = None,
):
    """Saves the DataFrames for each measurement as a sheet in a summary
    compiled_dataset_analysis.xlsx file for the dataset.

    Args:
        dir_path: Path to the directory for saving the .xlsx file.
        xlsx_fname: Name of the .xlsx file to save.
        df_list: List containing DataFrames for each measurement.
        sample_type: The sample type, e.g. "Cell", "Glomerulus", or "Grid".
        measures: A list of the measurement names.
        dataset_type: Chronic or acute dataset.
        animal_id: The animal ID, if it's a chronic dataset.
    """

    sheetname_list = [
        "Baseline",
        "Blank-subtracted DeltaFF(%)",
        "Blank sub AUC",
        "Latency (s)",
        "Time to peak (s)",
    ]

    odors_list = [f"Odor {x}" for x in range(1, 8)]

    for df_ct, df in enumerate(df_list):
        measure = measures[df_ct]
        if dataset_type == "chronic":
            df = df.reset_index().set_index(["Date", sample_type])
        else:
            df = df.reset_index().set_index(["Animal ID", "ROI", sample_type])
        df.sort_index(inplace=True)
        df = df.reindex(sorted(df.columns), axis=1)

        # Manually add back empty/non-sig odor columns to reduce confusion
        for odor in odors_list:
            if (measure, odor) not in df.columns:
                df[(measure, odor)] = np.nan

        # Drop odor 8/blank from df
        if (measure, "Odor 8") in df.columns:
            df.drop(columns=[(measure, "Odor 8")], inplace=True)
        columns_list = [(f"{measure}", f"Odor {x}") for x in range(1, 8)]

        df = df[columns_list]  # Reorders Odor columns list
        sheetname = sheetname_list[df_ct]
        add_label = False

        if dataset_type == "chronic":
            add_label = True

        save_to_excel(
            dir_path, sheetname, xlsx_fname, df, animal_id, add_label
        )


def generate_plots(
    sig_odors: list,
    nosig_exps: list,
    dataset_type: str,
    data_dict: dict,
    measures_list: list,
    sorted_dates: list = None,
    interval: str = None,
) -> dict:
    """Creates plots for each odor.

    Args:
        sig_odors: List of odors with significant responses.
        nosig_exps: List of experiments with no significant responses.
        dataset_type: Chronic or acute dataset.
        data_dict: Data for all significant responses.
        measures_list: A list of the measurement names.
        sorted_dates: A list of experiments, sorted by date. For chronic only.
        interval: User-selected interval type, for chronic only.

    Returns:
        A dict of dicts, with odor then measurement as keys, and plots as items.
    """

    plots_list = defaultdict(dict)

    # adds progress bar
    odor_bar = stqdm(sig_odors, desc="Plotting ")

    for odor in odor_bar:
        odor_data = get_odor_data(odor, dataset_type, data_dict)

        if dataset_type == "chronic":
            sig_odor_exps = odor_data
        else:
            sig_odor_exps = odor_data[0]
            all_roi_counts = odor_data[1]
            total_animals = odor_data[2]
            plot_groups, total_cols = get_acute_plot_params(all_roi_counts)

        for measure in measures_list:
            if measure != "Baseline":
                if dataset_type == "chronic":
                    measure_fig = plot_chronic_odor_measure_fig(
                        sig_odor_exps,
                        data_dict,
                        odor,
                        measure,
                        sorted_dates,
                    )

                    format_fig(
                        measure_fig,
                        measure,
                        "chronic",
                        interval,
                        sorted_dates,
                    )

                else:
                    measure_fig = plot_acute_odor_measure_fig(
                        sig_odor_exps,
                        data_dict,
                        odor,
                        measure,
                        total_animals,
                        plot_groups,
                        total_cols,
                    )

                    format_fig(measure_fig, measure, "acute")

                plots_list[odor][measure] = measure_fig

        odor_bar.set_description(f"Plotting {odor}", refresh=True)

    st.info("All plots generated.")
    if len(nosig_exps) != 0:
        st.warning(
            "No plots have been generated for the "
            "following experiments due to the lack of significant "
            "odor responses: \n"
            f"{nosig_exps}"
        )

    return plots_list


def show_plots_sliders(
    plots_list: dict, selected_odor: str, sig_odors: list, measures: list
):
    """Shows the slider for selecting odor number for displaying plots.

    Args:
        plots_list: A dict of dicts, with odor then measurement as keys,
            and plots as items.
        selected_odor: The odor for which to display plots.
        sig_odors: Significant odors with available plots to display.
        measures: The names of measurements.
    """

    plot_measures = measures.copy()
    plot_measures.remove("Baseline")
    if plots_list:
        selected_odor = st.selectbox(
            "Select odor number to display its corresponding plots:",
            options=sig_odors,
        )

        if selected_odor:
            display_plots(
                plot_measures,
                plots_list,
                selected_odor,
            )


def display_plots(measures_list: list, plots_list: dict, selected_odor: str):
    """Displays the plots for the selected odor.

    Args:
        measures_list: The names of measurements.
        plots_list: A dict of dicts, with odor then measurement as keys,
            and plots as items.
        selected_odor: The odor for which to display plots.
    """

    for measure in measures_list:
        st.plotly_chart(plots_list[selected_odor][measure])
