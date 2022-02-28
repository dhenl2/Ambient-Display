cd /home/pi/Python
sudo chown -R pi ../Python
sudo -u pi python3 -u main.py > output.txt 2> error.txt &
cd
