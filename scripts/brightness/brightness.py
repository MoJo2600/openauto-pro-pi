# Based on https://raw.githubusercontent.com/Grawa/brisensor/master/BriSensor.py
import time
import smbus
import sys
import RPi.GPIO as GPIO
from multiprocessing import Process
import logging
import argparse

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

# NOTE Select in OAPro day/night settings "GPIO Pin":27
GPIO_PIN = 27
bus = smbus.SMBus(1)                                            # i2c bus number (NOTE Default value: 1)
reading_count = 0

def read_sensor():
    global reading_count
    # Create a list of brightness values (then calculate the average)
    luxlist = []
    for counter in range(2):                                     # Refresh time 0,5*10=5s
        bus.write_byte_data(0x39, 0x00 | 0x80, 0x03)
        data = bus.read_i2c_block_data(0x39, 0x0C | 0x80, 2)      # Read brightness values from GPIO sensor
        currluxvalue = data[1] * 256 + data[0]                    # current lux value from sensor
        luxlist.append(currluxvalue)                              # append current lux value to list
        time.sleep(0.1)                                           # for loop sampling rate min. (every 0.5s or 2Hz)

    # Calculate brightness average
    lux_reading = int(sum(luxlist) / len(luxlist))
    logger.debug("Measured lux values: %s", luxlist)
    logger.debug("Lux average: %d", lux_reading)

    reading_count = reading_count + 1
    if reading_count > 5:
        logger.info("Measured reading: %d", lux_reading)
        reading_count = 0
    return lux_reading

def set_brightness(lux_reading):
    # Calculate target screen brightness value
    target_brightness = 0                                       # Default value
    if lux_reading in range(0, 5):
        target_brightness = 60                                  # 1/5 brightness level
    elif lux_reading in range(5, 20):
        target_brightness = 140                                 # 2/5 brightness level
    elif lux_reading in range(20, 100):
        target_brightness = 180                                 # 3/5 brightness level
    elif lux_reading in range(100, 200):
        target_brightness = 210                                 # 4/5 brightness level
    elif lux_reading > 200:
        target_brightness = 254                                 # 5/5 brightness level

    # Read current brightness from memory
    with open("/sys/class/backlight/rpi_backlight/brightness", "r") as x:
        current_brightness = int(x.read())
    logger.debug("Current brightness from file %d", current_brightness)

    # Sometimes it is not possible to set the value and this scripts tries indefinately
    if target_brightness < (current_brightness - 1) or target_brightness > (current_brightness + 1):
        logger.info("Brightness switch: current brightness %d, target brightness %d", current_brightness, target_brightness)
    else:
        logger.debug("No change in brightness")
        return

    # Gradually adjust the brightness
    if current_brightness > target_brightness:                     # Set adaptation step (decreasing / increasing)
        step = -1
    else:
        step = 1

    for brightness in range(current_brightness, target_brightness, step):
        logger.debug("Setting brightness %d", brightness)
        with open("/sys/class/backlight/rpi_backlight/brightness", "w") as file:
            file.write(str(brightness))
        time.sleep(0.02)                            # transition speed

def set_day_night_mode(lux_reading):
    night_lux_value = 20
    threshold = 25                                       # day/night threshold

    current_state = GPIO.input(GPIO_PIN) 
    # Setting up GPIO
    if lux_reading < night_lux_value and current_state == False:
        GPIO.output(GPIO_PIN, True)                       # set "Night mode"
        logger.info("Setting night mode")
    if lux_reading > night_lux_value + threshold and current_state == True:
        GPIO.output(GPIO_PIN, False)                       # set "Night mode"i false
        logger.info("Setting day mode")

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

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.OUT)
    try:
        while True:
            lux = read_sensor()
            p1 = Process(target=set_brightness, args=(lux,))
            p1.start()
            p2 = Process(target=set_day_night_mode, args=(lux,))
            p2.start()
            p1.join()
            p2.join()

            time.sleep(0.5)
    except KeyboardInterrupt:
        exit
    except Exception as ex:
        logger.error(ex)
        exit(1)
    finally:
        GPIO.cleanup()


