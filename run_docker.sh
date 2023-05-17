#!/bin/bash
# Allow X server connection
xhost +local:root
docker run -it --rm \
    -e DISPLAY=$DISPLAY \
    --env="QT_X11_NO_MITSHM=1" \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /home/jhuang:/app/local_computer \
    -p 8501:8501 \
    roi_analysis
# Disallow X server connection
xhost -local:root
