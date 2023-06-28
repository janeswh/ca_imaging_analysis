from pathlib import Path
import pandas as pd
import os
import openpyxl
import streamlit as st
import tkinter as tk
from tkinter.filedialog import askdirectory


import pdb


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
