import os
import glob
import pandas as pd
from collections import OrderedDict, defaultdict
from pathlib import Path, PureWindowsPath
import re

import pdb


def set_main_directory():
    """
    Defines the directory that holds all the text files across all imaging
    sessions
    """
    main_directory_path = (
        "/home/jhuang/Documents/phd_projects/Ca_image_analysis_examples"
    )

    return main_directory_path


def get_session_date():
    """
    Prompts the user for the date of the imaging session
    """

    date = input("Enter imaging date as format YYMMDD: ")

    return date


def search_matching_folders(main_directory_path, search_type, date, animal_id):
    """
    Search all folders in the directory containing matching string, depending
    on whether searching for animal ID for a given date, or ROI for a given 
    date and animal
    """
    extracted_list = []
    if search_type == "date":
        folders = [
            f.name
            for f in os.scandir(main_directory_path)
            if f.is_dir() and date in f.name
        ]

        for folder in folders:
            # this returns animal ID
            extracted_item = folder.split("--")[1].split("_")[0]
            extracted_list.append(extracted_item)

    elif search_type == "animal":
        folders = [
            f.name
            for f in os.scandir(main_directory_path)
            if f.is_dir() and date in f.name and animal_id in f.name
        ]

        for folder in folders:
            # this returns ROI
            extracted_item = folder.split("_")[1]
            extracted_list.append(extracted_item)

    return extracted_list


def make_choices_dict(raw_list):
    """
    Makes a dict of animal ID or ROI choices for user to select from
    """
    # sorts list by last digit of animal ID or ROI ID
    sorted_list = sorted(raw_list, key=lambda x: int(x[-1]))

    drop_dupes_dict = OrderedDict.fromkeys(sorted_list)

    choice_int_list = [
        str(i) for i in list(range(1, len(drop_dupes_dict) + 1))
    ]

    for key, val in zip(drop_dupes_dict, choice_int_list):
        drop_dupes_dict[key] = val

    select_dict = {v: k for k, v in drop_dupes_dict.items()}

    return select_dict


def get_user_input(choice_type, select_dict):
    """
    Prompts the user to select either animal ID from the specified date
    or ROI from the specified animal ID.
    """
    if choice_type == "animal":
        input_prompt = "Select animal ID using corresponding digit: "
        reprompt = "Animal ID: "
    elif choice_type == "ROI":
        input_prompt = "Select ROI using corresponding digit: "
        reprompt = "ROI: "

    # prompts user to select animal ID from available IDs in specified date
    for c, value in select_dict.items():
        print(f"{c}. {value}")

    choice = input(input_prompt)

    while choice not in select_dict:
        choice = input(f"Choose one of: {', '.join(select_dict)}: ")
    print(f"{reprompt}{select_dict[choice]}")

    return select_dict[choice]


def choose_criteria(main_directory, choice_type, date, animal_id=None):

    if choice_type == "animal":
        search_type = "date"

    elif choice_type == "ROI":
        search_type = "animal"

    folders = search_matching_folders(
        main_directory, search_type, date, animal_id
    )
    select_dict = make_choices_dict(folders)
    selected_criteria = get_user_input(choice_type, select_dict)

    return selected_criteria


def get_user_selections(main_directory):
    """
    Contains functions prompting user for date, animal ID, and ROI. 
    """

    date = get_session_date()
    selected_animal = choose_criteria(main_directory, "animal", date)
    selected_ROI = choose_criteria(
        main_directory, "ROI", date, selected_animal
    )

    return date, selected_animal, selected_ROI


def run_analysis(main_directory, date, animal, ROI):
    """
    Runs the analysis for one imaging session.
    """

    data = ImagingSession(main_directory, date, animal, ROI)
    data.get_solenoid_order()
    data.rename_first_trial_txt()
    data.read_txt_file()


class ImagingSession(object):
    def __init__(self, root_dir, date, animal_id, ROI_id):

        self.date = date
        self.animal_id = animal_id
        self.ROI_id = ROI_id
        self.solenoid_order = None

        # Sets path to folder holding all the txt files for analysis.
        self.session_path = (
            f"{root_dir}/{self.date}--{self.animal_id}_{self.ROI_id}"
        )

    def get_solenoid_order(self):
        """
        Reads .txt file from Python to get solenoid order
        """

        solenoid_filename = (
            self.date
            + "_"
            + self.animal_id
            + "_"
            + self.ROI_id
            + "_solenoid_info.txt"
        )

        solenoid_path = Path(self.session_path, solenoid_filename)

        # reads first line of solenoid order txt file
        with open(solenoid_path) as f:
            solenoid_order_raw = f.readline()

        # removes non-numeric characters from solenoid order string
        solenoid_order_num = re.sub("[^0-9]", "", solenoid_order_raw)
        self.solenoid_order = [int(x) for x in solenoid_order_num]

    def rename_first_trial_txt(self):
        """
        Adds "_000.txt" to the end of the txt file name for the first trial.
        Doesn't do anything if the file has already been renamed previously.
        """

        first_trial_name = f"{self.date}--{self.animal_id}_{self.ROI_id}"
        first_trial_path = Path(self.session_path, first_trial_name + ".txt")

        # check whether the first trial txt exists
        if os.path.isfile(first_trial_path):

            print("Adding _000.txt to the end of the first trial txt file.")
            os.rename(
                first_trial_path,
                Path(self.session_path, f"{first_trial_name}_000.txt"),
            )
        elif os.path.isfile(
            Path(self.session_path, f"{first_trial_name}_000.txt")
        ):
            print("First trial txt file is already named correctly.")

    def read_txt_file(self):
        """
        Reads a single txt file from one trial into a dataframe.
        """
        file = f"{self.date}--{self.animal_id}_{self.ROI_id}_000.txt"
        txt_df = pd.read_csv(Path(self.session_path, file))
        pdb.set_trace()


def main():
    main_directory = set_main_directory()
    date, selected_animal, selected_ROI = get_user_selections(main_directory)

    # confirms user selection and provides option to restart selection
    while True:
        confirm = input(
            f"You've chosen Date {date}, animal ID {selected_animal}, and \n"
            f"{selected_ROI}. Press y to start analysis, or n to restart \n"
            f"selection."
        )

        if confirm not in ("y", "n"):
            print("Invalid input. Type y or n.")
            break

        if confirm == "n":
            date, selected_animal, selected_ROI = get_user_selections(
                main_directory
            )
        else:
            break

    print("Continuing with analysis...")

    run_analysis(main_directory, date, selected_animal, selected_ROI)


if __name__ == "__main__":
    main()

