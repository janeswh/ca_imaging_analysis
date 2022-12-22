import os
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


def search_matching_date(main_directory_path, date):
    """
    Checks whether the user-entered date is found in directory. If it is,
    return list of available folders with the designated date. If not, print
    error message.
    """
    matching_animals = []

    folders = [
        f.name
        for f in os.scandir(main_directory_path)
        if f.is_dir() and date in f.name
    ]

    if len(folders) == 0:
        print("Please double check the entered date.")

    else:
        for folder in folders:
            # this returns animal ID
            extracted_animal = folder.split("--")[1].split("_")[0]
            matching_animals.append(extracted_animal)

    return matching_animals


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

        if len(folders) == 0:
            print("Please double check the entered date.")

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
    animals = search_matching_date(main_directory, date)

    while len(animals) == 0:
        date = get_session_date()
        animals = search_matching_date(main_directory, date)

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
    data.get_solenoid_order()  # gets odor order from solenoid txt file
    data.rename_first_trial_txt()  # adds _000.txt to end of first trial file
    data.iterate_txt_files()  # iterates over each txt file and extracts data

    # sort all data by neuron/glomerulus
    for n_count in range(data.total_n):
        raw_means, avg_means = data.collect_per_sample(
            data.all_data_df, data.n_column_labels[n_count]
        )

        # saves raw means to xlxs file
        data.save_raw_sample_data(raw_means, data.n_column_labels[n_count])

        # performs analysis for each sample
        data.analyze_signal(avg_means)


class ImagingSession(object):
    def __init__(self, root_dir, date, animal_id, ROI_id):

        self.date = date
        self.animal_id = animal_id
        self.ROI_id = ROI_id
        self.solenoid_order = None
        self.total_n = None
        self.n_column_labels = None
        self.num_frames = None

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

    def iterate_txt_files(self):
        """
        Iterates through txt files, opens them as csv and converts each file to
        dataframe, then collects everything inside a dict.
        """

        # creates list of paths for all text files, excluding solenoid info
        txt_paths = [
            str(path)
            for path in Path(self.session_path).rglob("*.txt")
            if "solenoid" not in path.stem
        ]

        # sorts the paths according to 000-001, etc
        paths = sorted(txt_paths, key=lambda x: int(x[-7:-4]))

        # makes one big df containing all txt data from all trials
        all_data_df = pd.DataFrame()

        for trial_num, path in enumerate(paths):
            df = self.read_txt_file(path)
            odor_num = self.solenoid_order[trial_num]

            # add columns for trial # and odor #
            df["Frame"] = list(range(1, len(df) + 1))
            df["Trial"] = trial_num + 1
            df["Odor"] = odor_num

            # reorder columns
            cols_to_move = ["Frame", "Trial", "Odor"]
            df = df[
                cols_to_move
                + [col for col in df.columns if col not in cols_to_move]
            ]

            all_data_df = pd.concat([all_data_df, df], axis=0)

        self.total_n = sum("Mean" in col for col in all_data_df.columns)
        self.n_column_labels = [
            col for col in all_data_df.columns if "Mean" in col
        ]
        self.all_data_df = all_data_df

    def read_txt_file(self, path):
        """
        Reads a single txt file from one trial into a dataframe.
        """
        # file = f"{self.date}--{self.animal_id}_{self.ROI_id}_000.txt"
        txt_df = pd.read_csv(Path(path), sep="\t", index_col=0)

        return txt_df

    def collect_per_sample(self, all_data_df, sample):
        """
        Collects the mean values from all trials for each neuron/glomerulus.
        Returns the raw means for each sample and the mean of means.
        """
        n_df = all_data_df[["Frame", "Trial", "Odor", sample]]

        # pivots n_df to sort by odor #
        sorted_df = n_df.pivot(
            index="Frame", columns=["Odor", "Trial"], values=sample,
        )

        sorted_df.sort_index(
            axis=1, level=[0, 1], ascending=[True, True], inplace=True
        )
        means = sorted_df.groupby(level=0, axis=1).mean()

        return sorted_df, means

    def analyze_signal(self, avg_means):
        """
        Calculates baseline signal using avg from frames #1-46

        """
        baseline = avg_means[:46].mean()

        # Calculates peak using max value from frames #49-300
        peak = avg_means[48:].max()

        # Calculates deltaF using peak-baseline
        deltaF = peak - baseline

        # Calculates 3 x std of baseline
        baseline_stdx3 = avg_means[:46].std() * 3

        # Get deltaF blank - is this the deltaF of Odor 8?
        deltaF_blank = deltaF[8]

        # Calculates blank-subtracted deltaF
        blank_sub_deltaF = deltaF - deltaF_blank

        # Calculates blanksub_deltaF/F(%)
        blank_sub_deltaF_F_perc = blank_sub_deltaF / baseline * 100

        # Determines whether response is significant by checking whether
        # blank_sub_deltaF is greater than baseline_stdx3.

        significance_bool = blank_sub_deltaF > baseline_stdx3
        # t = pd.Series([True, False])
        # pdb.set_trace()
        # for i in significance_bool:
        #     if i == False:
        #         i = 0
        #     else:
        #         i = blank_sub_deltaF[idx]

        # Calculates baseline-subtracted avg means
        baseline_subtracted = avg_means - baseline

        # Calculates AUC using sum of values from frames # 57-303
        auc = baseline_subtracted[56:303].sum()

        # Gets AUC_blank from AUC of Odor 8
        auc_blank = auc[8]

        # Calculates blank-subtracted AUC
        blank_sub_auc = auc - auc_blank

        # Calculates time at signal peak using all the frames
        # why does excel sheet have - 2??
        max_frames = avg_means[48:].idxmax()
        peak_times = max_frames * 0.0661

        # Get odor onset - how is this calculated?? Frame 57?
        odor_onset = 57 * 0.0661

        # Set frame at which odor response begins - need user input? Or
        # calculated?
        response_frame = 52  # dummy value

        # Calculate response onset
        response_onset = response_frame * 0.0661

        # Calculate latency
        latency = response_onset - odor_onset

        # Calculate time to peak
        time_to_peak = peak_times - response_onset

        pdb.set_trace()

    def save_raw_sample_data(self, raw_means, sheet_name):
        """
        Saves the raw means for each sample into a sheet in xlsx file.
        """
        xlsx_fname = (
            f"{self.date}_{self.animal_id}_{self.ROI_id}_raw_means.xlsx"
        )
        xlsx_path = Path(self.session_path, xlsx_fname)

        # checks whether xlsx file already exists
        if os.path.isfile(xlsx_path):  # if it does, write to existing file
            # if sheet already exists, overwrite it
            with pd.ExcelWriter(
                xlsx_path, mode="a", if_sheet_exists="replace"
            ) as writer:
                raw_means.to_excel(writer, sheet_name)
        else:  # otherwise, write to new file
            raw_means.to_excel(xlsx_path, sheet_name)


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

