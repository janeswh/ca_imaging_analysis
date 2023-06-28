import plotly.graph_objects as go
import plotly.io as pio
from math import nan
import pandas as pd
import streamlit as st

pio.templates.default = "plotly_white"
import pdb


def set_color_scales(dataset_type):
    """
    Creates fixed color scales used for plotting
    """

    #  this creates color scales for 12 animals with 2 ROIs each
    if dataset_type == "acute":
        colorscale = {
            "marker": {
                1: ["rgba(237, 174, 73, 0.5)", "rgba(244, 206, 144, 0.5)"],
                2: ["rgba(0, 61, 91, 0.5)", "rgba(0, 109, 163, 0.5)"],
                3: ["rgba(209, 73, 91, 0.5)", "rgba(222, 124, 137, 0.5)"],
                4: ["rgba(0, 121, 140, 0.5)", "rgba(0, 177, 204, 0.5)"],
                5: ["rgba(223, 124, 82, 0.5)", "rgba(233, 164, 134, 0.5)"],
                6: ["rgba(48, 99, 142, 0.5)", "rgba(73, 139, 193, 0.5)"],
                7: ["rgba(237, 174, 73, 0.5)", "rgba(244, 206, 144, 0.5)"],
                8: ["rgba(0, 61, 91, 0.5)", "rgba(0, 109, 163, 0.5)"],
                9: ["rgba(209, 73, 91, 0.5)", "rgba(222, 124, 137, 0.5)"],
                10: ["rgba(0, 121, 140, 0.5)", "rgba(0, 177, 204, 0.5)"],
                11: ["rgba(223, 124, 82, 0.5)", "rgba(233, 164, 134, 0.5)"],
                12: ["rgba(48, 99, 142, 0.5)", "rgba(73, 139, 193, 0.5)"],
            },
            "lines": {
                1: ["#95610F", "#EDAE49"],
                2: ["#001B29", "#003D5B"],
                3: ["#621822", "#D1495B"],
                4: ["#004752", "#00798C"],
                5: ["#793416", "#DF7C52"],
                6: ["#1A354C", "#30638E"],
                7: ["#95610F", "#EDAE49"],
                8: ["#001B29", "#003D5B"],
                9: ["#621822", "#D1495B"],
                10: ["#004752", "#00798C"],
                11: ["#793416", "#DF7C52"],
                12: ["#1A354C", "#30638E"],
            },
        }
    elif dataset_type == "chronic":
        #  this creates color scales for 20 timepoints
        colorscale = {
            "marker": {
                1: "rgba(162, 255, 255, 0.5)",
                2: "rgba(126, 233, 255, 0.5)",
                3: "rgba(87, 202, 255, 0.5)",
                4: "rgba(36, 172, 255, 0.5)",
                5: "rgba(0, 142, 227, 0.5)",
                6: "rgba(0, 114, 196, 0.5)",
                7: "rgb(0, 87, 165, 0.5)",
                8: "rgba(0, 62, 135, 0.5)",
                9: "rgba(0, 38, 107, 0.5)",
                10: "rgba(0, 15, 79, 0.5)",
                11: "rgba(162, 255, 255, 0.5)",
                12: "rgba(126, 233, 255, 0.5)",
                13: "rgba(87, 202, 255, 0.5)",
                14: "rgba(36, 172, 255, 0.5)",
                15: "rgba(0, 142, 227, 0.5)",
                16: "rgba(0, 114, 196, 0.5)",
                17: "rgb(0, 87, 165, 0.5)",
                18: "rgba(0, 62, 135, 0.5)",
                19: "rgba(0, 38, 107, 0.5)",
                20: "rgba(0, 15, 79, 0.5)"
                # 10: "#000f4f",
            },
            "lines": "#000f4f",
        }

    return colorscale


def plot_acute_odor_measure_fig(
    sig_odor_exps,
    data_dict,
    odor,
    measure,
    total_animals,
    plot_groups,
    total_cols,
):
    """
    Plots the analysis values for specified odor and measurement
    """
    measure_fig = go.Figure()
    color_scale = set_color_scales("acute")

    for animal_ct, animal_id in enumerate(sig_odor_exps.keys()):
        for exp_ct, sig_experiment in enumerate(sig_odor_exps[animal_id]):
            exp_odor_df = data_dict[animal_id][sig_experiment][odor]

            add_measure_trace(
                measure_fig,
                exp_ct,
                sig_experiment,
                "acute",
                animal_id,
                exp_odor_df.loc[measure],
                animal_ct,
            )

            # only adds mean line if there is more than one pt
            if isinstance(exp_odor_df.loc[measure], pd.Series):
                add_acute_mean_line(
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


def plot_chronic_odor_measure_fig(
    sig_odor_exps,
    data_dict,
    odor,
    measure,
    sorted_dates,
):
    """
    Plots the analysis values for specified odor and measurement
    """
    measure_fig = go.Figure()

    # generates list holding the mean values for plotting later
    # fills non-sig sessions with 0 or nan depending on measure

    if measure == "Blank-subtracted DeltaF/F(%)" or measure == "Blank sub AUC":
        avgs = [0] * len(sorted_dates)
    elif measure == "Latency (s)" or measure == "Time to peak (s)":
        avgs = [nan] * len(sorted_dates)

    for exp_ct, sig_experiment in enumerate(sig_odor_exps):
        # gets the timepoint position of the experiment
        interval_ct = sorted_dates.index(sig_experiment) + 1
        exp_odor_df = data_dict[sig_experiment][odor]

        add_measure_trace(
            measure_fig,
            exp_ct,
            sig_experiment,
            "chronic",
            interval_ct,
            exp_odor_df.loc[measure],
        )

        # only adds mean value to list for plotting if
        # there is more than one pt per exp
        if isinstance(exp_odor_df.loc[measure], pd.Series):
            avgs[interval_ct - 1] = exp_odor_df.loc[measure].values.mean()

    add_chronic_means(measure_fig, sorted_dates, measure, avgs)

    return measure_fig


def add_acute_mean_line(
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


def add_chronic_means(measure_fig, sorted_dates, measure, avgs):
    # makes x-axis values for mean trace
    x_vals = list(range(1, len(sorted_dates) + 1))

    # adds mean line
    measure_fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=avgs,
            mode="lines",
            line=dict(color="orange", dash="dot"),
            name="Mean",
        )
    )

    # adds mean point dots for latency and time to peak
    if measure == "Latency (s)" or measure == "Time to peak (s)":
        measure_fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=avgs,
                mode="markers",
                marker=dict(color="orange"),
                name="Single Mean",
            )
        )


def add_measure_trace(
    fig,
    exp_ct,
    sig_experiment,
    dataset_type,
    x_interval,
    y_values,
    animal_ct=None,
):
    # checks whether values need to be put in artificial list
    if isinstance(y_values, pd.Series):
        x = [x_interval] * len(y_values.values)
        y = y_values.values.tolist()
    else:
        x = [x_interval]
        y = [y_values]

    color_scale = set_color_scales(dataset_type)
    if dataset_type == "acute":
        marker_color = color_scale["marker"][animal_ct + 1][exp_ct]
        line_color = color_scale["lines"][animal_ct + 1][exp_ct]
        legend_group = animal_ct
    elif dataset_type == "chronic":
        marker_color = color_scale["marker"][x_interval]
        line_color = color_scale["lines"]
        legend_group = exp_ct

    fig.add_trace(
        go.Box(
            x=x,
            y=y,
            line=dict(color="rgba(0,0,0,0)"),
            fillcolor="rgba(0,0,0,0)",
            boxpoints="all",
            pointpos=0,
            marker_color=marker_color,
            marker=dict(
                # opacity=0.5,
                line=dict(
                    color=line_color,
                    width=2,
                ),
                size=12,
            ),
            name=sig_experiment,
            legendgroup=legend_group,
            offsetgroup=exp_ct if dataset_type == "acute" else None,
        ),
    )


def get_acute_plot_params(all_roi_counts):
    """
    Counts the number of ROIs (columns) and animals plotted for each odor
    """

    # determines whether plot has groups for multiple ROI
    # also counts total number of columns - if groups are present,
    # animals with one ROI still have two columns

    if 2 in all_roi_counts:
        plot_groups = True
        zeroes = all_roi_counts.count(0)
        total_cols = (len(all_roi_counts) - zeroes) * 2

    else:
        plot_groups = False
        total_cols = sum(all_roi_counts)

    return plot_groups, total_cols


def position_acute_mean_line(
    total_animals, total_cols, plot_groups, animal_ct, exp_ct
):
    """
    Sets the positioning values for mean lines depending on whether each
    animal has multiple ROIs.
    """

    if plot_groups:
        start = (1 / total_cols) / 1.6
        line_width = (1 / total_animals) / 6
        within_group_interval = (1 / total_animals) / 8
        between_group_interval = (1 / total_animals) / 1.95

    else:
        start = (1 / total_animals) / 3.5
        line_width = (1 / total_animals) / 3
        between_group_interval = (1 / total_animals) / 1.4

    animal1_roi1_x0 = start
    animal1_roi1_x1 = start + line_width

    if plot_groups:
        animal1_roi2_x0 = animal1_roi1_x1 + within_group_interval
        animal1_roi2_x1 = animal1_roi2_x0 + line_width

    # sets positioning variable depending on animal and exp count

    # # this is for the very first data point
    if animal_ct == 0:
        if exp_ct == 0:
            x0 = animal1_roi1_x0
            x1 = animal1_roi1_x1
        else:
            x0 = animal1_roi2_x0
            x1 = animal1_roi2_x1

    # for the first data point in subsequent animals
    else:
        if exp_ct == 0:
            if plot_groups:
                x0 = (
                    animal1_roi2_x1
                    + (animal_ct * (between_group_interval))
                    + (animal_ct - 1)
                    * ((line_width * 2) + within_group_interval)
                )
            else:
                x0 = (
                    animal1_roi1_x1
                    + (animal_ct * (between_group_interval))
                    + (animal_ct - 1) * line_width
                )

        # if this is not exp_ct=0, then obviously plot_groups == True
        else:
            x0 = (
                animal1_roi2_x1
                + (animal_ct * (between_group_interval))
                + (animal_ct - 1) * ((line_width * 2) + within_group_interval)
                + line_width
                + within_group_interval
            )

        x1 = x0 + line_width

    return x0, x1


def format_fig(fig, measure, dataset_type, interval=None, sorted_dates=None):
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

    fig.update_xaxes(
        showticklabels=True,
        title_text="<br />Animal ID"
        if dataset_type == "acute"
        else f"<br />{interval}",
    )
    if dataset_type == "chronic":
        fig.update_xaxes(
            tickvals=list(range(1, len(sorted_dates) + 1)),
            range=[0.5, len(sorted_dates) + 1],
        )

    fig.update_yaxes(
        title_text=measure,
    )

    if measure == "Time to peak (s)":
        fig.update_yaxes(
            rangemode="tozero",
        )

    fig.update_layout(
        title={
            "text": measure,
            "x": 0.4,
            "xanchor": "center",
        },
        legend_title_text="Experiment ID<br />",
        showlegend=True,
    )

    if dataset_type == "acute":
        fig.update_layout(boxmode="group", boxgap=0.4)
