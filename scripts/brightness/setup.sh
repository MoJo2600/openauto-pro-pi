#!/bin/bash
set -e
set -x

rm -rf venv/
sudo mkdir -p /opt/brightness
sudo cp -Rfv . /opt/brightness
cd /opt/brightness
sudo python3 -m venv venv
sudo ./venv/bin/pip3 install -r requirements.txt
sudo cp brightness.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable brightness
sudo systemctl start brightness