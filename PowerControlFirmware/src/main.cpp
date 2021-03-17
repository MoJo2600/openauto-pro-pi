
#include <Arduino.h>
#include <avr/io.h>
#include <util/delay.h>

#define PIN_LED PB1
#define PIN_POWER_CNTRL PB3
#define PIN_IGN_SENSE PB2
#define PIN_PI_IN PB4
#define NUDGE_PULSE_DURATION 150
#define WAITTIME_FOR_PI_TO_RESPOND 3000L

enum State {
  IDLE,
  WAIT_FOR_PI_BOOT,
  RUNNING,
  WAIT_FOR_PI_SHUTDOWN
};

volatile State g_currentState = IDLE;
unsigned long g_nudgeStartMillis = 0L;
bool power_on = true;

void setup() {
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_POWER_CNTRL, OUTPUT);
  digitalWrite(PIN_POWER_CNTRL, power_on);
  pinMode(PIN_IGN_SENSE, INPUT);
  pinMode(PIN_PI_IN, INPUT_PULLUP);
}

void loop() {

  switch(g_currentState) {
    case IDLE:
      if (digitalRead(PIN_IGN_SENSE)) {
        // Ignition on, enable power for pi to boot
        g_currentState = WAIT_FOR_PI_BOOT;
        digitalWrite(PIN_POWER_CNTRL, 0);
      }
      break;
    case WAIT_FOR_PI_BOOT:
      analogWrite(PIN_LED, sin( 2 * PI / NUDGE_PULSE_DURATION * (millis() - g_nudgeStartMillis) + 3 * PI / 2) * 128 + 128);
      if(millis() - g_nudgeStartMillis > WAITTIME_FOR_PI_TO_RESPOND) {
        // Pi did not boot, cut power
        g_currentState = IDLE;
        digitalWrite(PIN_POWER_CNTRL, 1);
      } 
      if(digitalRead(PIN_PI_IN)) {
        // Pi did respond, keep power on
        g_currentState = RUNNING;
        analogWrite(PIN_LED, 255);
      }
      break;
    case RUNNING:
      break;
    case WAIT_FOR_PI_SHUTDOWN:
      break;
  }
}