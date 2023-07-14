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


def load_avg_means(file):
    """
    Loads the average means from an experiment into a dict, with sheet
    names/sample # as keys, df as values

    """
    avg_means_dict = pd.read_excel(file, sheet_name=None)
    st.info(
        f"Avg means loaded successfully for {len(avg_means_dict)} " "samples."
    )

    # the below tries to get list of odor #s from column names
    first_sample_df = next(iter(avg_means_dict.values()))

    odor_list = [x for x in first_sample_df.columns.values if type(x) == int]

    return avg_means_dict, odor_list


def make_empty_containers(dataset_type):
    """
    Makes empty dicts and lists to hold sig_exp and odor data
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


def make_empty_measurements_df():
    """
    Makes empty dfs to hold measurement values
    """
    baseline_df = pd.DataFrame()
    blank_sub_df = pd.DataFrame()
    auc_df = pd.DataFrame()
    latency_df = pd.DataFrame()
    ttpeak_df = pd.DataFrame()

    df_list = [baseline_df, blank_sub_df, auc_df, latency_df, ttpeak_df]

    return df_list


def load_file(
    load_bar,
    file,
    df_list,
    dict_list,
    dataset_type,
):
    """
    Creates an ExperimentFile object for each imported file, then processes
    the file for Excel saving and plotting
    """
    if dataset_type == "acute":
        nosig_exps, all_sig_odors, data_dict = dict_list
    elif dataset_type == "chronic":
        nosig_exps, all_sig_odors, data_dict, all_exps = dict_list

    loaded_file = ExperimentFile(file, df_list, dataset_type)

    load_bar.set_description(
        f"Loading data from {loaded_file.exp_name}", refresh=True
    )
    loaded_file.import_excel()
    loaded_file.sort_data()
    loaded_file.make_plotting_dfs()

    all_sig_odors.append(loaded_file.sig_odors)

    if dataset_type == "chronic":
        all_exps.append(loaded_file.exp_name)

    if not loaded_file.sig_data_df.empty:
        if dataset_type == "acute":
            data_dict[loaded_file.animal_id][
                loaded_file.exp_name
            ] = loaded_file.sig_data_df
        elif dataset_type == "chronic":
            data_dict[loaded_file.exp_name] = loaded_file.sig_data_df
    if loaded_file.sig_data_df.empty:
        nosig_exps.append(loaded_file.exp_name)


def import_all_excel_data(dataset_type, files):
    dict_list = make_empty_containers(dataset_type)

    # makes df for each measurement, for summary csv
    df_list = make_empty_measurements_df()

    if dataset_type == "chronic":
        files = sort_files_by_date(files)

    # adds progress bar
    load_bar = stqdm(files, desc="Loading ")
    for file in load_bar:
        load_file(load_bar, file, df_list, dict_list, dataset_type)

    return dict_list, df_list


def sort_files_by_date(files):
    sorted_files = sorted(
        files,
        key=lambda file: datetime.strptime(file.name.split("_")[0], "%y%m%d"),
    )

    return sorted_files


def get_odor_data(odor, dataset_type, data_dict):
    """
    Collects the data for odors with significant responses
    """

    if dataset_type == "acute":
        # makes list of experiments that have sig responses for
        # the odor
        sig_odor_exps = {}

        # makes list of number of ROIs per animal
        all_roi_counts = []

        for animal_id in data_dict:
            animal_exp_list = []

            for exp_ct, experiment in enumerate(data_dict[animal_id].keys()):
                if odor in data_dict[animal_id][experiment]:
                    animal_exp_list.append(experiment)
                    sig_odor_exps[animal_id] = animal_exp_list

            roi_count = len(animal_exp_list)
            all_roi_counts.append(roi_count)

        total_animals = len(sig_odor_exps)

        data = [sig_odor_exps, all_roi_counts, total_animals]

    elif dataset_type == "chronic":
        # makes list of experiments that have sig responses for
        # the odor
        sig_odor_exps = []

        for experiment in data_dict.keys():
            if odor in data_dict[experiment]:
                sig_odor_exps.append(experiment)

        total_sessions = len(sig_odor_exps)

        data = sig_odor_exps

    return data


def sort_measurements_df(
    dir_path,
    xlsx_fname,
    df_list,
    sample_type,
    measures,
    dataset_type,
    animal_id=None,
):
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
    sig_odors,
    nosig_exps,
    dataset_type,
    data_dict,
    measures_list,
    sorted_dates=None,
    interval=None,
):
    """
    Creates plots for each odor
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


def show_plots_sliders(plots_list, selected_odor, sig_odors, measures):
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


def display_plots(measures_list, plots_list, selected_odor):
    """
    Displays the plots for the selected odor
    """
    for measure in measures_list:
        st.plotly_chart(plots_list[selected_odor][measure])


def process_txt_file(data, n_count, bar, sample_type):
    raw_means, avg_means = data.collect_per_sample(
        data.all_data_df, data.n_column_labels[n_count]
    )

    save_to_excel(
        data.session_path,
        data.n_column_labels[n_count],
        f"{data.date}_{data.animal_id}_{data.ROI_id}_raw_means.xlsx",
        raw_means,
    )
    # performs analysis for each sample
    analysis_df = data.analyze_signal(avg_means)

    # save avg_means to xlxs file
    data.save_avg_means(avg_means, data.n_column_labels[n_count])

    # save analyses values to xlxs file
    data.save_sig_analysis(analysis_df, data.n_column_labels[n_count])

    bar.set_description(f"Analyzing {sample_type} {n_count+1}", refresh=True)
