#!/bin/bash
set -e
set -x

rm -rf venv/
sudo mkdir -p /opt/rearcamera
sudo cp -Rfv . /opt/rearcamera
cd /opt/rearcamera
sudo python3 -m venv venv
sudo ./venv/bin/pip3 install -r requirements.txt
sudo cp rearcamera.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable rearcamera
sudo systemctl start rearcamera