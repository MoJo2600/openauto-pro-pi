#!/usr/bin/python
 
import RPi.GPIO as GPIO
import time
import sys
import subprocess, os
import signal
import psutil
import logging
import argparse

# Set up logging
formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Your GPIO pin here
GPIO_CAMERA_SWITCH=8
CAMERA_VIEW_WIDTH=1024
CAMERA_VIEW_HEIGHT=600
CAMERA_VIEW_FPS=30
# Tweak for your camera setup. 
# Flip switches: -vf -hf
CAMERA_VIEW_CMD = f"raspivid -t 0 -w {CAMERA_VIEW_WIDTH} -h {CAMERA_VIEW_HEIGHT} -fps {CAMERA_VIEW_FPS}" 

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(GPIO_CAMERA_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# raspivid process
p = None
camera_state = False 
switching = False
run = True

def signal_handler(sig, frame):
    """Event handler for program events"""
    global p, running
    run = False
    if p is not None:
        os.killpg(p.pid, signal.SIGTERM)
    GPIO.cleanup()
    sys.exit(0)

def kill_camera_process():
    global p

    try:
        logger.info("stop camera process")
        for proc in psutil.process_iter():
            if proc.name() == 'raspivid':
                proc.kill()
    except:
        logger.info("Error killing video process")

def switch_camera(on):
    global p

    if on:
        logger.info("Switching camera: on")
        try:
            if p != None:
                logger.info("Camera already on")
                kill_camera_process()
            p=subprocess.Popen(CAMERA_VIEW_CMD, shell=True, preexec_fn=os.setsid)
#            if p != None and p.returncode > 0: 
#                kill_camera_process()
        except:
            logger.error("Error starting camera process")

    else:
        logger.info("Switching camera: off")
        kill_camera_process()

    switching = False

def check_switch():
    """Check the switch"""
    global camera_state
    check_state = GPIO.input(GPIO_CAMERA_SWITCH)
    if check_state != camera_state:
        logger.info(f"Switch state: {check_state}")
        camera_state = check_state
        try:
            switch_camera(camera_state)
        except:
            logger.error("Could not switch camera")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log", nargs='?', const='DEBUG', help='log level (DEBUG, INFO, WARN, ERROR)')
    args = parser.parse_args()

    log_level = 'INFO'
    if args.log is not None:
        log_level = args.log.upper()

    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logger.setLevel(numeric_level)

    logger.info("Listening for gpio event")
    signal.signal(signal.SIGINT, signal_handler)

    try:
        while run:
            check_switch()
            time.sleep(0.25)
    except KeyboardInterrupt:
        exit
    except Exception as ex:
        logger.error(ex)
        exit(1)
    finally:
        GPIO.cleanup()
