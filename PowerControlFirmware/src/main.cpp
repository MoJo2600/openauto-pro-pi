
#include <Arduino.h>
#include <avr/io.h>
#include <util/delay.h>
#include <Bounce2.h>

#define PIN_LED PB1
#define PIN_POWER_CNTRL PB3
#define PIN_IGN_SENSE PB2
#define PIN_PI_IN PB4
#define PIN_PI_OUT PB0
#define PULSE_DURATION 150
#define PULSE_DURATION_FAST 30
#define WAITTIME_FOR_PI_TO_RESPOND 2000

enum State {
  IDLE,
  WAIT_FOR_PI_BOOT,
  RUNNING,
  WAIT_FOR_PI_SHUTDOWN,
  SHUTDOWN,
};

volatile State g_currentState = IDLE;
unsigned long g_eventStartMillis = 0L;
Bounce b_piIn = Bounce(); // Instantiate a Bounce object
Bounce b_ignSense = Bounce(); // Instantiate a Bounce object

void setup() {

  b_piIn.attach(PIN_PI_IN, INPUT); // Attach the debouncer to a pin with INPUT_PULLUP mode
  b_piIn.interval(125); // Use a debounce interval of 125 milliseconds

  b_ignSense.attach(PIN_IGN_SENSE, INPUT); // Attach the debouncer to a pin with INPUT_PULLUP mode
  b_ignSense.interval(250); // Use a debounce interval of 250 milliseconds

  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_POWER_CNTRL, OUTPUT);
  digitalWrite(PIN_POWER_CNTRL, 0);
  pinMode(PIN_IGN_SENSE, INPUT);
  pinMode(PIN_PI_IN, INPUT);
  pinMode(PIN_PI_OUT, OUTPUT);

  digitalWrite(PIN_PI_OUT, 0);
}

void loop() {
  b_piIn.update();                                                             // Update the Bounce instance
  b_ignSense.update();                                                             // Update the Bounce instance

  switch(g_currentState) {
    case IDLE:
      if (digitalRead(PIN_IGN_SENSE)) {                                        // Ignition is on, enable power for pi to boot
        digitalWrite(PIN_POWER_CNTRL, 1);
        g_eventStartMillis = millis();
        g_currentState = WAIT_FOR_PI_BOOT;
      }

      break;
    case WAIT_FOR_PI_BOOT:
      analogWrite(PIN_LED, sin( 2 * PI / PULSE_DURATION * (millis() - g_eventStartMillis) + 3 * PI / 2) * 128 + 128);

      if (b_piIn.rose()) {                                                     // Pi signals it has booted
        analogWrite(PIN_LED, 255);
        g_currentState = RUNNING;
      }

      if(millis() - g_eventStartMillis > WAITTIME_FOR_PI_TO_RESPOND) {         // Pi did not boot, cut power
        g_eventStartMillis = millis();
        g_currentState = SHUTDOWN;
      }

      break;
    case RUNNING:
      if (!b_ignSense.fell()) {                                       // Ignition is switched off shutdown pi
        g_eventStartMillis = millis();
        digitalWrite(PIN_PI_OUT, 1);                                           // Tell pi to shut down
        g_currentState = WAIT_FOR_PI_SHUTDOWN;
      }

      break;
    case WAIT_FOR_PI_SHUTDOWN:
      analogWrite(PIN_LED, sin( 2 * PI / PULSE_DURATION_FAST * (millis() - g_eventStartMillis) + 3 * PI / 2) * 128 + 128);

      if (b_piIn.fell()) {                                                     // Pi did shut down, cut power
        g_currentState = SHUTDOWN;
      }

      if(millis() - g_eventStartMillis > WAITTIME_FOR_PI_TO_RESPOND) {         // Pi did not shut down in time, cut power anyways
        g_currentState = SHUTDOWN;
      }

      break;
    case SHUTDOWN:
      analogWrite(PIN_LED, 0);
      digitalWrite(PIN_POWER_CNTRL, 0);
      g_currentState = IDLE;
      break;
    //   analogWrite(PIN_LED, sin( 2 * PI / PULSE_DURATION_FAST * (millis() - g_eventStartMillis) + 3 * PI / 2) * 128 + 128);

    //   break;
  }
}