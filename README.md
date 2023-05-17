## About
The ROI Analysis app imports .txt files containing raw fluorescence intensity data from imaging experiments, then collates and analyzes the data before saving analysis results as human readable .xlsx files. Additional functions include user-friendly data visualization and exploration across multiple experimental sessions.

## Getting started

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) 
* [VcXserv](https://sourceforge.net/projects/vcxsrv) (on Windows)
* [XQuartz](https://www.xquartz.org) (on Mac)
* Docker image (contact author for access)

### Installation
1. Install Docker Desktop.
2. Install VcXserv or XQuartz depending on your OS, and configure to disable access control.
3. Download the zip file containing the Docker image and unzip the contents.
4. Place the roi_app_x.y.z folder in the same directory containing all the experiment folders that you wish to analyze. Make sure the experiment folder names and solenoid_info.txt file names are formatted as shown below: 

```
.
└── C:/
    └── Users/
        └── Bob/
            └── Documents/
                └── GCaMP6s/
                    ├── 211119--834736-5-6_ROI1/
                    │   ├── 211119_834736-5-6_ROI1_solenoid_info.txt
                    │   ├── 211119--834736-5-6_ROI1.txt
                    │   ├── 211119--834736-5-6_ROI1_001.txt
                    │   ├── 211119--834736-5-6_ROI1_002.txt
                    │   ├── 211119--834736-5-6_ROI1_003.txt
                    │   ├── 211119--834736-5-6_ROI1_004.txt
                    │   ├── 211119--834736-5-6_ROI1_005.txt
                    │   ├── 211119--834736-5-6_ROI1_006.txt
                    │   ├── 211119--834736-5-6_ROI1_007.txt
                    │   ├── 211119--834736-5-6_ROI1_008.txt
                    │   ├── 211119--834736-5-6_ROI1_009.txt
                    │   └── 211119--834736-5-6_ROI1_010.txt
                    ├── 220118--957214-1-3_ROI1
                    ├── 220118--953068_2-1_ROI2
                    └── roi_app_0.1.0/
                        ├── roi_analysis_0.1.0.tar
                        ├── run_docker_win.ps1
                        └── readme_win.txt
```
### Starting the app
1. Start up Docker Desktop and VcXserv/Xquartz, ensuring that access control is disabled.
2. Load the Docker image in a container.
3. The web app can be accessed in a browser at the address `localhost:8501`
4. Analysis .xlsx output files are saved to the same directory chosen in the select folder popup window.

## Available functions

### Collating and analyzing raw .txt files

