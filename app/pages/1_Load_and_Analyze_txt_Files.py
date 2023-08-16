from src.utils import (
    make_pick_folder_button,
    pop_folder_selector,
    check_solenoid_file,
    get_selected_folder_info,
)

from src.experiment import RawFolder

import streamlit as st
import os
from stqdm import stqdm

import pdb


def set_webapp_params():
    """Sets the name of the Streamlit app"""
    st.set_page_config(page_title="Load & Analyze .txt files")
    st.title("ROI Analysis")


def initialize_states():
    """Initializes session state variables."""
    if "manual_path" not in st.session_state:
        st.session_state.manual_path = False
    if "dir_path" not in st.session_state:
        st.session_state.dir_path = False
    if "sample_type" not in st.session_state:
        st.session_state.sample_type = False
    if "run_type" not in st.session_state:
        st.session_state.run_type = False
    if "drop_trial" not in st.session_state:
        st.session_state.drop_trial = False


def prompt_dir():
    """Prompts user for directory containing the raw .txt files to be
    analyzed.
    """
    st.markdown(
        "Please select (by double clicking into) the folder containing the Ca "
        "imaging raw .txt files from the imaging session you want to analyze. "
        "The folder should be named in the format YYMMDD--123456-7-8_ROIX "
        "where 123456-7-8 is the animal ID, and X is the one-digit ROI number."
    )

    clicked = make_pick_folder_button()
    if clicked:
        select_manual = False
        st.session_state.manual_path = False
        st.session_state.dir_path = pop_folder_selector()

    select_manual = st.button("Enter folder path manually")
    if select_manual or st.session_state.manual_path:
        st.session_state.manual_path = True
        st.session_state.dir_path = st.text_input(
            "Enter full path of the folder, e.g. "
            "/Users/Bob/Experiments/2019_GCaMP6s/220101--123456-7-8_ROI1 "
            " and make sure there are no spaces in the path."
        )


def choose_sample_type():
    """Prompts user to select sample type - cell vs. glomerulus vs. grid.

    Returns:
        A Streamlit radio button containing the choice options.
    """

    choice = st.radio("Select sample type:", ("Cell", "Glomerulus", "Grid"))

    return choice


def choose_run_type():
    """Asks user whether they want to export the solenoid info as csv or do
    the analysis as normal.

    Returns:
        A string representing the type of run.
    """

    choice = st.radio(
        "Select task:", ("Run analysis", "Export solenoid info only")
    )

    if choice == "Run analysis":
        choice_type = "analysis"
    elif choice == "Export solenoid info only":
        choice_type = "solenoid"

    return choice_type


def run_analysis(
    folder_path, date, animal, ROI, sample_type, run_type, drop_trial
):
    """Runs the analysis for one imaging session.

    Args:
        folder_path (str): Path to the folder to run the analysis for.
        date (str): Date of the analysis (YYYYMMDD).
        animal (str): Name of the animal being analysed.
        ROI (str): Region of Interest.
        sample_type (str): Type of sample being analysed.
        run_type (str): Type of analysis to run.
        drop_trial (str): Whether to drop trials or not.
    """

    data = RawFolder(folder_path, date, animal, ROI, sample_type, drop_trial)
    data.get_solenoid_order()  # gets odor order from solenoid txt file

    if run_type == "solenoid":
        data.save_solenoid_info()  # saves solenoid order to csv
        st.info("Solenoid info exported to csv.")

    elif run_type == "analysis":
        # display error message if no txt files present
        data_files = [
            x
            for x in os.listdir(data.session_path)
            if "solenoid" not in x and ".txt" in x
        ]
        if len(data_files) == 0:
            st.error(
                "Please make sure the Ca imaging txt files are present in "
                "the selected directory."
            )
        else:
            data.rename_txt()  # adds _000.txt to end of first trial file
            file_paths = data.get_txt_file_paths()
            data_df = data.iterate_txt_files(file_paths)
            data.organize_all_data_df(data_df)

            # Drop trials from the data set.
            if drop_trial:
                data.drop_trials()

            # sort all data by neuron/glomerulus
            # adds progress bar
            bar = stqdm(
                range(data.total_n),
                desc=f"Analyzing {sample_type}",
            )
            for n_count in bar:
                bar_text = data.process_txt_file(n_count, sample_type)
                bar.set_description(bar_text, refresh=True)

            st.info("Analysis finished.")


def main():
    set_webapp_params()
    initialize_states()
    prompt_dir()

    if st.session_state.dir_path:
        date, animal_id, roi = get_selected_folder_info(
            st.session_state.dir_path
        )

        if date:
            # if folder has been selected properly, proceed
            solenoid_file = check_solenoid_file(st.session_state.dir_path)

            # if solenoid file is present and correctly named, proceed
            if solenoid_file:
                # Only choose run type if solenoid order file doesn't already
                # exist (Beichen's old code)
                if "solenoid_info.txt" in str(solenoid_file):
                    st.session_state.run_type = choose_run_type()
                elif "solenoid_order" in str(solenoid_file):
                    st.session_state.run_type = "analysis"

                if st.session_state.run_type == "analysis":
                    st.session_state.sample_type = choose_sample_type()
                    if st.checkbox("Exclude specific trials from analysis"):
                        st.session_state.drop_trial = st.text_input(
                            "Enter trial number to drop, separated by comma if "
                            "there are multiple, e.g. 1,2,5,6"
                        )

                st.warning(
                    "If this is a re-run, please delete all the .xlsx files "
                    " from the previous run through before clicking Go!"
                )
                if st.button("Go!"):
                    run_analysis(
                        st.session_state.dir_path,
                        date,
                        animal_id,
                        roi,
                        st.session_state.sample_type,
                        st.session_state.run_type,
                        st.session_state.drop_trial,
                    )


if __name__ == "__main__":
    main()
