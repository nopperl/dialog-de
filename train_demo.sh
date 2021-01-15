#!/bin/sh
CONFIG=${1}
cd demo
if [ "$CONFIG" != "" ]; then
    rasa train nlu --config $CONFIG
else
    rasa train nlu
fi
