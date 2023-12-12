"""Sets up the Streamlit app page responsible plotting multiple imaging 
sessions in one chronic dataset.

The page prompts the user to select a folder where the generated summary file
compiled_dataset_analysis.xlsx file should be saved to. Next, the user will 
need to upload all the analysis.xlsx files from all imaging sessions in the 
dataset that they want to plot data for.

Four different measurement plots will be generated for each odor (selected by
drop-down menu). Analysis will generate compiled_dataset_analysis.xlsx file
containing the summary statistics for all imaging sessions in the dataset.
"""

import plotly.io as pio

pio.templates.default = "plotly_white"
import streamlit as st
from src.utils import (
    make_pick_folder_button,
    pop_folder_selector,
    check_uploaded_files,
    check_sig_odors,
)

from src.processing import (
    import_all_excel_data,
    sort_measurements_df,
    generate_plots,
    show_plots_sliders,
)
import pdb


def set_webapp_params():
    """Sets the name of the Streamlit app."""

    st.set_page_config(page_title="Plot Chronic Imaging Data")
    st.title("Plot data from chronic imaging sessions")


def initialize_states():
    """Initializes session state variables."""

    # # # --- Initialising SessionState ---
    if "chronic_dir_path" not in st.session_state:
        st.session_state.chronic_dir_path = False
    # makes the avg_means data persist
    if "chronic_files" not in st.session_state:
        st.session_state.chronic_files = False
    # checks whether Load data was clicked
    if "pg4_load_data" not in st.session_state:
        st.session_state.pg4_load_data = False
    if "animal_id" not in st.session_state:
        st.session_state.animal_id = False
    if "interval" not in st.session_state:
        st.session_state.interval = False
    if "sig_data" not in st.session_state:
        st.session_state.sig_data = False
    if "sorted_dates" not in st.session_state:
        st.session_state.sorted_dates = False
    if "sig_odors" not in st.session_state:
        st.session_state.sig_odors = False
    if "nosig_exps" not in st.session_state:
        st.session_state.no_sig_exps = False

    # assigns a color to each exp session with significant responses
    if "sig_exp_colors" not in st.session_state:
        st.session_state.sig_exp_colors = False

    if "chronic_plots_list" not in st.session_state:
        st.session_state.chronic_plots_list = False
    if "selected_odor" not in st.session_state:
        st.session_state.selected_odor = False

    # measures to plot
    st.session_state.measures = [
        "Baseline",
        "Blank-subtracted DeltaF/F(%)",
        "Blank sub AUC",
        "Latency (s)",
        "Time to peak (s)",
    ]


def prompt_dir():
    """Prompts user for directory to save summary .xlsx file."""

    st.markdown(
        "Please select the folder where you want to save the summary "
        ".xlsx file"
    )

    clicked = make_pick_folder_button()

    if clicked:
        st.session_state.chronic_dir_path = pop_folder_selector()

    if st.session_state.chronic_dir_path:
        st.write("Summary .xlsx file will be saved to:")
        st.info(st.session_state.chronic_dir_path)


def upload_dataset():
    """Prompts user to upload files from dataset to be analyzed."""

    st.markdown(
        "Please select the .xlsx files containing the response properties that you "
        "want to plot. The files should be named in the format "
        "YYMMDD--123456-7-8_ROIX_analysis.xlsx."
    )

    st.session_state.chronic_files = st.file_uploader(
        label="Choose files",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )


def get_data(status: st.status) -> list:
    """Gets data from uploaded .xlsx files and drops non-significant response
        data.

    Returns:
        A list containing experimental data and the ids of significant
            experiments and odors.
    """

    st.write(
        f"Importing data from {len(st.session_state.chronic_files)} Excel "
        f"files from animal ID {st.session_state.animal_id}..."
    )

    dict_list, df_list = import_all_excel_data(
        "chronic", st.session_state.chronic_files
    )
    sample_type = df_list[0].index.name

    st.write("Generating summary .xlsx file...")

    st.session_state.animal_id = (
        f"{st.session_state.chronic_files[0].name.split('_')[1]}_"
        f"{st.session_state.chronic_files[0].name.split('_')[2]}"
    )

    sort_measurements_df(
        st.session_state.chronic_dir_path,
        "compiled_dataset_analysis.xlsx",
        df_list,
        sample_type,
        st.session_state.measures,
        dataset_type="chronic",
        animal_id=st.session_state.animal_id,
    )

    return dict_list


def process_dataset():
    """Processes data from uploaded files and creates summary .xlsx file."""

    with st.status("Processing data...", expanded=True) as status:
        st.session_state.pg4_load_data = True

        (
            st.session_state.nosig_exps,
            odors_list,
            st.session_state.sig_data,
            st.session_state.sorted_dates,
        ) = get_data(status)

        status.update(
            label="All data loaded. Summary .xlsx file saved to the selected "
            "directory as compiled_dataset_analysis.xlsx",
            state="complete",
            expanded=False,
        )

        st.session_state.sig_odors = check_sig_odors(
            odors_list,
            st.session_state.nosig_exps,
            st.session_state.chronic_files,
        )

        # if load data is clicked again, doesn't display plots/slider
        st.session_state.chronic_plots_list = False


def main():
    initialize_states()
    set_webapp_params()
    prompt_dir()
    upload_dataset()

    # Checks that all the uploaded files are correct
    checked_files = check_uploaded_files(st.session_state.chronic_files)

    if checked_files is False:
        st.session_state.chronic_files = False
        st.session_state.pg4_load_data = False

    if st.session_state.chronic_files or st.session_state.pg4_load_data:
        if st.session_state.chronic_dir_path:
            if st.button("Load data"):
                process_dataset()

            # select interval type if load data has been clicked
            if st.session_state.pg4_load_data:
                st.session_state.interval = st.radio(
                    "Select timepoint interval:", ("Day", "Week", "Session")
                )

            # if data has been loaded, always show plotting buttons
            if st.session_state.pg4_load_data and len(
                st.session_state.nosig_exps
            ) != len(st.session_state.chronic_files):
                if st.button("Plot data"):
                    st.session_state.chronic_plots_list = generate_plots(
                        st.session_state.sig_odors,
                        st.session_state.nosig_exps,
                        "chronic",
                        st.session_state.sig_data,
                        st.session_state.measures,
                        st.session_state.sorted_dates,
                        st.session_state.interval,
                    )
                # display slider and plots if plots have already been generated
                # even if Plot data isn't clicked again
                show_plots_sliders(
                    st.session_state.chronic_plots_list,
                    st.session_state.selected_odor,
                    st.session_state.sig_odors,
                    st.session_state.measures,
                )


if __name__ == "__main__":
    main()
