import streamlit as st

st.set_page_config(page_title="ROI Analysis Home")

st.write("# ROI Analysis App")

st.markdown(
    """
    Please click the links in the side bar to access the different functions 
    available in this app. See below for a description of each.

    ### *Load and Analyze txt Files*

    Loads the raw .txt files output by Fiji and collates into Excel .xlsx 
    files containing:


    1. all raw intensity values 
    2. average intensity values 
    3. kinetic properties of response values 

    ---

    ### *Plot One Imaging Session Data*

    Loads the avg intensity values from one imaging session and generates
    time series plots for all odors and all samples imaged.

    ---

    ### *Plot Multiple Acute Imaging Data*

    Plots the response properties for all odors with significant responses
    from the uploaded imaging sessions. All samples imaged are shown as 
    individual points grouped by animal ID.

    ---

    ### *Plot Chronic Imaging Data*

    Plots the response properties for all odors with significant responses
    from one animal across multiple imaging sessions (time on x-axis). Mean
    values over time are shown by connected lines or individual dots.
    """
)
