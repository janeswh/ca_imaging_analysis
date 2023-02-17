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
    st.set_page_config(page_title="Load & Analyze .txt files")
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


def choose_run_type():
    """
    Asks user whether they want to export the solenoid info as csv, or do the
    analysis as normal.
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
    """
    Runs the analysis for one imaging session.
    """

    data = ImagingSession(
        folder_path, date, animal, ROI, sample_type, drop_trial
    )
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
            data.get_txt_file_paths()
            data.iterate_txt_files()  # iterates over each txt file and extracts data

            if drop_trial:
                data.drop_trials()

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
                data.save_raw_sample_data(
                    raw_means, data.n_column_labels[n_count]
                )

                # performs analysis for each sample
                analysis_df = data.analyze_signal(avg_means)

                # save avg_means to xlxs file
                data.save_avg_means(avg_means, data.n_column_labels[n_count])

                # save analyses values to xlxs file
                data.save_sig_analysis(
                    analysis_df, data.n_column_labels[n_count]
                )

                bar.set_description(
                    f"Analyzing {sample_type} {n_count+1}", refresh=True
                )

            st.info("Analysis finished.")


class ImagingSession(object):
    def __init__(
        self, folder_path, date, animal_id, ROI_id, sample_type, drop_trials
    ):
        self.date = date
        self.animal_id = animal_id
        self.ROI_id = ROI_id
        self.sample_type = sample_type
        self.solenoid_order = None
        self.solenoid_df = None
        self.txt_paths = None
        self.total_n = None
        self.n_column_labels = None
        self.num_frames = None

        # Sets path to folder holding all the txt files for analysis.
        self.session_path = folder_path

        # determines whether trials need to be dropped
        if drop_trials:
            temp_drops = drop_trials.split(",")
            self.drop_trials_list = [int(x) for x in temp_drops]

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

        # makes df of solenoid info for export as csv
        solenoid_info_df = pd.DataFrame({"Odor": self.solenoid_order})
        solenoid_info_df["Trial"] = range(1, len(solenoid_info_df) + 1)
        solenoid_info_df.sort_values(by=["Odor"], inplace=True)

        self.solenoid_df = solenoid_info_df

    def rename_txt(self):
        """
        Checks to see whether the data .txt files are named correctly, if not,
        renames them.
        """

        # pulls out txt file names, excluding solenoid file
        data_files = [
            x
            for x in os.listdir(self.session_path)
            if "solenoid" not in x and ".txt" in x
        ]

        # sorts the file names according to 000-001, etc
        file_names = sorted(data_files, key=lambda x: x[-7:-4])

        # checks whether files have been renamed
        first_trial_name = f"{self.date}--{self.animal_id}_{self.ROI_id}"

        # check whether the first trial txt exists
        if os.path.isfile(
            Path(self.session_path, f"{first_trial_name}_000.txt")
        ):
            st.info(
                ".txt files are already in the correct format; proceeding with analysis."
            )

        else:
            st.info("Renaming .txt files to the correct format.")
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
            st.info(".txt files renamed; proceeding with analysis.")

    def get_txt_file_paths(self):
        """
        Creates list of paths for all text files, excluding solenoid info
        """
        self.txt_paths = [
            str(path)
            for path in Path(self.session_path).rglob("*.txt")
            if "solenoid" not in path.stem
        ]

    def iterate_txt_files(self):
        """
        Iterates through txt files, opens them as csv and converts each file to
        dataframe, then collects everything inside a dict.
        """
        # sorts the paths according to 000-001, etc
        paths = sorted(self.txt_paths, key=lambda x: int(x[-7:-4]))

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

        # keep first tree column names
        old_cols = all_data_df.columns[:3].tolist()
        mean_cols = len(all_data_df.columns) - 3

        # make new column names based on sample type
        new_cols = [f"{self.sample_type} {i}" for i in range(1, mean_cols + 1)]

        all_data_df.columns = old_cols + new_cols

        self.total_n = sum(
            self.sample_type in col for col in all_data_df.columns
        )
        self.n_column_labels = new_cols

        self.all_data_df = all_data_df

    def drop_trials(self):
        """
        Drops excluded trials from all_data_df
        """

        self.all_data_df = self.all_data_df.loc[
            ~self.all_data_df["Trial"].isin(self.drop_trials_list)
        ]

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

    def save_solenoid_info(self):
        """
        Saves the solenoid info (odor # by trial) as csv.
        """
        fname = f"{self.date}_{self.animal_id}_{self.ROI_id}_solenoid_info.csv"
        csv_path = Path(self.session_path, fname)

        self.solenoid_df.to_csv(csv_path, index=False)

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

    clicked = make_pick_folder_button()
    if clicked:
        st.session_state.dir_path = pop_folder_selector()

    select_manual = st.button("Enter folder path manually")
    if select_manual or st.session_state.manual_path:
        st.session_state.manual_path = True
        st.session_state.dir_path = st.text_input(
            "Enter full path of the folder, e.g. "
            "/Users/Bob/Experiments/2019_GCaMP6s/220101--123456-7-8_ROI1 "
            " and make sure there are no spaces in the path."
        )

    if st.session_state.dir_path:
        date, animal_id, roi = get_selected_folder_info(
            st.session_state.dir_path
        )

        # if folder has been selected properly, proceed

        if date:
            st.session_state.run_type = choose_run_type()

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
        else:
            # tells user to pick directory properly
            st.error(
                "Please ensure that you've selected the desired folder by "
                "opening it in the file dialog and that it's named correctly."
            )


if __name__ == "__main__":
    main()
