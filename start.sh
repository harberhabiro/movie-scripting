killall screen

screen -dm -S movies sudo python3.8 server.py && screen -r movies
