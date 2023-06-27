from src.utils import (
    make_pick_folder_button,
    pop_folder_selector,
    get_odor_data,
    sort_measurements_df,
    check_sig_odors,
)

from src.experiment import ExperimentFile

from src.plotting import (
    set_color_scales,
    get_acute_plot_params,
    position_acute_mean_line,
    plot_acute_odor_measure_fig,
)

import streamlit as st
import pandas as pd
from collections import defaultdict
import plotly.graph_objects as go
import plotly.io as pio

pio.templates.default = "plotly_white"

from stqdm import stqdm


def set_webapp_params():
    """
    Sets the name of the Streamlit app along with other things
    """
    st.set_page_config(page_title="Plot Multiple Acute Imaging Data")
    st.title("Plot data from multiple acute imaging sessions")

    st.markdown(
        "Please select the folder where you want to save the summary "
        ".xlsx file"
    )

    clicked = make_pick_folder_button()

    if clicked:
        st.session_state.dir_path = pop_folder_selector()

    if st.session_state.dir_path:
        st.write("Summary .xlsx file will be saved to:")
        st.info(st.session_state.dir_path)

    st.markdown(
        "Please select the .xlsx files containing the response properties that you "
        "want to plot. The files should be named in the format "
        "YYMMDD--123456-7-8_ROIX_analysis.xlsx."
    )

    st.session_state.files = st.file_uploader(
        label="Choose files",
        label_visibility="collapsed",
        accept_multiple_files=True,
    )


def initialize_states():
    """
    Initializes session state variables
    """

    # # # --- Initialising SessionState ---
    if "dir_path" not in st.session_state:
        st.session_state.dir_path = False
    # makes the avg_means data persist
    if "files" not in st.session_state:
        st.session_state.files = False
    # checks whether Load data was clicked
    if "pg3_load_data" not in st.session_state:
        st.session_state.pg3_load_data = False
    if "sig_data" not in st.session_state:
        st.session_state.sig_data = False
    if "sorted_sig_data" not in st.session_state:
        st.session_state.sorted_sig_data = False
    if "sig_odors" not in st.session_state:
        st.session_state.sig_odors = False
    if "nosig_exps" not in st.session_state:
        st.session_state.nosig_exps = False

    # assigns a color to each exp session with significant responses
    if "sig_exp_colors" not in st.session_state:
        st.session_state.sig_exp_colors = False

    if "pg3_plots_list" not in st.session_state:
        st.session_state.pg3_plots_list = False
    if "selected_odor" not in st.session_state:
        st.session_state.selected_odor = False

    # measures to plot
    st.session_state.measures = [
        "Blank-subtracted DeltaF/F(%)",
        "Blank sub AUC",
        "Latency (s)",
        "Time to peak (s)",
    ]


def import_data():
    # makes list to hold exp names with no significant data
    nosig_exps = []

    # makes list to hold all significant odors
    all_sig_odors = []

    # makes dict to hold data from all significant odors
    sig_data_dict = {}

    # make dict to hold significant data sorted by animal id
    sorted_sig_data_dict = defaultdict(dict)

    # makes df for each measurement, for summary csv
    blank_sub_df = pd.DataFrame()
    auc_df = pd.DataFrame()
    latency_df = pd.DataFrame()
    ttpeak_df = pd.DataFrame()

    df_list = [blank_sub_df, auc_df, latency_df, ttpeak_df]

    # adds progress bar
    load_bar = stqdm(st.session_state.files, desc="Loading ")
    for file in load_bar:
        experiment = ExperimentFile(file, df_list)
        experiment.import_excel()
        experiment.sort_data()
        experiment.make_plotting_dfs()

        all_sig_odors.append(experiment.sig_odors)
        sig_data_dict[experiment.exp_name] = experiment.sig_data_df

        if not experiment.sig_data_df.empty:
            sorted_sig_data_dict[experiment.animal_id][
                experiment.exp_name
            ] = experiment.sig_data_df
        if experiment.sig_data_df.empty:
            nosig_exps.append(experiment.exp_name)

    sort_measurements_df(
        st.session_state.dir_path,
        "compiled_dataset_analysis.xlsx",
        df_list,
        experiment.sample_type,
        st.session_state.measures,
    )

    return nosig_exps, all_sig_odors, sorted_sig_data_dict


def plot_odor_measure_fig(
    sig_odor_exps,
    odor,
    measure,
    color_scale,
    total_animals,
    plot_groups,
    total_cols,
):
    """
    Plots the analysis values for specified odor and measurement
    """
    measure_fig = go.Figure()

    for animal_ct, animal_id in enumerate(sig_odor_exps.keys()):
        for exp_ct, sig_experiment in enumerate(sig_odor_exps[animal_id]):
            exp_odor_df = st.session_state.sorted_sig_data[animal_id][
                sig_experiment
            ][odor]

            measure_fig.add_trace(
                go.Box(
                    x=[animal_id] * len(exp_odor_df.loc[measure].values)
                    if isinstance(exp_odor_df.loc[measure], pd.Series)
                    else [animal_id],
                    y=exp_odor_df.loc[measure].values.tolist()
                    if isinstance(exp_odor_df.loc[measure], pd.Series)
                    else [exp_odor_df.loc[measure]],
                    line=dict(color="rgba(0,0,0,0)"),
                    fillcolor="rgba(0,0,0,0)",
                    boxpoints="all",
                    pointpos=0,
                    marker_color=color_scale["marker"][animal_ct + 1][exp_ct],
                    marker=dict(
                        # opacity=0.5,
                        line=dict(
                            color=color_scale["lines"][animal_ct + 1][exp_ct],
                            width=2,
                        ),
                        size=12,
                    ),
                    name=sig_experiment,
                    offsetgroup=exp_ct,
                    legendgroup=animal_ct,
                ),
            )

            # only adds mean line if there is more than one pt
            if isinstance(exp_odor_df.loc[measure], pd.Series):
                measure_fig = add_mean_line(
                    measure_fig,
                    total_animals,
                    total_cols,
                    plot_groups,
                    animal_ct,
                    exp_ct,
                    color_scale,
                    measure,
                    exp_odor_df,
                )

    return measure_fig


def add_mean_line(
    fig,
    total_animals,
    total_cols,
    plot_groups,
    animal_ct,
    exp_ct,
    color_scale,
    measure,
    exp_odor_df,
):
    """
    Adds mean line to each dataset
    """
    x0, x1 = position_acute_mean_line(
        total_animals,
        total_cols,
        plot_groups,
        animal_ct,
        exp_ct,
    )

    fig.add_shape(
        type="line",
        line=dict(
            color=color_scale["lines"][animal_ct + 1][exp_ct],
            width=4,
        ),
        xref="x domain",
        x0=x0,
        x1=x1,
        y0=exp_odor_df.loc[measure].values.mean(),
        y1=exp_odor_df.loc[measure].values.mean(),
    )

    return fig


def format_fig(fig, measure):
    """
    Formats the legend, axes, and titles of the fig
    """
    #  below is code from stack overflow to hide duplicate legends
    names = set()
    fig.for_each_trace(
        lambda trace: trace.update(showlegend=False)
        if (trace.name in names)
        else names.add(trace.name)
    )

    fig.update_xaxes(showticklabels=True, title_text="<br />Animal ID")

    fig.update_yaxes(
        title_text=measure,
    )

    if measure == "Time to peak (s)":
        fig.update_yaxes(
            rangemode="tozero",
        )

    fig.update_layout(
        boxmode="group",
        boxgap=0.4,
        title={
            "text": measure,
            "x": 0.4,
            "xanchor": "center",
        },
        legend_title_text="Experiment ID<br />",
        showlegend=True,
    )

    return fig


def generate_plots():
    """
    Creates plots for each odor
    """

    plots_list = defaultdict(dict)

    # adds progress bar
    odor_bar = stqdm(st.session_state.sig_odors, desc="Plotting ")

    for odor in odor_bar:
        odor_data = get_odor_data(
            odor, "acute", st.session_state.sorted_sig_data
        )
        sig_odor_exps = odor_data[0]
        all_roi_counts = odor_data[1]
        total_animals = odor_data[2]

        plot_groups, total_cols = get_acute_plot_params(all_roi_counts)

        for measure in st.session_state.measures:
            measure_fig = plot_acute_odor_measure_fig(
                sig_odor_exps,
                st.session_state.sorted_sig_data,
                odor,
                measure,
                total_animals,
                plot_groups,
                total_cols,
            )

            measure_fig = format_fig(measure_fig, measure)

            plots_list[odor][measure] = measure_fig

        odor_bar.set_description(f"Plotting {odor}", refresh=True)

    st.info("All plots generated.")
    if len(st.session_state.nosig_exps) != 0:
        st.warning(
            "No plots have been generated for the "
            "following experiments due to the lack of significant "
            "odor responses: \n"
            f"{st.session_state.nosig_exps}"
        )

    st.session_state.pg3_plots_list = plots_list


def display_plots():
    """
    Displays the plots for the selected odor
    """
    for measure in st.session_state.measures:
        st.plotly_chart(
            st.session_state.pg3_plots_list[st.session_state.selected_odor][
                measure
            ]
        )


def main():
    initialize_states()
    set_webapp_params()

    # checks that all the uploaded files are correct
    for file in st.session_state.files:
        if "_analysis" not in file.name:
            st.error(
                "Please make sure all uploaded files end in '_analysis.xlsx'"
            )
            st.session_state.files = False
            st.session_state.pg3_load_data = False

    if st.session_state.files or st.session_state.pg3_load_data:
        if st.session_state.dir_path:
            if st.button("Load data"):
                st.session_state.pg3_load_data = True

                (
                    st.session_state.nosig_exps,
                    odors_list,
                    st.session_state.sorted_sig_data,
                ) = import_data()

                st.info(
                    f"Response data loaded successfully for "
                    f"{len(st.session_state.files)} experiments. Summary .xlsx"
                    " file saved to the selected dictory as "
                    "compiled_dataset_analysis.xlsx"
                )

                st.session_state.sig_odors = check_sig_odors(odors_list)

                # if load data is clicked again, doesn't display plots/slider
                st.session_state.pg3_plots_list = False

            # if data has been loaded, always show plotting buttons
            if (
                st.session_state.pg3_load_data
                and len(st.session_state.nosig_exps)
                != len(st.session_state.files)
                and st.session_state.dir_path
            ):
                if st.button("Plot data"):
                    generate_plots()

                # display slider and plots if plots have already been generated
                # even if Plot data isn't clicked again
                if st.session_state.pg3_plots_list:
                    st.session_state.selected_odor = st.selectbox(
                        "Select odor number to display its corresponding plots:",
                        options=st.session_state.sig_odors,
                    )

                    if st.session_state.selected_odor:
                        display_plots()


if __name__ == "__main__":
    main()
