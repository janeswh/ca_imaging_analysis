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


import plotly.io as pio

pio.templates.default = "plotly_white"
import streamlit as st
import pdb


def set_webapp_params():
    """
    Sets the name of the Streamlit app along with other things
    """
    st.set_page_config(page_title="Plot Multiple Acute Imaging Data")
    st.title("Plot data from multiple acute imaging sessions")


def initialize_states():
    """
    Initializes session state variables
    """

    # # # --- Initialising SessionState ---
    if "acute_dir_path" not in st.session_state:
        st.session_state.acute_dir_path = False
    # makes the avg_means data persist
    if "acute_files" not in st.session_state:
        st.session_state.acute_files = False
    # checks whether Load data was clicked
    if "pg3_load_data" not in st.session_state:
        st.session_state.pg3_load_data = False
    if "sorted_sig_data" not in st.session_state:
        st.session_state.sorted_sig_data = False
    if "sig_odors" not in st.session_state:
        st.session_state.sig_odors = False
    if "nosig_exps" not in st.session_state:
        st.session_state.nosig_exps = False

    # assigns a color to each exp session with significant responses
    if "sig_exp_colors" not in st.session_state:
        st.session_state.sig_exp_colors = False

    if "acute_plots_list" not in st.session_state:
        st.session_state.acute_plots_list = False
    if "selected_odor" not in st.session_state:
        st.session_state.selected_odor = False

    # measures to plot
    st.session_state.measures = [
        "Blank-subtracted DeltaF/F(%)",
        "Blank sub AUC",
        "Latency (s)",
        "Time to peak (s)",
    ]


def prompt_dir():
    """
    Prompts user for directory to save summary .xlsx file, then asks user to
    upload analysis files to plot
    """

    st.markdown(
        "Please select the folder where you want to save the summary "
        ".xlsx file"
    )

    clicked = make_pick_folder_button()

    if clicked:
        st.session_state.acute_dir_path = pop_folder_selector()

    if st.session_state.acute_dir_path:
        st.write("Summary .xlsx file will be saved to:")
        st.info(st.session_state.acute_dir_path)


def upload_dataset():
    """
    Prompts user to upload files from dataset to be analyzed
    """

    st.markdown(
        "Please select the .xlsx files containing the response properties that you "
        "want to plot. The files should be named in the format "
        "YYMMDD--123456-7-8_ROIX_analysis.xlsx."
    )

    st.session_state.acute_files = st.file_uploader(
        label="Choose files",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )


def get_data():
    """
    Loads data from uploaded .xlsx files, drops non-significant response data,
    and returns only significant data and list of significant odors
    """
    dict_list, df_list = import_all_excel_data(
        "acute", st.session_state.acute_files
    )
    sample_type = df_list[0].index.name

    sort_measurements_df(
        st.session_state.acute_dir_path,
        "compiled_dataset_analysis.xlsx",
        df_list,
        sample_type,
        st.session_state.measures,
        dataset_type="acute",
    )

    return dict_list


def process_dataset():
    """
    Loads data from uploaded files and creates summary .xlsx file
    """
    st.session_state.pg3_load_data = True

    (
        st.session_state.nosig_exps,
        odors_list,
        st.session_state.sorted_sig_data,
    ) = get_data()

    st.info(
        f"Response data loaded successfully for "
        f"{len(st.session_state.acute_files)} experiments. Summary .xlsx"
        " file saved to the selected directory as "
        "compiled_dataset_analysis.xlsx"
    )

    st.session_state.sig_odors = check_sig_odors(
        odors_list,
        st.session_state.nosig_exps,
        st.session_state.acute_files,
    )

    # if load data is clicked again, doesn't display plots/slider
    st.session_state.acute_plots_list = False


def main():
    initialize_states()
    set_webapp_params()
    prompt_dir()
    upload_dataset()

    # Checks that all the uploaded files are correct
    checked_files = check_uploaded_files(st.session_state.acute_files)

    if checked_files is False:
        st.session_state.acute_files = False
        st.session_state.pg3_load_data = False

    if st.session_state.acute_files or st.session_state.pg3_load_data:
        if st.session_state.acute_dir_path:
            if st.button("Load data"):
                process_dataset()

            # if data has been loaded, always show plotting buttons
            if (
                st.session_state.pg3_load_data
                and len(st.session_state.nosig_exps)
                != len(st.session_state.acute_files)
                and st.session_state.acute_dir_path
            ):
                if st.button("Plot data"):
                    st.session_state.acute_plots_list = generate_plots(
                        st.session_state.sig_odors,
                        st.session_state.nosig_exps,
                        "acute",
                        st.session_state.sorted_sig_data,
                        st.session_state.measures,
                    )
                # display slider and plots if plots have already been generated
                # even if Plot data isn't clicked again
                show_plots_sliders(
                    st.session_state.acute_plots_list,
                    st.session_state.selected_odor,
                    st.session_state.sig_odors,
                    st.session_state.measures,
                )


if __name__ == "__main__":
    main()
