#! /bin/bash

docker run -it -e "PULSE_SERVER=${PULSE_SERVER}" -v /mnt/wslg/:/mnt/wslg -v $PWD/src:/app -p 8501:8501 imax32/vinyl-recorder $1