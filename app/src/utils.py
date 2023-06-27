from pathlib import Path
import pandas as pd
import numpy as np
import os
import openpyxl
import streamlit as st
import tkinter as tk
from tkinter.filedialog import askdirectory
from natsort import natsorted
import pdb


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

        data = [sig_odor_exps, total_sessions]

    return data


def sort_measurements_df(
    dir_path,
    xlsx_fname,
    df_list,
    sample_type,
    measures,
    chronic=False,
    animal_id=None,
):
    sheetname_list = [
        "Blank-subtracted DeltaFF(%)",
        "Blank sub AUC",
        "Latency (s)",
        "Time to peak (s)",
    ]

    odors_list = [f"Odor {x}" for x in range(1, 8)]

    for df_ct, df in enumerate(df_list):
        measure = measures[df_ct]
        if chronic is True:
            df = df.reset_index().set_index(["Date", sample_type])
        else:
            df = df.reset_index().set_index(["Animal ID", "ROI", sample_type])
        df.sort_index(inplace=True)
        df = df.reindex(sorted(df.columns), axis=1)
        df.drop(columns=[(measure, "Odor 2")], inplace=True)

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
        save_to_excel(dir_path, sheetname, xlsx_fname, df, animal_id)


def save_to_excel(dir_path, sheetname, xlsx_fname, df, animal_id=None):
    """
    Saves measurement dfs as one sheet per measurement type into Excel file
    """

    # xlsx_fname = f"compiled_dataset_analysis.xlsx"
    xlsx_path = Path(dir_path, xlsx_fname)

    if os.path.isfile(xlsx_path):  # if it does, write to existing file
        # if sheet already exists, overwrite it
        with pd.ExcelWriter(
            xlsx_path, mode="a", if_sheet_exists="replace"
        ) as writer:
            df.to_excel(writer, sheetname)
    else:  # otherwise, write to new file
        df.to_excel(xlsx_path, sheetname)

    format_workbook(xlsx_path, animal_id)


def format_workbook(xlsx_path, animal_id=None):
    """
    Adds borders to Excel spreadsheets
    """
    wb = openpyxl.load_workbook(xlsx_path)

    # Initialize formatting styles
    no_fill = openpyxl.styles.PatternFill(fill_type=None)
    side = openpyxl.styles.Side(border_style="thin")
    border = openpyxl.styles.borders.Border(
        left=side,
        right=side,
        top=side,
        bottom=side,
    )

    # Loop through all cells in all worksheets
    for sheet in wb.worksheets:
        if animal_id:
            sheet["A1"] = animal_id
        for row in sheet:
            for cell in row:
                # Apply colorless and borderless styles
                cell.fill = no_fill
                cell.border = border

    # Save workbook
    wb.save(xlsx_path)


def check_sig_odors(odors_list):
    """
    Checks significant odor responses from loaded data and puts them in a list
    """
    # flatten list of odors
    flat_odors_list = flatten(odors_list)

    if len(st.session_state.nosig_exps) == len(st.session_state.files):
        st.error(
            "None of the uploaded experiments have significant "
            " odor responses. Please upload data for experiments with "
            " significant responses to plot the response measurements."
        )

    else:
        # gets unique significant odors and puts them in order
        sig_odors = list(dict.fromkeys(flat_odors_list))
        sig_odors.sort()

        return sig_odors


def flatten(arg):
    """
    Flattens nested list of sig odors
    """
    if not isinstance(arg, list):  # if not list
        return [arg]
    return [x for sub in arg for x in flatten(sub)]  # recurse and collect


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
