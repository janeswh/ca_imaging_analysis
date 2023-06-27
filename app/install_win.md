# Using the app on Windows

## Initial Installation
1. Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/). After installation, you may get a notification that you need to update WSL2:

![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win1.png)

2. Follow the steps described here (https://learn.microsoft.com/en-us/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package) and complete everything through step 5 (don’t need to do step 6). 

3. Download and install [VcXserv](https://sourceforge.net/projects/vcxsrv/). After installing, restart your computer.

    1. Start up VcXsrv by typing xlaunch in the Start Menu search. Go through the dialogue box by clicking “Next”, leaving everything default until “Extra Settings”. Make sure all the checkboxes are checked (importantly, make sure "Disable access control" is checked). Click “Next” one more time, then Finish. If Windows Defender Firewall pops up, click “Allow access.”

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win2.png)


4. Download the web app [here](https://pitt-my.sharepoint.com/personal/cheetham_pitt_edu/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fcheetham%5Fpitt%5Fedu%2FDocuments%2FCheetham%20lab%2Froi%5Fanalysis%5Fapp%5Ftest%2Ezip&parent=%2Fpersonal%2Fcheetham%5Fpitt%5Fedu%2FDocuments%2FCheetham%20lab) and unzip the file contents. There will be two folders: the cleanedup_files are example test data, and the roi_app_x.y.z folder contains the actual web app. 

    1. Move the roi_app_x.y.z folder into the same folder that contains all the experiments that you want to analyze. The app will be able to access anything that’s in the same directory as itself, so you can place the roi_app folder in as high of a directory as you want. Example shown below:

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win3.png)

    2. Make sure the folder names containing the raw experiment ROI txt files are formatted exactly as shown above.

    3. Within each experiment folder, ensure that the solenoid info .txt file name is formatted exactly as shown below. You don’t need to rename/reformat the ROI .txt files containing the raw intensity values.

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win4.png)

## Starting the web app for the first time

1. Make sure you have both Docker and VcXsrv open and running. Docker might take awhile to start depending on your computer.

2. The first time you run everything, you'll need to give your PC permission to run the script.

    1. Go to the roi_app_x.y.z folder.

    2. Right click on run_docker_win.ps1. If you're using Windows 11, click "Copy as path". Otherwise, click "Properties" and copy the full path of the file next to "Location".

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win5.png)

    3. Open up Start Menu, type `powershell` in the search bar, and right click on Windows PowerShell > Run as Administrator, click yes.
    
    4. In the terminal window, type `Unblock-File -Path `C:\Users\Bob\Documents\GCaMP6s\roi_app_0.1.0\run_docker_win.ps1, but replace the path with the actual path to the .ps1 file on your system. Make sure there are no quotes around the path name. Press Enter. See example below:

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win6.png)

    5. In the next command line, type `set-executionpolicy remotesigned` and Press Enter. Enter `Y` after the prompt is displayed:

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win7.png)

3. After the above steps, for subsequent runs, you should be able to right click on run_docker_win.ps1 and click "Run with PowerShell."

    1. If Windows Defender Firewall pops up again, click “Allow access”.

    2. A PowerShell window should pop up.

    3. The web app will have started successfully if you see the following message “You can now view your Streamlit app…”

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win8.png)

    4. Open up a browser and enter localhost:8501 in the address bar. The analysis app should appear.

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win9.png)

4. After the initial set-up, you can open the app by just double-clicking on run_docker_win.ps1 (just need to have both Docker and VcXsrv open, and make sure the VcXsrv settings are configured correctly as described previously).


## Steps for exiting the script properly

1. Close the browser window where the app is running, and close the Terminal window.
2. Go to Docker Desktop, and in the left sidebar, click on Containers.
3. You should see under “Image” something like roi_analysis_0.1.0 - click on the trash can icon to delete the container.

![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win10.png)

4. Exit VcXsrv by looking for an X icon in your taskbar icons, right clicking on it, and clicking Exit.

![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/win/win11.png)















