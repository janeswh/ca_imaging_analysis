import pandas as pd
import streamlit as st
from pathlib import Path
import re
import os
import numpy as np
import pdb

from src.utils import read_txt_file, save_to_excel, save_to_csv


class RawFolder(object):
    def __init__(
        self, folder_path, date, animal_id, ROI_id, sample_type, drop_trials
    ):
        self.date = date
        self.animal_id = animal_id
        self.ROI_id = ROI_id
        self.file_prefix = f"{self.date}_{self.animal_id}_{self.ROI_id}"
        self.sample_type = sample_type
        self.solenoid_order = None
        self.solenoid_df = None
        self.txt_paths = None
        self.total_n = None
        self.n_column_labels = None
        self.num_frames = None
        self.sig_odors = None

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

        # solenoid_filename = (
        #     self.date
        #     + "_"
        #     + self.animal_id
        #     + "_"
        #     + self.ROI_id
        #     + "_solenoid_info.txt"
        # )

        # solenoid_filename = (
        #     f"{self.date}_{self.animal_id}_{self.ROI_id}_"
        #     f"soenoid_info.txt"
        # )

        solenoid_filename = [self.date, self.animal_id, self.ROI_id].join("_")
        solenoid_filename += "_solenoid_info.txt"

        solenoid_path = Path(self.session_path, solenoid_filename)

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

        # removes non-numeric characters from solenoid order string
        solenoid_order_num = re.sub("[^0-9]", "", solenoid_order_raw)
        self.solenoid_order = [int(x) for x in solenoid_order_num]

        # makes df of solenoid info for export as csv
        solenoid_info_df = pd.DataFrame({"Odor": self.solenoid_order})
        solenoid_info_df["Trial"] = range(1, len(solenoid_info_df) + 1)
        solenoid_info_df.sort_values(by=["Odor"], inplace=True)

        self.solenoid_df = solenoid_info_df

    def rename_correct_format(self, m, filename, _ext):
        """
        Renames .txt files to correct format
        """
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

    def rename_first_txt(self, filename, _ext):
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

    @property
    def _trial_name(self):
        return f"{self.date}--{self.animal_id}_{self.ROI_id}"

    # TODO: consider doing this for csv and txt
    @property
    def _csv_filename(self):
        return f"{self._trial_name}_solenoid_info.csv"

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
        first_trial_name = self._trial_name
        # first_trial_name = f"{self.date}--{self.animal_id}_{self.ROI_id}"

        # check whether the first trial txt exists
        if os.path.isfile(
            # Path(self.session_path, f"{first_trial_name}_000.txt")
            Path(self.session_path, f"{self._trial_name}_000.txt")
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
                    self.rename_correct_format(m, filename, _ext)

                # this renames the first trial text file and adds 000
                else:
                    self.rename_first_txt(filename, _ext)
            st.info(".txt files renamed; proceeding with analysis.")

    def get_txt_file_paths(self):
        """
        Creates list of paths for all text files, excluding solenoid info
        """
        # TODO: return []
        self.txt_paths = [
            str(path)
            for path in Path(self.session_path).rglob("*.txt")
            if "solenoid" not in path.stem
        ]

    def iterate_txt_files(self):
        """
        Iterates through txt files, opens them as csv and converts each file to
        dataframe, then collects everything inside a dict.

        TODO: pass in txt_paths (or whatever the output of get_txt_file_paths)
        """
        # TODO: if not txt_paths: raise Exception("no paths")

        # sorts the paths according to 000-001, etc
        paths = sorted(self.txt_paths, key=lambda x: int(x[-7:-4]))

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

        # return all_data_df
        self.organize_all_data_df(all_data_df)

    def organize_all_data_df(self, all_data_df):
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

        self.all_data_df = all_data_df

    def process_txt_file(self, n_count, bar, sample_type):
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
            f"{self.date}_{self.animal_id}_{self.ROI_id}_raw_means.xlsx",
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
        # TODO: return description and don't pass in bar

        bar.set_description(
            f"Analyzing {sample_type} {n_count+1}", refresh=True
        )

    def drop_trials(self):
        """
        Drops excluded trials from all_data_df
        """

        self.all_data_df = self.all_data_df.loc[
            ~self.all_data_df["Trial"].isin(self.drop_trials_list)
        ]

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
        (
            baseline,
            peak,
            deltaF,
            baseline_stdx3,
            deltaF_blank,
            blank_sub_deltaF,
            blank_sub_deltaF_F_perc,
            baseline_subtracted,
        ) = self.do_initial_calcs(avg_means)

        # Determines whether response is significant by checking whether
        # blank_sub_deltaF is greater than baseline_stdx3.
        significance_bool = blank_sub_deltaF > baseline_stdx3
        self.sig_odors = significance_bool[significance_bool].index.values

        significance_report = self.get_sig_responses(
            significance_bool, blank_sub_deltaF_F_perc
        )

        auc, auc_blank = self.calc_auc(avg_means, baseline)

        # only do the below if response is present
        (
            blank_sub_auc,
            peak_times,
            odor_onset,
            response_onset,
            latency,
            time_to_peak,
        ) = self.analyze_sig_responses(
            avg_means, auc, auc_blank, deltaF, baseline_subtracted
        )

        response_analyses_df = self.make_analysis_df(
            avg_means,
            baseline,
            peak,
            deltaF,
            baseline_stdx3,
            deltaF_blank,
            blank_sub_deltaF,
            blank_sub_deltaF_F_perc,
            significance_report,
            auc,
            auc_blank,
            blank_sub_auc,
            peak_times,
            odor_onset,
            response_onset,
            latency,
            time_to_peak,
        )
        # TODO: make these args fixed? avg_means=avg_means, baseline=baseline..

        return response_analyses_df

    def do_initial_calcs(
        self, avg_means
    ):  # TODO: change verb to "calculate_initial_nums" or something that suggests these calcs are being returned
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
        # TODO: comment is very obvious - better to explain why _blank is being subtracted from deltaF
        #   or explain what this value will be used for
        blank_sub_deltaF = deltaF - deltaF_blank

        # Calculates blanksub_deltaF/F(%)
        blank_sub_deltaF_F_perc = blank_sub_deltaF / baseline * 100

        # Calculates baseline-subtracted avg means
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

    def calc_auc(self, avg_means, baseline):
        # Calculates AUC using sum of values from frames # 1-300
        auc = (avg_means[:300].sum() - (baseline * 300)) * 0.0661
        auc.clip(lower=0, inplace=True)  # Sets negative AUC values to 0

        # Gets AUC_blank from AUC of the last odor
        auc_blank = auc[avg_means.columns[-1]]

        return auc, auc_blank

    def get_sig_responses(self, significance_bool, blank_sub_deltaF_F_perc):
        """
        :param List[bool] significance_bool:
        :param float blank_sub_deltaF_F_perc:
        :return rtype_here:
        """

        # TODO 5: since we are using self.sig_odors elsewhere, it would be better
        #  to set the value outside of this method -- also bc the values that
        #  significance_bool is dependent on are being passed into this method.
        #  it is easy to separate this. (next 4 lines move out)

        # reports False if odor is not significant, otherwise
        # reports blanksub_deltaF/F(%)
        significance_report = significance_bool.copy()
        significance_report[self.sig_odors] = blank_sub_deltaF_F_perc[
            self.sig_odors
        ]
        significance_report = pd.Series(significance_report)

        return significance_report

    def analyze_sig_responses(
        self, avg_means, auc, auc_blank, deltaF, baseline_subtracted
    ):
        # Creates 'N/A' template for non-significant odor responses
        na_template = pd.Series("N/A", index=avg_means.columns)

        # Calculates blank-subtracted AUC only if response is present
        blank_sub_auc = na_template.copy()
        blank_sub_auc[self.sig_odors] = auc[self.sig_odors] - auc_blank

        # Calculates time at signal peak using all the frames
        # why does excel sheet have - 2??
        max_frames = avg_means[:300].idxmax()
        peak_times = na_template.copy()
        peak_times[self.sig_odors] = max_frames[self.sig_odors] * 0.0661

        # Get odor onset - Frame 57?
        odor_onset = 57 * 0.0661

        # Calculate response onset only for significant odors
        response_onset = na_template.copy()
        onset_amp = deltaF * 0.05

        for sig_odor in self.sig_odors:
            window = baseline_subtracted[56:300][sig_odor]
            onset_idx = np.argmax(window >= onset_amp[sig_odor])
            onset_time = window.index[onset_idx] * 0.0661
            response_onset[sig_odor] = onset_time

        # Calculate latency
        latency = na_template.copy()
        latency[self.sig_odors] = response_onset[self.sig_odors] - odor_onset

        # Calculate time to peak
        time_to_peak = na_template.copy()
        time_to_peak[self.sig_odors] = (
            peak_times[self.sig_odors] - response_onset[self.sig_odors]
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
        avg_means,
        baseline,
        peak,
        deltaF,
        baseline_stdx3,
        deltaF_blank,
        blank_sub_deltaF,
        blank_sub_deltaF_F_perc,
        significance_report,
        auc,
        auc_blank,
        blank_sub_auc,
        peak_times,
        odor_onset,
        response_onset,
        latency,
        time_to_peak,
    ):
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

        # TODO: put pd.Series values into their own variables for pretty
        # pretty_var = pd.Series([blah])
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
        # fname = f"{self._trial_name}_solenoid_info.csv"
        fname = f"{self.date}_{self.animal_id}_{self.ROI_id}_solenoid_info.csv"
        save_to_csv(fname, self.session_path, self.soelnoid_df)


class ExperimentFile(object):
    def __init__(self, file, df_list, dataset_type):
        self.file = file
        self.dataset_type = dataset_type

        # TODO:
        # it's cleaner/more pythonic to use split whenever u can
        # also more pythonic to assign variables by unpacking (see _, _ = file_parts)
        # also more pythonic to use join whenever u can

        # file_parts = file.name.split("_")[0:2]  # this is a list
        # self.date, self.animal_id, self.roi = file_parts
        # self.exp_name = file_parts.join("_")

        self.exp_name = (
            file.name.split("_")[0]
            + "_"
            + file.name.split("_")[1]
            + "_"
            + file.name.split("_")[2]
        )
        self.animal_id = file.name.split("_")[1]
        self.roi = self.exp_name.split("_")[2]

        if self.dataset_type == "chronic":
            self.date = file.name.split("_")[0]

        self.sample_type = None
        self.data_dict = None
        self.tuple_dict = None
        self.mega_df = None
        self.sig_data_df = None
        self.sig_odors = None  # TODO: this can be initialized to []

        self.df_list = df_list

        # TODO: ponder putting in an initialize method OR group the Nones and
        # group the ones being assigned values

    def import_excel(self):
        """
        Imports each .xlsx file into dictionary
        """

        self.data_dict = pd.read_excel(
            self.file,
            sheet_name=None,
            header=1,
            index_col=0,
            na_values="FALSE",
            dtype="object",
        )

    # def shared_method(self):
    #     do stuff

    #     if chronic:
    #         do stuff
    #     elif acute:
    #         do other stuff

    def sort_data(self):
        """
        Converts imported dict into dataframe for each measurement
        """
        self.tuple_dict = {
            (outerKey, innerKey): values
            for outerKey, innerDict in self.data_dict.items()
            for innerKey, values in innerDict.items()
        }

        self.mega_df = pd.DataFrame(self.tuple_dict)
        self.sample_type = self.mega_df.columns[0][0].split(" ")[0]

        # Replaces values with "" for non-sig responses
        temp_mega_df = self.mega_df.T
        temp_mega_df.loc[
            temp_mega_df["Significant response?"] == False, "Blank sub AUC"
        ] = ""
        temp_mega_df.loc[
            temp_mega_df["Significant response?"] == False,
            "Blank-subtracted DeltaF/F(%)",
        ] = ""

        self.mega_df = temp_mega_df.copy().T

        for measure_ct, measure in enumerate(st.session_state.measures):
            temp_measure_df = (
                pd.DataFrame(self.mega_df.loc[measure]).T.stack().T
            )

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

            concat_pd = pd.concat([self.df_list[measure_ct], temp_measure_df])
            self.df_list[measure_ct] = concat_pd

    def make_plotting_dfs(self):
        """
        Makes the dfs used for plotting measusrements
        """
        self.sig_data_df = pd.DataFrame()
        self.sig_odors = []  # TODO: can delete this line if u take suggestion

        # drop non-significant colums from each df using NaN values
        for data_df in self.data_dict.values():
            data_df.dropna(axis=1, inplace=True)

            # extracts measurements to plot
            data_df = data_df.loc[
                [
                    "Blank-subtracted DeltaF/F(%)",
                    "Blank sub AUC",
                    "Latency (s)",
                    "Time to peak (s)",
                ]
            ]

            self.sig_data_df = pd.concat([self.sig_data_df, data_df], axis=1)

            # gets list of remaining significant odors
            if len(data_df.columns.values) == 0:
                pass
            else:
                df_sig_odors = data_df.columns.values.tolist()
                self.sig_odors.append(df_sig_odors)

        # TODO: return self.sig_odors, self.sig_data_df so processing can use
