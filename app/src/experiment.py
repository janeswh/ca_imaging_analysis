"""Contains classes for loading either .txt files or .xlsx summary files."""

import pandas as pd
import streamlit as st
from pathlib import Path
import re
import os
import numpy as np
import pdb

from src.utils import read_txt_file, save_to_excel, save_to_csv


class RawFolder(object):
    """Runs and stores the analysis for a folder containing raw .txt files.

    For the purposes of this class, a trial represents the data contained in
    one .txt file, and a sample is the cell/glomerulus/grid (user's choice)
    being imaged.

    Attributes:
        date (str): The date of the experiment.
        animal_id (str): The animal ID from the experiment.
        ROI_id (str): The ROI imaged in the experiment.
        file_prefix (str): Prefix for the experiment metadata, used for
            formatting.
        sample_type (str): The sample type, e.g. "Cell", "Glomerulus", or "Grid".
        solenoid_order (list): The order of odors/solenoids delivered in the
            experiment.
        solenoid_df (pd.DataFrame): The solenoid order, with Trial and Odor as
            columns.
        total_n (int): The total number of trials in the experiment.
        n_column_labels (list): The sheet names for exported .xlsx.
        all_data_df (pd.DataFrame): The df holding the collected fluorescence
            values from every frame for every trial and odor for all .txt files.
        session_path (str): The path to the selected folder.
        drop_trials_list (list): Trials to drop, if selected.

    """

    def __init__(
        self,
        folder_path: str,
        date: str,
        animal_id: str,
        ROI_id: str,
        sample_type: str,
        drop_trials: bool,
    ):
        """Initializes an instance of RawFolder() for the selected folder.

        Args:
            folder_path: Path to the folder to run the analysis for.
            date: Date of the experiment (YYYYMMDD).
            animal: Name of the animal being analysed.
            ROI: Region of Interest.
            sample_type: Type of sample being analysed.
            drop_trial: Whether to drop trials.
        """
        self.date = date
        self.animal_id = animal_id
        self.ROI_id = ROI_id
        self.file_prefix = f"{self.date}_{self.animal_id}_{self.ROI_id}"
        self.sample_type = sample_type
        self.solenoid_order = []
        self.solenoid_df = None
        self.total_n = None
        self.n_column_labels = None
        self.all_data_df = None

        # Sets path to folder holding all the txt files for analysis.
        self.session_path = folder_path

        # determines whether trials need to be dropped
        if drop_trials:
            temp_drops = drop_trials.split(",")
            self.drop_trials_list = [int(x) for x in temp_drops]

    def get_solenoid_order(self):
        """Reads .csv or .txt solenoid file to get solenoid order."""

        for filename in os.listdir(self.session_path):
            solenoid_path = Path(self.session_path, filename)

            # This ignores temp files if csv file is open in Excel
            if ".~lock" not in filename and "._" not in filename:
                # For new delivery code with solenoid_order.csv file
                if "solenoid_order" in filename:
                    solenoid_data = pd.read_csv(solenoid_path)
                    self.solenoid_df = solenoid_data

                    temp_solenoid_df = solenoid_data.copy()
                    temp_solenoid_df.sort_values(by=["Trial"], inplace=True)
                    self.solenoid_order = temp_solenoid_df.iloc[:, 0].tolist()

                # For Beichen's old code with solenoid_info.txt file
                elif "solenoid_info.txt" in filename:
                    with open(solenoid_path) as f:
                        solenoid_data = f.readline()
                        # removes non-numeric characters from solenoid order string
                        solenoid_order_num = re.sub(
                            "[^0-9]", "", solenoid_data
                        )
                        self.solenoid_order = [
                            int(x) for x in solenoid_order_num
                        ]

                        # makes df of solenoid info for export as csv
                        solenoid_info_df = pd.DataFrame(
                            {"Odor": self.solenoid_order}
                        )
                        solenoid_info_df["Trial"] = range(
                            1, len(solenoid_info_df) + 1
                        )
                        solenoid_info_df.sort_values(by=["Odor"], inplace=True)
                        self.solenoid_df = solenoid_info_df

    def rename_correct_format(
        self, m: re.Match, filename: str, _ext: str, first: bool = False
    ):
        """Renames .txt files to the correct format.

        Args:
            m: A regex match object for re-numbering .txt file names.
            filename: The original file name.
            _ext: The extension of the file.
            first: Whether the file being renamed is the first trial.
        """

        if first:
            file_number = str(0).zfill(3)
        else:
            file_number = m.group(1).zfill(3)

        os.rename(
            Path(self.session_path, filename),
            Path(
                self.session_path,
                f"{self._exp_name}_{file_number}{_ext}",
            ),
        )

    @property
    def _exp_name(self):
        """str: The expected prefix of the original .txt file names."""
        return f"{self.date}--{self.animal_id}_{self.ROI_id}"

    @property
    def _csv_filename(self):
        """str: The file name for exporting .csv file."""
        return f"{self.file_prefix}_solenoid_info.csv"

    def rename_txt(self, status: st.status):
        """Renames .txt files if needed.

        Args:
            status: st.status container to update progress message
        """

        # pulls out txt file names, excluding solenoid file
        data_files = [
            x
            for x in os.listdir(self.session_path)
            if "solenoid" not in x and ".txt" in x
        ]

        # sorts the file names according to 000-001, etc
        file_names = sorted(data_files, key=lambda x: x[-7:-4])

        # check whether the first trial txt exists
        if os.path.isfile(
            Path(self.session_path, f"{self._exp_name}_000.txt")
        ):
            st.write(".txt files are already in the correct format.")

        else:
            st.write("Renaming .txt files to the correct format.")
            # renames text files
            _ext = ".txt"
            endsWithNumber = re.compile(r"(\d+)" + (re.escape(_ext)) + "$")
            for filename in file_names:
                m = endsWithNumber.search(filename)

                if m:
                    self.rename_correct_format(m, filename, _ext)

                # this renames the first trial text file and adds 000
                else:
                    self.rename_correct_format(m, filename, _ext, first=True)
            st.write(".txt files renamed.")

    def get_txt_file_paths(self) -> list:
        """Creates list of paths for all text files, excluding solenoid info.

        Returns:
            A list of all the .txt files.
        """

        paths_list = [
            str(path)
            for path in Path(self.session_path).rglob("*.txt")
            if "solenoid" not in path.stem
        ]

        return paths_list

    def iterate_txt_files(self, txt_paths: str) -> pd.DataFrame:
        """Collects all .txt files data into one dataframe.

        Args:
            txt_paths: The paths to all the .txt files in the directory.

        Returns:
            all_data_df: A DataFrame holding fluorescence values from all
                frames and trials for each odor, from all .txt files.
        """

        if not txt_paths:
            raise Exception("No .txt files in directory")

        # sorts the paths according to 000-001, etc
        paths = sorted(txt_paths, key=lambda x: int(x[-7:-4]))

        # makes one big df containing all txt data from all trials
        all_data_df = pd.DataFrame()

        for trial_num, path in enumerate(paths):
            df = read_txt_file(path)
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

        return all_data_df

    def organize_all_data_df(self, all_data_df: pd.DataFrame):
        """Formats the df containing raw data for all .txt files.

        Creates column names based on selected sample type.

        Args:
            all_data_df: A DataFrame holding fluorescence values from all
                frames and trials for each odor, from all .txt files.
        """

        # keep first three column names
        old_cols = all_data_df.columns[:3].tolist()
        mean_cols = len(all_data_df.columns) - 3

        # make new column names based on sample type
        new_cols = [f"{self.sample_type} {i}" for i in range(1, mean_cols + 1)]

        all_data_df.columns = old_cols + new_cols

        self.total_n = sum(
            self.sample_type in col for col in all_data_df.columns
        )
        self.n_column_labels = new_cols

        self.all_data_df = all_data_df.copy()

    def process_txt_data(self, n_count: int, sample_type: str) -> str:
        """Performs and saves analyses on the raw data from .txt files.

        Analysis will generate three .xlsx files:
            _analysis.xlsx, containing experiment analysis values
            _avg_means.xlsx, containing the avg fluorescence intensity values
                for each odor
            _raw_means.xlsx, containing the raw fluorescence intensity values
                for all trials for each odor

        Args:
            n_count: The trial number currently being analyzed (for iterating)
            sample_type: The selected sample type.

        Returns:
            bar_txt: The text description for updating the progress bar.

        """

        raw_means, avg_means = self.collect_per_sample(
            self.all_data_df, self.n_column_labels[n_count]
        )

        # performs analysis for each sample
        analysis_df = self.analyze_signal(avg_means)

        # Saving to Excel
        sheet_name = self.n_column_labels[n_count]

        # Save raw means to xlsx file
        save_to_excel(
            self.session_path,
            self.n_column_labels[n_count],
            f"{self.file_prefix}_raw_means.xlsx",
            raw_means,
        )

        # save avg_means to xlxs file
        avgmeans_fname = f"{self.file_prefix}_avg_means.xlsx"
        save_to_excel(self.session_path, sheet_name, avgmeans_fname, avg_means)

        # save analyses values to xlxs file
        analysis_fname = f"{self.file_prefix}_analysis.xlsx"
        save_to_excel(
            self.session_path, sheet_name, analysis_fname, analysis_df
        )

        bar_txt = f"Analyzing {sample_type} {n_count+1}"

        return bar_txt

    def drop_trials(self):
        """Drops excluded trials from all_data_df."""

        self.all_data_df = self.all_data_df.loc[
            ~self.all_data_df["Trial"].isin(self.drop_trials_list)
        ]

    def collect_per_sample(
        self, all_data_df: pd.DataFrame, sample: str
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Collects the mean values from all trials for one sample.

        Args:
            all_data_df: A DataFrame holding fluorescence values from all
                    frames and trials for each odor, from all .txt files.
            sample: The sample currently being collected.

        Returns:
            A tuple (sorted_df, means), where sorted_df contains the raw mean
            fluorescence values for each sample, and means, which contains the
            mean of means.
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

    def analyze_signal(self, avg_means: pd.DataFrame) -> pd.DataFrame:
        """A wrapper function for analyzing mean fluorescence values.

        Args:
            avg_means: The mean of mean fluorescence values from one sample.

        Returns:
            A DataFrame containing all the analysis values gathered for one
                sample.
        """

        (
            baseline,
            peak,
            deltaF,
            baseline_stdx3,
            deltaF_blank,
            blank_sub_deltaF,
            blank_sub_deltaF_F_perc,
            baseline_subtracted,
        ) = self.calculate_initial_nums(avg_means)

        # Determines whether response is significant by checking whether
        # blank_sub_deltaF is greater than baseline_stdx3.
        significance_bool = blank_sub_deltaF > baseline_stdx3
        sig_odors = significance_bool[significance_bool].index.values

        significance_report = significance_bool.copy()
        significance_report[sig_odors] = blank_sub_deltaF_F_perc[sig_odors]
        significance_report = pd.Series(significance_report)

        auc, auc_blank = self.calc_auc(avg_means, baseline=baseline)

        (
            blank_sub_auc,
            peak_times,
            odor_onset,
            response_onset,
            latency,
            time_to_peak,
        ) = self.analyze_sig_responses(
            sig_odors=sig_odors,
            avg_means=avg_means,
            auc=auc,
            auc_blank=auc_blank,
            deltaF=deltaF,
            baseline_subtracted=baseline_subtracted,
        )

        response_analyses_df = self.make_analysis_df(
            avg_means,
            baseline=baseline,
            peak=peak,
            deltaF=deltaF,
            baseline_stdx3=baseline_stdx3,
            deltaF_blank=deltaF_blank,
            blank_sub_deltaF=blank_sub_deltaF,
            blank_sub_deltaF_F_perc=blank_sub_deltaF_F_perc,
            significance_report=significance_report,
            auc=auc,
            auc_blank=auc_blank,
            blank_sub_auc=blank_sub_auc,
            peak_times=peak_times,
            odor_onset=odor_onset,
            response_onset=response_onset,
            latency=latency,
            time_to_peak=time_to_peak,
        )

        return response_analyses_df

    def calculate_initial_nums(
        self, avg_means: pd.DataFrame
    ) -> tuple[
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.Series,
        pd.DataFrame,
    ]:
        """Performs initial calculations for mean fluorescence values.

        Args:
            avg_means: The mean of mean fluorescence values from one sample.

        Returns:
            A tuple containing the following pd.Series/DataFrame (one value
            per odor):
                baseline: The fluorescence values from defined baseline period.
                peak: The max fluorescence value during trial period.
                deltaF: The change in fluorescence value from peak and baseline.
                baseline_stdx3: Three standard deviations of baseline.
                deltaF_blank: The deltaF value of the blank odor (last odor).
                blank_sub_deltaF: The deltaF value with the blank odor's
                    deltaF subtracted to remove blank response.
                blank_sub_deltaF_F_perc: The blank-subtracted deltaF as a
                    percent of baseline.
                baseline_subtracted: The average fluorescence value, with
                    baseline subtracted.
        """
        baseline = avg_means[:52].mean()

        # Calculates peak using max value from frames #53-300
        peak = avg_means[52:300].max()
        deltaF = peak - baseline
        baseline_stdx3 = avg_means[:52].std() * 3

        deltaF_blank = deltaF[avg_means.columns[-1]]
        blank_sub_deltaF = deltaF - deltaF_blank
        blank_sub_deltaF_F_perc = blank_sub_deltaF / baseline * 100
        baseline_subtracted = avg_means - baseline

        return (
            baseline,
            peak,
            deltaF,
            baseline_stdx3,
            deltaF_blank,
            blank_sub_deltaF,
            blank_sub_deltaF_F_perc,
            baseline_subtracted,
        )

    def calc_auc(
        self, avg_means: pd.DataFrame, baseline: pd.Series
    ) -> tuple[pd.Series, np.float64]:
        """Calculates area under curve (AUC).

        Args:
            avg_means: The mean of mean fluorescence values from one sample.
            baseline: Baseline fluorescence values.

        Returns:
            A tuple containing a pd.Series (AUC values for each odor) and
            a np.float64 value (AUC value for blank odor).

        """

        # Calculates AUC using sum of values from frames # 1-300
        auc = (avg_means[:300].sum() - (baseline * 300)) * 0.0661
        auc.clip(lower=0, inplace=True)  # Sets negative AUC values to 0

        # Gets AUC_blank from AUC of the last odor
        auc_blank = auc[avg_means.columns[-1]]

        return auc, auc_blank

    def analyze_sig_responses(
        self,
        sig_odors: np.ndarray,
        avg_means: pd.DataFrame,
        auc: pd.Series,
        auc_blank: np.float64,
        deltaF: pd.Series,
        baseline_subtracted: pd.DataFrame,
    ) -> tuple[pd.Series, pd.Series, float, pd.Series, pd.Series, pd.Series]:
        """Analyzes odor responses for significant responses only.

        Args:
            sig_odors: Odors with significant responses.
            avg_means: The mean of mean fluorescence values from one sample.
            auc: The area under curve values for all odor.
            auc_blank: The area under curve values for the blank odor.
            deltaF: The deltaF values for all odors.
            baseline_subtracted: The baseline-subtracted fluorescence values.

        Returns:
            blank_sub_auc: The AUC, minus the blank AUC.
            peak_times: The times of peak fluorescence for all odors.
            odor_onset: The odor onset time for all odors (frame 57).
            response_onset: The response onset times for all odors.
            latency: The latency to response onset from odor onset.
            time_to_peak: The times from response onset to response peak.
        """

        # Creates 'N/A' template for non-significant odor responses
        na_template = pd.Series("N/A", index=avg_means.columns)

        # Calculates blank-subtracted AUC only if response is present
        blank_sub_auc = na_template.copy()
        blank_sub_auc[sig_odors] = auc[sig_odors] - auc_blank

        # Calculates time at signal peak using all the frames
        # why does excel sheet have - 2??
        max_frames = avg_means[40:300].idxmax()
        peak_times = na_template.copy()
        peak_times[sig_odors] = max_frames[sig_odors] * 0.0661

        # Get odor onset - Frame 57
        odor_onset = 57 * 0.0661

        # Calculate response onset only for significant odors
        response_onset = na_template.copy()
        onset_amp = deltaF * 0.05

        for sig_odor in sig_odors:
            # Window doesn't start at frame 53 because it can't precede
            #  odor onset
            window = baseline_subtracted[40:300][sig_odor]
            onset_idx = np.argmax(window >= onset_amp[sig_odor])
            onset_time = window.index[onset_idx] * 0.0661
            response_onset[sig_odor] = onset_time

        latency = na_template.copy()
        latency[sig_odors] = response_onset[sig_odors] - odor_onset

        time_to_peak = na_template.copy()
        time_to_peak[sig_odors] = (
            peak_times[sig_odors] - response_onset[sig_odors]
        )

        return (
            blank_sub_auc,
            peak_times,
            odor_onset,
            response_onset,
            latency,
            time_to_peak,
        )

    def make_analysis_df(
        self,
        avg_means: pd.DataFrame,
        baseline: pd.Series,
        peak: pd.Series,
        deltaF: pd.Series,
        baseline_stdx3: pd.Series,
        deltaF_blank: pd.Series,
        blank_sub_deltaF: pd.Series,
        blank_sub_deltaF_F_perc: pd.Series,
        significance_report: pd.Series,
        auc: pd.Series,
        auc_blank: np.float64,
        blank_sub_auc: pd.Series,
        peak_times: pd.Series,
        odor_onset: float,
        response_onset: pd.Series,
        latency: pd.Series,
        time_to_peak: pd.Series,
    ) -> pd.DataFrame:
        """Places analysis results into a df.

        Args:
            avg_means: The mean of mean fluorescence values from one sample.
            baseline: The fluorescence values from defined baseline period.
            peak: The max fluorescence value during the trial period.
            deltaF: The change in fluorescence value from peak and baseline.
            baseline_stdx3: Three standard deviations of baseline.
            deltaF_blank: deltaF value of the blank odor (last odor).
            blank_sub_deltaF: deltaF values with the blank odor's deltaF
                subtracted to remove blank response.
            blank_sub_deltaF_F_perc: The blank-subtracted deltaF as a
                percent of baseline.
            significance report: A Series of denoting whether an odor had a
                significant response; if yes, print blank_sub_deltaF_F_perc,
                else print FALSE.
            auc: The area under curve values for all odor.
            auc_blank: The area under curve values for the blank odor.
            blank_sub_auc: The AUC, minus the blank AUC.
            peak_times: The times of peak fluorescence for all odors.
            odor_onset: The odor onset time for all odors (frame 57).
            response_onset: The response onset times for all odors.
            latency: The latency to response onset from odor onset.
            time_to_peak: The times from response onset to response peak.

        Returns:
            All the analysis results in a DataFrame, with rows as measurement
            labels and columns as Odor #.
        """

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

        num_odors = len(avg_means.columns)
        series_axis = range(1, num_odors + 1)

        odor_labels = pd.Series([f"Odor {x}" for x in series_axis]).set_axis(
            series_axis
        )

        deltaF_blank_series = pd.Series([deltaF_blank] * num_odors).set_axis(
            series_axis
        )

        auc_blank_series = pd.Series([auc_blank] * num_odors).set_axis(
            series_axis
        )

        odor_onset_series = pd.Series([odor_onset] * num_odors).set_axis(
            series_axis
        )

        series_list = [
            odor_labels,
            baseline,
            peak,
            deltaF,
            baseline_stdx3,
            deltaF_blank_series,
            blank_sub_deltaF,
            blank_sub_deltaF_F_perc,
            significance_report,
            auc,
            auc_blank_series,
            blank_sub_auc,
            peak_times,
            odor_onset_series,
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
        """Saves the solenoid info (odor # by trial) as csv."""
        fname = self._csv_filename
        save_to_csv(fname, self.session_path, self.solenoid_df)


class ExperimentFile(object):
    """Extracts the values from the analysis.xlsx file of a given imaging
    session. Used to collate analyses from all imaging sessions in a given
    acute or chronic dataset.

    Attributes:
        file: streamlit.runtime.uploaded_file_manager.UploadedFile of csv file
        dataset_type (str): Chronic or acute experiment type.
        date (str): The date of the experiment.
        animal_id (str): The animal ID from the experiment.
        ROI_id (str): The ROI imaged in the experiment.
        exp_name (str): The name of the experiment imaging session.
        sample_type (str): The sample type, e.g. "Cell", "Glomerulus", or "Grid".
        tuple_dict (dict): A dictionary containing tuples  of
            (sample #, odor #) as keys and the analysis values of that sample
            and odor pair as the values.
    """

    def __init__(self, file: str, dataset_type: str):
        """Initializes an instance of ExperimentFile() for the dataset.

        Args:
            file: streamlit.runtime.uploaded_file_manager.UploadedFile, csv file
            dataset_type: Chronic or acute experiment type.
            date (str): The date of the experiment.
            animal_id (str): The animal ID from the experiment.
            ROI_id (str): The ROI imaged in the experiment.
            exp_name (str): The name of the experiment imaging session.
            sample_type (str): The sample type, e.g. "Cell", "Glomerulus", or "Grid".
            tuple_dict (dict): A dictionary containing tuples  of
                (sample #, odor #) as keys and the analysis values of that sample
                and odor pair as the values.
        """

        self.file = file
        self.dataset_type = dataset_type
        file_parts = file.name.split("_")[0:3]  # this is a list
        self.date, self.animal_id, self.roi = file_parts
        self.exp_name = "_".join(file_parts)

        self.sample_type = None
        self.tuple_dict = None

    def import_excel(self) -> dict:
        """Imports data from each .xlsx file into a dictionary.

        Returns:
            A dictionary containing measurement values from the analysis.xlsx
            file, with sample # as keys.
        """
        data_dict = pd.read_excel(
            self.file,
            sheet_name=None,
            header=1,
            index_col=0,
            na_values="FALSE",
            dtype="object",
        )

        return data_dict

    # def shared_method(self):
    #     do stuff

    #     if chronic:
    #         do stuff
    #     elif acute:
    #         do other stuff

    def sort_data(self, data_dict: dict, df_list: list) -> list:
        """Converts dicts containing .analysis data into DataFrames for each
        measurement (e.g. "Time to peak (s)").

        Args:
            data_dict: A dictionary containing measurement values from
                the analysis.xlsx file, with sample # as keys.
            df_list: A list of DataFrames to hold the values for each
                measurement.

        Returns:
            A list of a list of DataFrames, one list for each measurement.
                Values from each new .xlsx file are appended as new rows in the
                DataFrames in df_list.
        """

        self.tuple_dict = {
            (outerKey, innerKey): values
            for outerKey, innerDict in data_dict.items()
            for innerKey, values in innerDict.items()
        }

        mega_df = pd.DataFrame(self.tuple_dict)
        self.sample_type = mega_df.columns[0][0].split(" ")[0]

        # Replaces values with "" for non-sig responses if not already NaN
        temp_mega_df = mega_df.T
        # temp_mega_df.loc[
        #     temp_mega_df["Significant response?"] == False, "Blank sub AUC"
        # ] = ""
        temp_mega_df.loc[
            temp_mega_df["Significant response?"] == False,
            "Blank-subtracted DeltaF/F(%)",
        ] = ""

        mega_df = temp_mega_df.copy().T
        appended_df_list = [[] for x in range(5)]

        for measure_ct, measure in enumerate(st.session_state.measures):
            temp_measure_df = pd.DataFrame(mega_df.loc[measure]).T.stack().T

            if self.dataset_type == "chronic":
                temp_measure_df["Date"] = self.date
            else:
                temp_measure_df["Animal ID"] = self.animal_id
                temp_measure_df["ROI"] = self.roi

            # Renaming sample names for better sorting
            temp_measure_df.rename(
                index=lambda x: int(x.split(" ")[1]), inplace=True
            )
            temp_measure_df.index.rename(self.sample_type, inplace=True)

            # Append values from this analysis.xlsx file
            concat_pd = pd.concat([df_list[measure_ct], temp_measure_df])
            appended_df_list[measure_ct] = concat_pd

        return appended_df_list

    def make_plotting_dfs(self, data_dict: dict) -> tuple[list, pd.DataFrame]:
        """Makes the DataFrames used for plotting measurements.

        Args:
            data_dict: A dictionary containing measurement values from
                the analysis.xlsx file, with sample # as keys.

        Returns:
            sig_odors: A list of all the significant odors from the experiment.
            sig_data_df: A DataFrame containing only measurements for
                significant responses.
        """

        sig_data_df = pd.DataFrame()
        sig_odors = []

        # drop non-significant colums from each df using NaN values
        for data_df in data_dict.values():
            data_df.dropna(axis=1, inplace=True)

            # extracts measurements to plot
            data_df = data_df.loc[
                [
                    "Baseline",
                    "Blank-subtracted DeltaF/F(%)",
                    "Blank sub AUC",
                    "Latency (s)",
                    "Time to peak (s)",
                ]
            ]

            sig_data_df = pd.concat([sig_data_df, data_df], axis=1)

            # gets list of remaining significant odors
            if len(data_df.columns.values) == 0:
                pass
            else:
                df_sig_odors = data_df.columns.values.tolist()
                sig_odors.append(df_sig_odors)

        return sig_odors, sig_data_df
