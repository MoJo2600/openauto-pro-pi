import time
import sys
import subprocess, os
import signal

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
RearView_Switch = 8 #25  # Your GPIO pin here
GPIO.setup(RearView_Switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

p = None

def signal_handler(sig, frame):
    if p is not None:
        os.killpg(p.pid, signal.SIGTERM)
    GPIO.cleanup()
    sys.exit(0)


def button_callback(channel):
    global p
    if GPIO.input(RearView_Switch):
        print "Button pressed"
        rpistr = "raspivid -t 0 -vf -w 1024 -h 600 -fps 30"  # Tweak for your camera setup.
        p=subprocess.Popen(rpistr,shell=True, preexec_fn=os.setsid)
    else:
        print "Button released"
        #if p is not None:
        os.killpg(p.pid, signal.SIGTERM)

GPIO.add_event_detect(RearView_Switch, GPIO.BOTH,
                      callback=button_callback, bouncetime=50)

signal.signal(signal.SIGINT, signal_handler)
signal.pause()
