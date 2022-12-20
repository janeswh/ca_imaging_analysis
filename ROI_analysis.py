import os
import glob
import pandas as pd
from collections import OrderedDict, defaultdict
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


class ImagingSession(object):
    def __init__(self, main_directory):
        self.main_directory = main_directory

    def search_matching_folders(self, search_type):
        """
        Search all folders in the directory containing matching string, depending
        on whether searching for animal ID for a given date, or ROI for a given 
        date and animal
        """
        if search_type == "date":
            folders = [
                f.name
                for f in os.scandir(self.main_directory)
                if f.is_dir() and self.date in f.name
            ]

        elif search_type == "animal":
            folders = [
                f.name
                for f in os.scandir(self.main_directory)
                if f.is_dir()
                and self.date in f.name
                and self.animal_id in f.name
            ]

        extracted_list = []
        for folder in folders:
            if search_type == "date":
                # this returns animal ID
                extracted_item = folder.split("--")[1].split("_")[0]
            elif search_type == "animal":
                # this returns ROI
                extracted_item = folder.split("_")[1]
            extracted_list.append(extracted_item)

    def get_user_input(self, prompt_type):
        """
        
        """

    def get_txt_directory(self):
        """
        Prompts the user for the imaging session date and animal ID to perform
        analysis on, then locates the directory of txt files.
        """
        self.date = input("Enter imaging date as format YYMMDD:")

        date_folders = [
            f.name
            for f in os.scandir(self.main_directory)
            if f.is_dir() and self.date in f.name
        ]

        # extracts possible animal IDs from the folders for the specified date
        animal_list = []

        for folder in date_folders:
            folder_strings = folder.split("--")
            animal_data = folder_strings[1].split("_")
            animal_id = animal_data[0]
            animal_list.append(animal_id)
            pdb.set_trace()

        animal_dict = OrderedDict.fromkeys(animal_list)
        animal_select_list = [str(i) for i in list(range(len(animal_dict)))]

        for key, val in zip(animal_dict, animal_select_list):
            animal_dict[key] = val

        animal_select_dict = {v: k for k, v in animal_dict.items()}

        # prompts user to select animal ID from available IDs in specified date
        for c, animal in animal_select_dict.items():
            print(f"{c}. {animal}")

        choice = input("Select animal ID using corresponding digit: ")

        while choice not in animal_select_dict:
            choice = input(f"Choose one of: {', '.join(animal_select_dict)}: ")
        print(f"Animal ID: {animal_select_dict[choice]}")

        self.animal_id = animal_select_dict[choice]

        # extracts possible ROIs from the folders for the specified date +
        # animal ID
        ROI_list = []
        ROI_folders = [
            f.name
            for f in os.scandir(self.main_directory)
            if f.is_dir() and self.date in f.name and self.animal_id in f.name
        ]

        for ROI_folder in ROI_folders:
            ROI_folder_strings = ROI_folder.split("_")
            roi = ROI_folder_strings[1]
            ROI_list.append(roi)

        ROI_dict = OrderedDict.fromkeys(ROI_list)
        ROI_select_list = [str(i) for i in list(range(len(animal_dict)))]
        for key, val in zip(ROI_dict, ROI_select_list):
            ROI_dict[key] = val
        ROI_select_dict = {v: k for k, v in ROI_dict.items()}

        # prompts user to select ROI from available ROIs in specified date
        for c, roi in ROI_select_dict.items():
            print(f"{c}. {roi}")

        choice = input("Select ROI using corresponding digit: ")

        while choice not in ROI_select_dict:
            choice = input(f"Choose one of: {', '.join(ROI_select_dict)}: ")
        print(f"ROI: {ROI_select_dict[choice]}")

        self.ROI = ROI_select_dict[choice]

        pdb.set_trace()

    def get_metadata():
        """
        Gets the date, animal ID, and ROI location from the ImageJ output txt files
    """


def main():
    main_directory = set_main_directory()
    roi_data = ImagingSession(main_directory)
    roi_data.get_txt_directory()


if __name__ == "__main__":
    main()

