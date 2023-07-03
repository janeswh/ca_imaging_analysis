# Changelog

## [0.2.0] - 2023-06-30

### Changed

- Added compilation of measurements for one acute/chronic dataset into .xlsx file, automatically generated after loading data
- Set negative AUC values to 0 for all odors including blank
- Made file/data `st.session_state` variables unique to each `st.Page`
- Upgraded to Python 3.11

### Added

- Duplicated color scales to increase the number of mice and ROIs that can be plotted in acute and chronic experiments
- Added modules to be imported by streamlit pages

### Fixed

- Fixed pick directory button not working after path has been entered manually

### Removed

- Removed duplicate functions/methods

## [0.1.0] - 2023-03-08

### Changed

- Changed color scale of `3_Plot_Multiple_Acute_Imaging_Data.py` and tweaked marker opacity values

### Added

- Added Changelog page
- Added description of basic functionalities in the app home page
- Display error message if uploaded file is incorrect/not the expected file

### Fixed

- Fixed `plot_list` and `load_data` `st.session_state` variables to be unique across app pages
