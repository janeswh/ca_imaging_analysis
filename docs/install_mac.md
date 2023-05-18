# Using the app on Mac OS

## Initial Installation
1. Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/). Make sure you select the correct download for your computer processor chip. You can check your chip type by clicking on the Apple icon in the top left corner of your screen > About this Mac.

![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac1.png)

2. Download and install [XQuartz](https://www.xquartz.org/). After installing, restart your computer.

    1. Start XQuartz (you can search for it using the top right search icon.)

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac2.png)

    2. Then, click XQuartz at the top left corner of the screen > Settings.

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac3.png)

    3. Click on the Security tab and check “Allow connections from network clients”.

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac4.png)

3. Download the web app [here](https://pitt-my.sharepoint.com/personal/cheetham_pitt_edu/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fcheetham%5Fpitt%5Fedu%2FDocuments%2FCheetham%20lab%2Froi%5Fanalysis%5Fapp%5Ftest%2Ezip&parent=%2Fpersonal%2Fcheetham%5Fpitt%5Fedu%2FDocuments%2FCheetham%20lab) and unzip the file contents. There will be two folders: the cleanedup_files are example test data, and the roi_app_x.y.z folder contains the actual web app. 

    1. Move the roi_app_x.y.z folder into the same folder that contains all the experiments that you want to analyze. The app will be able to access anything that’s in the same directory as itself, so you can place the roi_app folder in as high of a directory as you want. Example shown below:

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac5.png)

    2. Make sure the folder names containing the raw experiment ROI txt files are formatted exactly as shown above.

    3. Within each experiment folder, ensure that the solenoid info .txt file name is formatted exactly as shown below. You don’t need to rename/reformat the ROI .txt files containing the raw intensity values.

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac6.png)

## Starting the web app for the first time

1. Make sure you have both Docker and XQuartz open and running. Docker might take awhile to start depending on your computer.

2. Go to the roi_app_x.y.z folder.
    1. Right click on the run_docker_mac.sh file, click Get Info, then Under “Open with:”, click on “Other”.

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac7.png)

    2. In the window that pops up, click on the dropdown box next to Enable and click “All Applications”.

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac8.png)

    3. Scroll down to “Utilities” on the leftmost list, click on the folder, and scroll down to “Terminal” and click on it. Make sure you check the “Always Open With” box, then click Add.

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac9.png)

3. Double-click on the run_docker_mac.sh file.

4. If you get a security message saying that it’s from an unidentified developer, as shown below, click OK.

    ![](https://github.com/janeswh/ca_imaging_analysis/blob/main/docs/media/mac/mac10.png)










