"""Sets up the Streamlit app page responsible for plotting mean fluorescence
amplitude values from one imaging session.

The page prompts the user to upload the avg_means.xlsx file containing the
fluorescence data to be plotted. Clicking "Load Data" and "Plot Data" will
generate one plot for each sample, with each plot containing fluorescence 
values for all odors as different-colored traces. Mean amplitude is plotted on
the y axis against Frame # on the x axis.
"""

import streamlit as st
from stqdm import stqdm
import pdb

from src.processing import load_avg_means
from src.plotting import plot_avg_amps


def set_webapp_params():
    """Sets the name of the Streamlit app."""

    st.set_page_config(page_title="Plot One Imaging Session Data")
    st.title("Plot data from one imaging session")


def initialize_states():
    """Initializes session state variables."""

    # makes the avg_means data persist
    if "data" not in st.session_state:
        st.session_state.data = False
    # checks whether Load data was clicked
    if "pg2_load_data" not in st.session_state:
        st.session_state.pg2_load_data = False
    if "file" not in st.session_state:
        st.session_state.file = False
    if "odor_list" not in st.session_state:
        st.session_state.odor_list = False
    if "pg2_plots_list" not in st.session_state:
        st.session_state.pg2_plots_list = False
    if "selected_sample" not in st.session_state:
        st.session_state.selected_sample = False


def prompt_file():
    """Prompts user to select the avg_means.xlsx file containing the mean
    fluorescence values to plot.
    """

    st.markdown(
        "Please select the .xlsx file containing the mean amplitudes that you "
        "want to plot. The file should be named in the format "
        "YYMMDD--123456-7-8_ROIX_avg_means.xlsx."
    )
    st.session_state.file = st.file_uploader(
        label="Choose a file", label_visibility="collapsed"
    )


def check_file():
    """Checks that the correct .xlsx file has been uploaded."""

    if st.session_state.file is not None:
        if "avg_means" not in st.session_state.file.name:
            st.error(
                "Please make sure that the correct file with name "
                "ending in 'avg_means.xlsx' has been uploaded."
            )
            st.session_state.pg2_load_data = False
            st.session_state.file = False


def generate_plots():
    """Generates mean amplitude plots for all odors in all samples."""

    if st.checkbox("Select specific odors to plot"):
        odors_to_plot = st.multiselect(
            label="Odors to plot",
            options=st.session_state.odor_list,
            label_visibility="collapsed",
        )
        if len(odors_to_plot) == 0:
            odors_to_plot = st.session_state.odor_list

    else:
        odors_to_plot = st.session_state.odor_list

    if st.button("Plot data"):
        plots_list = {}

        # adds progress bar
        bar = stqdm(st.session_state.data.items(), desc="Plotting ")
        for sample, avg_means_df in bar:
            fig = plot_avg_amps(avg_means_df, odors_to_plot)
            plots_list[sample] = fig

        st.info("All plots generated.")
        st.session_state.pg2_plots_list = plots_list


def display_plots():
    """Displays slider and plots.

    Will be displayed if plots have already been generated even if Plot Data
    isn't clicked again.
    """

    st.session_state.selected_sample = st.select_slider(
        "Select sample number to display its " "corresponding plot:",
        options=st.session_state.data.keys(),
    )

    if st.session_state.selected_sample:
        st.plotly_chart(
            st.session_state.pg2_plots_list[st.session_state.selected_sample]
        )


def main():
    set_webapp_params()
    initialize_states()
    prompt_file()

    check_file()

    if st.session_state.file or st.session_state.pg2_load_data:
        if st.button("Load data"):
            st.session_state.data, st.session_state.odor_list = load_avg_means(
                st.session_state.file
            )
            st.session_state.pg2_load_data = True
            # if load data is clicked again, doesn't display plots/slider
            st.session_state.pg2_plots_list = False

        # if data has been loaded, always show plotting buttons
        if st.session_state.pg2_load_data:
            generate_plots()

            # display slider and plots if plots have already been generated
            # even if Plot data isn't clicked again
            if st.session_state.pg2_plots_list:
                display_plots()


if __name__ == "__main__":
    main()
