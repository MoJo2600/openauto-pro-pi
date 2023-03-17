"""
Backlight Control Script With TSL2561 Light Sensor

This script implements a recommendation from analog devices
https://www.analog.com/en/design-notes/a-simple-implementation-of-lcd-brightness-control-using-the-max44009-ambientlight-sensor.html
"""

import math
import time
from multiprocessing import Process, Value
import sys
import signal
import RPi.GPIO as GPIO
import logging
import argparse
from tsl2561 import *
from statistics import mean
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Configuration
with open("config.yml", "r") as ymlfile:
    cfg = load(ymlfile, Loader=Loader)

NIGHT_MODE_GPIO_PIN = cfg["night_mode_gpio_pin"]
LUX_SAMPLE_COUNT = cfg["lux_sample_count"]
NIGHT_MODE_ON_LUX = cfg["night_mode_on_lux"]
NIGHT_MODE_OFF_LUX = cfg["night_mode_off_lux"]
MAXIMUM_LUX_BREAKPOINT = cfg["maximum_lux_breakpoint"]
BRIGHTNESS_LEVEL_MIN = cfg["brightness_level_min"]
BRIGHTNESS_LEVEL_MAX = cfg["brightness_level_max"]

# private
current_lux = Value('i', 1)
current_brightness_percent = 0.5
desired_brightness_percent = 0.5
running = True
step_size = 0.01

def map_range(x, in_min, in_max, out_min, out_max):
    """Maps an value to a target range

    Args:
        x (_type_): The value to map
        in_min (_type_): Input minimum
        in_max (_type_): Input maximum
        out_min (_type_): Output minimum
        out_max (_type_): Output maximum

    Returns:
        _type_: The mapped value
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def get_brightness_percent_from_lux_reading(lux) -> float:
    """calculate screen brightness in percent for given lux

    Args:
        lux (int): The current light reading in lux

    Returns:
        float: The brightness in percent based on a function
    """
    if lux > MAXIMUM_LUX_BREAKPOINT:
        return 1.0
    if lux == 0:
        return 0
    else:
        return (9.9323 * math.log(lux) + 27.059) / 100.0;

def process_read_sensor(tsl_sensor, curr) -> None:
    """
    Reads the sensor and calculates the average of the last readings
    """
    global running

    lux_readings = []

    while running:
        try:
            # Reading the value does a time.sleep
            lux = tsl_sensor.lux()

            lux_readings.append(lux)
            if len(lux_readings) > LUX_SAMPLE_COUNT:
                lux_readings.pop(0)

            curr.value = int(mean(lux_readings))
            logger.info(f"lux reading: {lux}, avg: {curr.value}")
            time.sleep(0.5)
        except KeyboardInterrupt:
            break

def step_brightness() -> None:
    """Steps the brightness from current value to desired value
    """
    global current_brightness_percent, desired_brightness_percent, step_size

    if current_brightness_percent == desired_brightness_percent:
        return
    
    if current_brightness_percent > desired_brightness_percent:
        if (current_brightness_percent-step_size) < desired_brightness_percent:
            current_brightness_percent = desired_brightness_percent
        else:
            current_brightness_percent = current_brightness_percent - step_size
    elif current_brightness_percent < desired_brightness_percent:
        if (current_brightness_percent+step_size) > desired_brightness_percent:
            current_brightness_percent = desired_brightness_percent
        else:
            current_brightness_percent = current_brightness_percent + step_size

    set_brightness(current_brightness_percent)

def set_brightness(brightness_in_percent) -> None:
    """Sets the display brightness
    Calculates the correct value from percent value
    Args:
        brightness_in_percent (float): Brightness in percent
    """
    brightness = int(map_range(brightness_in_percent, 0.0, 1.0, BRIGHTNESS_LEVEL_MIN, BRIGHTNESS_LEVEL_MAX))
    logger.debug("brightness in percent: %s, brightness to set: %s", brightness_in_percent, brightness)
    try:
        with open("/sys/class/backlight/rpi_backlight/brightness", "w") as f:
            f.write(str(brightness))
            f.flush()
    except OSError as e:
        print(f"Unable to open brightness file: {e}", file=sys.stderr)
        return
    except Exception:
        logger.exception('Could not set brightness')

def set_day_night_mode(lux):
    """Sets the day/night mode via GPIO port

    Args:
        lux (int): Current light reading in lux
    """
    GPIO.setup(NIGHT_MODE_GPIO_PIN, GPIO.IN)
    current_state = GPIO.input(NIGHT_MODE_GPIO_PIN) 

    GPIO.setup(NIGHT_MODE_GPIO_PIN, GPIO.OUT)
    # Setting up GPIO
    if lux < NIGHT_MODE_ON_LUX and current_state == False:
        GPIO.output(NIGHT_MODE_GPIO_PIN, True)                       # set "Night mode"
        logger.info("Setting night mode")
    if lux > NIGHT_MODE_OFF_LUX and current_state:
        GPIO.output(NIGHT_MODE_GPIO_PIN, False)                       # set "Night mode" false
        logger.info("Setting day mode")


def start():
    """Start the script
    """
    global running, current_lux, current_brightness_percent, step_size, desired_brightness_percent

    current_lux = Value('i', 1)

    logger.info('Connecting to sensor...')
    try:
        tsl_sensor = TSL2561(autogain=False) # integration_time=TSL2561_INTEGRATIONTIME_101MS,
        logger.info('successfull')
    except:
        logger.exception('Could not connect to sensor!')
        running = False
        exit(1)

    running = True

    read_sensor = Process(target=process_read_sensor, args=(tsl_sensor, current_lux,))
    read_sensor.start()

    light_reading_counter = 0

    try:
        while running:
            start = time.time()
            step_brightness()
            set_day_night_mode(current_lux.value)
            if (light_reading_counter):
                light_reading_counter = light_reading_counter -1
            else:
                logger.debug("Current Lux %s", current_lux.value)
                light_reading_counter = 20                          # 2 seconds delay
                desired_brightness_percent = get_brightness_percent_from_lux_reading(current_lux.value)
                logger.debug("Desired brightness in percent %f", desired_brightness_percent)
                difference = abs(desired_brightness_percent - current_brightness_percent)
                step_size = 0.01 if (difference <= 0.01) else difference / 10.0

            # Adjust loop time to 100ms seconds for smooth transitions
            end = time.time()
            elapsed_time = end - start
            time.sleep(0.1 - elapsed_time)
    except KeyboardInterrupt:
        logger.info("Caught keyboard interrupt, canceling all tasks.")
        running = False
        read_sensor.join()
        read_sensor.terminate()
    except Exception as ex:
        logger.exception('Something went wrong')
        exit(1)
    finally:
        GPIO.cleanup()
        logger.info("Successfully shutdown brightness service.")
        exit

def stop():
    """Stop the script"""
    global running
    logger.info("Stopping brightness service")
    running = False
    GPIO.cleanup()
    sys.exit(0)

def _handle_sigterm(sig, frame):
    logger.warning('SIGTERM received...')
    stop()

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_sigterm)

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log", nargs='?', const='DEBUG', help='log level (DEBUG, INFO, WARN, ERROR)')
    args = parser.parse_args()

    log_level = 'INFO'
    if args.log is not None:
        log_level = args.log.upper()

    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log)
    logger.setLevel(numeric_level)

    # GPIO is in use by openauto so ignore warning about current use
    GPIO.setwarnings(False)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(NIGHT_MODE_GPIO_PIN, GPIO.OUT)

    day_night_mode = GPIO.input(NIGHT_MODE_GPIO_PIN)
    logger.info("Nightmode: %d", day_night_mode)

    start()