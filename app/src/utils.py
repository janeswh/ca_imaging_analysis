from pathlib import Path
import pandas as pd
import os
import openpyxl
import streamlit as st
import tkinter as tk
from tkinter.filedialog import askdirectory


import pdb


def check_solenoid_file(date, animal_id, ROI_id, session_path):
    """
    Checks that the solenoid .txt file is named properly and present.
    """
    solenoid_filename = (
        date + "_" + animal_id + "_" + ROI_id + "_solenoid_info.txt"
    )

    solenoid_path = Path(session_path, solenoid_filename)

    # reads first line of solenoid order txt file
    try:
        with open(solenoid_path) as f:
            solenoid_order_raw = f.readline()
    except OSError:
        st.error(
            "Please make sure that the solenoid info txt file is "
            "present in the directory and named correctly in the "
            "format YYMMDD_123456-7-8_ROIX_solenoid_info.txt."
        )
        solenoid_order_raw = None

    return solenoid_order_raw


def check_uploaded_files(files):
    """
    Checks that files are correct
    """
    files_correct = None
    for file in files:
        if "_analysis" not in file.name:
            st.error(
                "Please make sure all uploaded files end in '_analysis.xlsx'"
            )
            files_correct = False
            break
        else:
            files_correct = True

    return files_correct


def save_to_excel(
    dir_path,
    sheetname,
    xlsx_fname,
    df,
    animal_id=None,
    add_label=False,
):
    """
    Saves measurement dfs as one sheet per measurement type into Excel file.
    By default, to_excel sets NaN values to "" using na_rep=""
    """
    xlsx_path = Path(dir_path, xlsx_fname)
    if os.path.isfile(xlsx_path):  # if it does, write to existing file
        # if sheet already exists, overwrite it
        with pd.ExcelWriter(
            xlsx_path, mode="a", if_sheet_exists="replace"
        ) as writer:
            df.to_excel(writer, sheetname)
    else:  # otherwise, write to new file
        df.to_excel(xlsx_path, sheetname)

    format_workbook(xlsx_path, animal_id, add_label)


def format_workbook(xlsx_path, animal_id=None, add_label=False):
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
        if add_label:
            sheet["A1"] = animal_id
        for row in sheet:
            for cell in row:
                # Apply colorless and borderless styles
                cell.fill = no_fill
                cell.border = border

    # Save workbook
    wb.save(xlsx_path)


def check_sig_odors(odors_list, nosig_exps, files):
    """
    Checks significant odor responses from loaded data and puts them in a list
    """
    # flatten list of odors
    flat_odors_list = flatten(odors_list)

    if len(nosig_exps) == len(files):
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


def get_selected_folder_info(dir_path):
    """
    Gets the date, animal ID, and ROI info from the selected folder.
    """
    st.write("Selected folder:")
    st.info(dir_path)
    folder = os.path.basename(dir_path)
    try:
        date, animal_ID, roi = get_session_info(folder)

    except IndexError:
        date = animal_ID = roi = None
        st.error(
            "Please ensure that you've selected the desired folder by "
            "double clicking to open it in the file dialog and that it's "
            "named correctly."
        )

    return date, animal_ID, roi


def get_session_info(folder):
    """
    Gets the date, animal ID, and ROI info from the name of the selected
    folder.
    """

    date = folder.split("--")[0]
    animal_ID = folder.split("--")[1].split("_")[0]
    roi = folder.split("_")[1]

    return date, animal_ID, roi


def read_txt_file(path):
    """
    Reads a single txt file from one trial into a dataframe.
    """
    txt_df = pd.read_csv(Path(path), sep="\t", index_col=0)

    return txt_df


def save_to_csv(fname, path, df):
    """
    Saves a df to csv
    """
    csv_path = Path(path, fname)

    df.to_csv(csv_path, index=False)
