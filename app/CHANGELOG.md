# Changelog

## [0.5.1] - 2023-08-16

### Fixed

- Fixed `baseline_std3x3` using a different `avg_means` window length than `baseline`
- Fixed `max_frames` using a different `avg_means` window length than `peak`

## [0.5.0] - 2023-08-14

### Added

- Added support for Arm64/Apple chips

## [0.4.0] - 2023-08-10

### Added

- Added compatibility with new `solenoid_order.csv` files that contain odor panel type (1% or 10%)

## [0.3.1] - 2023-07-26

### Fixed

- Make Load and Analyze function ignore MacOS system files starting with `._`

## [0.3.0] - 2023-07-21

### Added

- Added compatibility with new Odor Delivery App's output `solenoid_order.csv` files while maintaining compatibility with Beichen's legacy solenoid_info.txt files

### Changed

- Only provide the option to export solenoid info if the experiment folder contains `solenoid_info.txt`; otherwise it's unnecessary because `solenoid_order.csv` exists

## [0.2.2] - 2023-07-14

### Fixed

- Fixed Odor 2 in `compiled_dataset_analysis.xlsx` always being blank

### Added

- Added Baseline to `compiled_dataset_analysis.xlsx`

## [0.2.1] - 2023-07-12

### Fixed

- Fixed Chronic Imaging plotting load file to display info that compiled .xlsx file has been generated

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
