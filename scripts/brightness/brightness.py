import time
# import smbus
import sys
import RPi.GPIO as GPIO
from multiprocessing import Process
import logging
import argparse
from tsl2561 import TSL2561

formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

GPIO_PIN = 27
TSL_SENSOR = None

LUX_LEVEL_1 = 5
BRIGHTNESS_LEVEL_1 = 60

LUX_LEVEL_2 = 20
BRIGHTNESS_LEVEL_2 = 140

LUX_LEVEL_3 = 100
BRIGHTNESS_LEVEL_3 = 180

LUX_LEVEL_4 = 200
BRIGHTNESS_LEVEL_4 = 210

# > LUX_LEVEL_4
BRIGHTNESS_LEVEL_MAX = 254

TRANSISTION_SPEED = 0.02

NIGHT_MODE_ON_LUX = 20
NIGHT_MODE_OFF_LUX = 100

def read_sensor():
    lux = TSL_SENSOR.lux()
    logger.debug(f"lux reading: {lux}")
    return lux


def set_brightness(lux_reading):
    # Read current brightness from memory
    with open("/sys/class/backlight/rpi_backlight/brightness", "r") as x:
        current_brightness = int(x.read())

    # Calculate target screen brightness value
    target_brightness = BRIGHTNESS_LEVEL_1                                        # Default value
    level = 0

    if lux_reading in range(0, LUX_LEVEL_1):
        target_brightness = BRIGHTNESS_LEVEL_1
        level = 1
    elif lux_reading in range(LUX_LEVEL_1+1, LUX_LEVEL_2):
        target_brightness = BRIGHTNESS_LEVEL_2
        level = 2
    elif lux_reading in range(LUX_LEVEL_2+1, LUX_LEVEL_3):
        target_brightness = BRIGHTNESS_LEVEL_3
        level = 3
    elif lux_reading in range(LUX_LEVEL_3+1, LUX_LEVEL_4):
        target_brightness = BRIGHTNESS_LEVEL_4
        level = 4
    elif lux_reading > LUX_LEVEL_4:
        target_brightness = BRIGHTNESS_LEVEL_MAX
        level = 5
    
    logger.debug("Current brightness: %d, Target brightness: %d", current_brightness, target_brightness)

    if (target_brightness != current_brightness):
        logger.info("Changing brightness to level %s/5 (lux: %d, current: %d, target brightness: %d)", level, lux_reading, current_brightness, target_brightness)

        direction = -1 if current_brightness > target_brightness else 1
        with open("/sys/class/backlight/rpi_backlight/brightness", "w") as f:
            for brightness in range(current_brightness, target_brightness+direction, direction):
                logger.debug("Setting brightness %d", brightness)
                f.write(str(brightness))
                f.flush()
                time.sleep(TRANSISTION_SPEED)

    else:
        logger.debug("No change")


def set_day_night_mode(lux_reading):
    GPIO.setup(GPIO_PIN, GPIO.IN)
    current_state = GPIO.input(GPIO_PIN) 
    logger.debug("Nightmode - current %d, lux_reading %d", current_state, lux_reading)

    GPIO.setup(GPIO_PIN, GPIO.OUT)
    # Setting up GPIO
    if lux_reading < NIGHT_MODE_ON_LUX and current_state == False:
        GPIO.output(GPIO_PIN, True)                       # set "Night mode"
        logger.info("Setting night mode")
    if lux_reading > NIGHT_MODE_OFF_LUX and current_state:
        GPIO.output(GPIO_PIN, False)                       # set "Night mode" false
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
        raise ValueError('Invalid log level: %s' % args.log)
    logger.setLevel(numeric_level)

    logger.info('Connecting to sensor...')
    try:
        TSL_SENSOR = TSL2561(debug=True)
        logger.info('successfull')
    except:
        logger.exception('Could not connect to sensor!')
        exit(2)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.OUT)

    day_night_mode = GPIO.input(GPIO_PIN)
    logger.info("day night mode: %d", day_night_mode)

    try:
        while True:
            lux = read_sensor()
            p1 = Process(target=set_brightness, args=(lux,))
            p1.start()
            p2 = Process(target=set_day_night_mode, args=(lux,))
            p2.start()
            p1.join()
            p2.join()
            time.sleep(2)
    except KeyboardInterrupt:
        exit
    except Exception as ex:
        logger.error(ex)
        exit(1)
    finally:
        GPIO.cleanup()