#!/usr/bin/env bash
cd "$(dirname ${BASH_SOURCE[0]})"
exp_dir=$(cd ../ && pwd)

# IP_ADDRESS=$(ifconfig |awk '/inet /&&!/127.0.0.1/{print $2;exit}')

#xhost +$IP_ADDRESS

# export DISPLAY=:0
/opt/X11/bin/xhost +

docker pull janeswh/ca_imaging_analysis
docker run --rm -e DISPLAY=host.docker.internal:0.0 -v /tmp/.X11-unix:/tmp/.X11-unix -p:8501:8501 -v $exp_dir:/app_dir/local_files janeswh/ca_imaging_analysis

# xhost -$IP_ADDRESS

