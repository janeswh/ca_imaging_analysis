import streamlit as st
import os
import pandas as pd
import numpy as np
from collections import OrderedDict, defaultdict
from pathlib import Path, PureWindowsPath
import re
import tkinter as tk
from tkinter.filedialog import askdirectory
from stqdm import stqdm

import pdb


def set_webapp_params():
    """
    Sets the name of the Streamlit app along with other things
    """
    st.title("ROI Analysis")

    st.markdown(
        "Please select the folder containing the Ca imaging raw .txt files "
        "from the imaging session you want to analyze. The folder should be "
        "named in the format YYMMDD--123456-7-8_ROIX where 123456-7-8 is the "
        "animal ID, and X is the one-digit ROI number."
    )


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

    return date, animal_ID, roi


def make_pick_folder_button():
    """
    Makes the "Pick folder" button and checks whether it has been clicked.
    """
    clicked = st.button("Pick folder")
    return clicked


# @st.cache(suppress_st_warning=True)
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


def confirm_choice():
    """
    Confirms data selection before proceeding with analysis, or gives the
    option to rerun script.
    """
    st.markdown(
        "If the above selections look correct, press Analyze to "
        "proceed with analysis. Otherwise, press Restart to restart "
        "data selection."
    )


def get_main_directory():
    """
    Prompts user for the folder containing txt files to be analyzed.
    """

    dir_path = st.text_input("Selected folder:", askdirectory())
    folder = os.path.basename(dir_path)

    return dir_path, folder


def get_session_info(folder):
    """
    Gets the date, animal ID, and ROI info from the name of the selected
    folder.
    """

    date = folder.split("--")[0]
    animal_ID = folder.split("--")[1].split("_")[0]
    roi = folder.split("_")[1]

    return date, animal_ID, roi


def choose_sample_type():
    """
    Prompts user to select the sample type - cell vs. glomerulus
    """

    choice = st.radio("Select sample type:", ("Cell", "Glomerulus", "Grid"))

    return choice


def run_analysis(folder_path, date, animal, ROI, sample_type):
    """
    Runs the analysis for one imaging session.
    """

    data = ImagingSession(folder_path, date, animal, ROI, sample_type)
    data.get_solenoid_order()  # gets odor order from solenoid txt file
    data.rename_first_trial_txt()  # adds _000.txt to end of first trial file
    data.iterate_txt_files()  # iterates over each txt file and extracts data

    # sort all data by neuron/glomerulus
    # adds progress bar
    bar = stqdm(
        range(data.total_n),
        desc=f"Analyzing {sample_type}",
    )
    for n_count in bar:
        raw_means, avg_means = data.collect_per_sample(
            data.all_data_df, data.n_column_labels[n_count]
        )

        # saves raw means to xlxs file
        data.save_raw_sample_data(raw_means, data.n_column_labels[n_count])

        # performs analysis for each sample
        analysis_df = data.analyze_signal(avg_means)

        # save avg_means to xlxs file
        data.save_avg_means(avg_means, data.n_column_labels[n_count])

        # save analyses values to xlxs file
        data.save_sig_analysis(analysis_df, data.n_column_labels[n_count])

        bar.set_description(
            f"Analyzing {sample_type} {n_count+1}", refresh=True
        )

    st.write("Analysis finished.")


class ImagingSession(object):
    def __init__(self, folder_path, date, animal_id, ROI_id, sample_type):
        self.date = date
        self.animal_id = animal_id
        self.ROI_id = ROI_id
        self.sample_type = sample_type
        self.solenoid_order = None
        self.total_n = None
        self.n_column_labels = None
        self.num_frames = None

        # Sets path to folder holding all the txt files for analysis.
        self.session_path = folder_path

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

        # pulls out txt file names, excluding solenoid file
        data_files = [
            x
            for x in os.listdir(self.session_path)
            if "solenoid" not in x and ".txt" in x
        ]

        # sorts the file names according to 000-001, etc
        file_names = sorted(data_files, key=lambda x: x[-7:-4])

        # renames text files
        _ext = ".txt"
        endsWithNumber = re.compile(r"(\d+)" + (re.escape(_ext)) + "$")
        for filename in file_names:
            m = endsWithNumber.search(filename)

            if m:
                os.rename(
                    Path(self.session_path, filename),
                    Path(
                        self.session_path,
                        str(
                            self.date
                            + "--"
                            + self.animal_id
                            + "_"
                            + self.ROI_id
                            + "_"
                            + m.group(1).zfill(3)
                            + _ext
                        ),
                    ),
                )

            # this renames the first trial text file and adds 000
            else:
                os.rename(
                    Path(self.session_path, filename),
                    Path(
                        self.session_path,
                        str(
                            self.date
                            + "--"
                            + self.animal_id
                            + "_"
                            + self.ROI_id
                            + "_"
                            + str(0).zfill(3)
                            + _ext
                        ),
                    ),
                )

        pdb.set_trace()
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

        # replace column names with sample type
        all_data_df.columns = all_data_df.columns.str.replace(
            "Mean", f"{self.sample_type} "
        )

        self.total_n = sum(
            self.sample_type in col for col in all_data_df.columns
        )
        self.n_column_labels = [
            col for col in all_data_df.columns if self.sample_type in col
        ]

        self.all_data_df = all_data_df

    def read_txt_file(self, path):
        """
        Reads a single txt file from one trial into a dataframe.
        """
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
            index="Frame",
            columns=["Odor", "Trial"],
            values=sample,
        )

        sorted_df.sort_index(
            axis=1, level=[0, 1], ascending=[True, True], inplace=True
        )
        means = sorted_df.groupby(level=0, axis=1).mean()

        return sorted_df, means

    def analyze_signal(self, avg_means):
        """
        Calculates baseline signal using avg from frames #1-52

        """
        baseline = avg_means[:52].mean()

        # Calculates peak using max value from frames #53-300
        peak = avg_means[52:300].max()

        # Calculates deltaF using peak-baseline
        deltaF = peak - baseline

        # Calculates 3 x std of baseline
        baseline_stdx3 = avg_means[:46].std() * 3

        # Get deltaF blank - blank is the last odor
        deltaF_blank = deltaF[avg_means.columns[-1]]

        # Calculates blank-subtracted deltaF
        blank_sub_deltaF = deltaF - deltaF_blank

        # Calculates blanksub_deltaF/F(%)
        blank_sub_deltaF_F_perc = blank_sub_deltaF / baseline * 100

        # Determines whether response is significant by checking whether
        # blank_sub_deltaF is greater than baseline_stdx3.

        significance_bool = blank_sub_deltaF > baseline_stdx3

        # gets odor #s with significant responses
        sig_odors = significance_bool[significance_bool].index.values
        # sig_odors = [1, 5]    # for testing

        # reports False if odor is not significant, otherwise
        # reports blanksub_deltaF/F(%)
        significance_report = significance_bool.copy()
        significance_report[sig_odors] = blank_sub_deltaF_F_perc[sig_odors]
        significance_report = pd.Series(significance_report)

        # Calculates baseline-subtracted avg means
        baseline_subtracted = avg_means - baseline

        # Calculates AUC using sum of values from frames # 1-300
        # formula: (sum(avg_mean_frames1-300) - (baseline*300)) * 0.0661

        auc = (avg_means[:300].sum() - (baseline * 300)) * 0.0661

        # Gets AUC_blank from AUC of the last odor

        auc_blank = auc[avg_means.columns[-1]]

        # Creates 'N/A' template for non-significant odor responses
        na_template = pd.Series("N/A", index=avg_means.columns)

        # Calculates blank-subtracted AUC only if response is present
        blank_sub_auc = na_template.copy()
        blank_sub_auc[sig_odors] = auc[sig_odors] - auc_blank

        # only do the below if response is present

        # Calculates time at signal peak using all the frames
        # why does excel sheet have - 2??
        max_frames = avg_means[:300].idxmax()
        peak_times = na_template.copy()
        peak_times[sig_odors] = max_frames[sig_odors] * 0.0661

        # Get odor onset - Frame 57?
        odor_onset = 57 * 0.0661

        # Calculate response onset only for significant odors
        response_onset = na_template.copy()
        onset_amp = deltaF * 0.05

        for sig_odor in sig_odors:
            window = baseline_subtracted[56:300][sig_odor]
            onset_idx = np.argmax(window >= onset_amp[sig_odor])
            onset_time = window.index[onset_idx] * 0.0661
            response_onset[sig_odor] = onset_time

        # Calculate latency
        latency = na_template.copy()
        latency[sig_odors] = response_onset[sig_odors] - odor_onset

        # Calculate time to peak
        time_to_peak = na_template.copy()
        time_to_peak[sig_odors] = (
            peak_times[sig_odors] - response_onset[sig_odors]
        )

        # puts everything in a df
        col_names = [
            "Odor",
            "Baseline",
            "Peak",
            "DeltaF",
            "3 std of baseline",
            "DeltaF(BLANK)",
            "Blank-subtracted DeltaF",
            "Blank-subtracted DeltaF/F(%)",
            "Significant response?",
            "Area under curve",
            "Blank area under curve",
            "Blank sub AUC",
            "Time at peak (s)",
            "Odor onset",
            "Response onset (s)",
            "Latency (s)",
            "Time to peak (s)",
        ]

        odor_labels = pd.Series(
            [f"Odor {x}" for x in range(1, len(avg_means.columns) + 1)]
        ).set_axis(range(1, len(avg_means.columns) + 1))

        series_list = [
            odor_labels,
            baseline,
            peak,
            deltaF,
            baseline_stdx3,
            pd.Series([deltaF_blank] * len(avg_means.columns)).set_axis(
                range(1, len(avg_means.columns) + 1)
            ),
            blank_sub_deltaF,
            blank_sub_deltaF_F_perc,
            significance_report,
            auc,
            pd.Series([auc_blank] * len(avg_means.columns)).set_axis(
                range(1, len(avg_means.columns) + 1)
            ),
            blank_sub_auc,
            peak_times,
            pd.Series([odor_onset] * len(avg_means.columns)).set_axis(
                range(1, len(avg_means.columns) + 1)
            ),
            response_onset,
            latency,
            time_to_peak,
        ]

        response_analyses_df = pd.concat(
            series_list, axis=1, ignore_index=True
        )

        response_analyses_df.columns = col_names
        response_analyses_df = response_analyses_df.T

        return response_analyses_df

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

    def save_sig_analysis(self, stats, sheet_name):
        """
        Saves the signal analysis for each sample into a sheet in xlsx file.
        """
        xlsx_fname = (
            f"{self.date}_{self.animal_id}_{self.ROI_id}_analysis.xlsx"
        )
        xlsx_path = Path(self.session_path, xlsx_fname)

        # checks whether xlsx file already exists
        if os.path.isfile(xlsx_path):  # if it does, write to existing file
            # if sheet already exists, overwrite it
            with pd.ExcelWriter(
                xlsx_path, mode="a", if_sheet_exists="replace"
            ) as writer:
                stats.to_excel(writer, sheet_name)
        else:  # otherwise, write to new file
            stats.to_excel(xlsx_path, sheet_name)

    def save_avg_means(self, avg_means, sheet_name):
        """
        Saves the avg means for each sample into a sheet in xlsx file.
        """
        xlsx_fname = (
            f"{self.date}_{self.animal_id}_{self.ROI_id}_avg_means.xlsx"
        )
        xlsx_path = Path(self.session_path, xlsx_fname)

        # checks whether xlsx file already exists
        if os.path.isfile(xlsx_path):  # if it does, write to existing file
            # if sheet already exists, overwrite it
            with pd.ExcelWriter(
                xlsx_path, mode="a", if_sheet_exists="replace"
            ) as writer:
                avg_means.to_excel(writer, sheet_name)
        else:  # otherwise, write to new file
            avg_means.to_excel(xlsx_path, sheet_name)


def main():
    set_webapp_params()

    # # # --- Initialising SessionState ---

    if "dir_path" not in st.session_state:
        st.session_state.dir_path = False
    if "sample_type" not in st.session_state:
        st.session_state.sample_type = False

    clicked = make_pick_folder_button()

    if clicked:
        st.session_state.dir_path = pop_folder_selector()

    if st.session_state.dir_path:
        date, animal_id, roi = get_selected_folder_info(
            st.session_state.dir_path
        )

        # if folder has been selected properly, proceed
        # pdb.set_trace()
        if date:
            st.session_state.sample_type = choose_sample_type()
            # confirm_choice()

            if st.button("Analyze"):
                run_analysis(
                    st.session_state.dir_path,
                    date,
                    animal_id,
                    roi,
                    st.session_state.sample_type,
                )
        else:
            # tells user to pick directory properly
            st.error(
                "Please ensure that you've selected the desired folder by "
                "opening it in the file dialog and that it's named correctly."
            )


if __name__ == "__main__":
    main()
