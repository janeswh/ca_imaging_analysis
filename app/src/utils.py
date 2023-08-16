"""Contains helper utilities for processing experiment folders and data saving.
"""

from pathlib import Path
import pandas as pd
import os
import openpyxl
import streamlit as st
import tkinter as tk
from tkinter.filedialog import askdirectory


import pdb


def check_solenoid_file(session_path):
    """Checks that solenoid. txt file is named properly and present.

    Args:
        session_path (str): Path to the session directory.

    Returns:
        A string containing the path to the solenoid file.
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
    """Checks that all uploaded files end in _analysis.xlsx.

    Args:
        files (list): A list of file objects to check for correctness.

    Returns:
        A bool value. True if all files are correct, False if not or None.
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
    """Saves measurement dfs as one sheet per measurement type into Excel file.

    By default, to_excel sets NaN values to "" using na_rep="".

    Args:
        dir_path (str): A path to directory to save file.
        sheetname (str): The name of sheet to save df to.
        xlsx_fname (str): The name of the xlsx file to save df to.
        df (pd.DataFrame): The df to save.
        animal_id (str): The animal id to use for file name formating.
        add_label (bool): If True add label to sheet (default False).
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
    """Adds borders to Excel spreadsheets.

    Args:
        xlsx_path (str): Path to the Excel file to be formatted.
        animal_id (str): ID of the animal to be used in the format.
        add_label (bool): If True adds label to A1 cell.
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
    """Checks the odors from the uploaded data and puts them in a list.

    Args:
        odors_list (list): The odors to check.
        nosig_exps (list): The experiments that are not significant.
        files (list): The files uploaded for experiment.

    Returns:
        A list of significant odors sorted by odor number.
    """

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


def flatten(to_flatten: str | list) -> list:
    """Flattens a nested list of significant odors into a single list.

    Args:
        to_flatten: The nested list of odors to flatten. If it only contains
            a single odor, it will be returned as a list.

    Returns:
        A list of all elements of the list in the same order
    """

    if not isinstance(to_flatten, list):  # If single odor (str)
        return [to_flatten]
    return [
        x for sub in to_flatten for x in flatten(sub)
    ]  # recurse and collect


def make_pick_folder_button() -> bool:
    """Makes the Pick folder button and checks whether it has been clicked.

    Returns:
        True if button was clicked, False if not.
    """

    clicked = st.button("Pick folder")

    return clicked


def pop_folder_selector() -> str:
    """Pops up a dialog to select a folder.

    Returns:
        The path to the selected folder
    """

    # Set up tkinter
    root = tk.Tk()
    root.withdraw()

    # Make folder picker dialog appear on top of other windows
    root.wm_attributes("-topmost", 1)

    dir_path = askdirectory(master=root)
    return dir_path


def get_selected_folder_info(dir_path: str) -> tuple[str, str, str]:
    """Gets information about the selected folder.

    Args:
        dir_path: Path to the selected folder.

    Returns:
        A tuple containing the date, animal_ID, and ROI of the selected folder.
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


def get_session_info(folder: str) -> tuple[str, str, str]:
    """Gets the date, animal ID and ROI info from the name of the selected
    folder.

    Args:
        folder: The name of the folder to be parsed.

    Returns:
        A tuple containing the date, animal ID, and ROI of the folder.
    """

    date = folder.split("--")[0]
    animal_ID = folder.split("--")[1].split("_")[0]
    roi = folder.split("_")[1]

    return date, animal_ID, roi


def read_txt_file(path: str) -> pd.DataFrame:
    """Reads a single txt file from one trial into a dataframe.

    Args:
        path: Path to the txt file.

    Returns:
        A DataFrame with the txt file's data in columns.
    """

    txt_df = pd.read_csv(Path(path), sep="\t", index_col=0)

    return txt_df


def save_to_csv(fname: str, path: str, df: pd.DataFrame):
    """Saves a dataframe to a csv file.

    Args:
        fname: The name of the csv file.
        path: The path to save the csv to.
        df: The dataframe to save to the csv file.
    """

    csv_path = Path(path, fname)

    df.to_csv(csv_path, index=False)
