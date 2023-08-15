from pathlib import Path
import pandas as pd
import os
import openpyxl
import streamlit as st
import tkinter as tk
from tkinter.filedialog import askdirectory


import pdb


def find_solenoid_file(session_path):
    """
    Find solenoid file in the session directory.

    Args:
        session_path: path to the session directory

    Returns:
        string with the name of the solenoid file
    """

    for filename in os.listdir(session_path):
        if "solenoid_order" in filename:
            return filename


def check_solenoid_file(session_path):
    """
    Checks that solenoid. txt file is named properly and present.

    Args:
        session_path: path to the session directory. It must be a directory

    Returns:
        Path to the solenoid file
    """

    solenoid_file = None
    for filename in os.listdir(session_path):
        # for new code with solenoid_order.csv file
        if "solenoid_order" in filename or "solenoid_info.txt" in filename:
            solenoid_file = Path(session_path, filename)

    if solenoid_file is None:
        st.error(
            "Please make sure that the solenoid order file is present in the "
            "directory, either as ...solenoid_info.txt or "
            "...solenoid_order...csv."
        )

    return solenoid_file


def check_uploaded_files(files):
    """
    Checks that all uploaded files end in _analysis.xlsx

    Args:
        files: list of file objects to check for correctness

    Returns:
        True if all files are correct, False if not or None
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

    Args:
        dir_path (str): path to directory to save file
        sheetname (str): name of sheet to save df to
        xlsx_fname (str): name of xlsx file to save df to
        df (pd.DataFrame): df to save
        animal_id (str): animal id to use for file name formating
        add_label (bool): if True add label to sheet (default False)
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

    Args:
        xlsx_path (str): Path to the Excel file to be formatted
        animal_id (str): ID of the animal to be used in the format
        add_label (bool): If True adds label to A1 cell
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
    Checks the odors from the uploaded data and puts them in a list.

    Args:
        odors_list: list of odors to check
        nosig_exps: list of experiments that are not significant
        files: list of files uploaded for experiment

    Returns:
        sig_odors list sorted by odors
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


def flatten(to_flatten):
    """
    Flattens a nested list of sig odors into a single list.

    Args:
        to_flatten: The list to flatten. If it's a list it will be returned as is.

    Returns:
        A list of all elements of the list in the same order
    """

    if not isinstance(to_flatten, list):  # if not list
        return [to_flatten]
    return [
        x for sub in to_flatten for x in flatten(sub)
    ]  # recurse and collect


def make_pick_folder_button():
    """
    Makes the Pick folder button and checks whether it has been clicked. It is used to select a folder to be picked

    Returns:
        button that is clicked
    """

    clicked = st.button("Pick folder")
    return clicked


def pop_folder_selector():
    """
    Pops up a dialog to select a folder.


    Returns:
        Path to the selected folder
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
    Gets information about the selected folder. This is a wrapper around
    get_session_info to allow the user to select a folder by clicking on
    the folder in the file dialog.

    Args:
        dir_path: Path to the folder that is selected.

    Returns:
        The date, animal_ID, and ROI of the selected folder as strings.
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
    Gets the date, animal ID and ROI info from the name of the selected folder.

    Args:
        folder: Folder to be parsed.

    Returns:
        The date, animal ID and ROI of the folder as strings.
    """

    date = folder.split("--")[0]
    animal_ID = folder.split("--")[1].split("_")[0]
    roi = folder.split("_")[1]

    return date, animal_ID, roi


def read_txt_file(path):
    """
    Reads a single txt file from one trial into a dataframe. This is a
    convenience function for read_csv that does not require a file path

    Args:
        path: Path to the txt file

    Returns:
        DataFrame with the txt file's data in columns
    """

    txt_df = pd.read_csv(Path(path), sep="\t", index_col=0)

    return txt_df


def save_to_csv(fname, path, df):
    """
    Saves a dataframe to a csv file.

    Args:
        fname (str): The name of the csv file
        path (str): The path to save the csv to
        df (DataFrame): The dataframe to save to the csv file
    """

    csv_path = Path(path, fname)

    df.to_csv(csv_path, index=False)
