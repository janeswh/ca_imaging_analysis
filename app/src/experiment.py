import pandas as pd
import streamlit as st
import pdb


class ExperimentFile(object):
    def __init__(self, file, df_list, dataset_type):
        self.file = file
        self.sample_type = None
        self.dataset_type = dataset_type
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

        self.data_dict = None
        self.tuple_dict = None
        self.mega_df = None
        self.sig_data_df = None
        self.sig_odors = None

        self.df_list = df_list

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
        self.sig_odors = []

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
