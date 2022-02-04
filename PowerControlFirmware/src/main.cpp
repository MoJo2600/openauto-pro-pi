
#include <Arduino.h>
#include <avr/io.h>
#include <util/delay.h>
#include <Bounce2.h>

#define PIN_LED PB1                                                            // Pin to LED
#define PIN_POWER_CNTRL PB3                                                    // Pin to enable / disable power to Pi
#define PIN_IGN_SENSE PB2                                                      // Pin to sense ignition
#define PIN_PI_IN PB4                                                          // Pin from Pi to tell it is up and running
#define PIN_PI_OUT PB0                                                         // Pin to Pi to tell it to shut down
#define PULSE_DURATION_SLOW 150
#define PULSE_DURATION_FAST 30
#define PULSE_DURATION_SUPER_FAST 20
#define WAITTIME_FOR_PI_TO_RESPOND 6000
#define FINAL_WAIT_TIME 1000

enum State {
  WAIT_FOR_PI_BOOT,
  RUNNING,
  WAIT_FOR_PI_SHUTDOWN,
  WAIT_FOR_PI_COME_BACK,
  SHUTDOWN,
  KILL,
};

State g_currentState = WAIT_FOR_PI_BOOT;
unsigned long g_eventStartMillis = 0L;
Bounce b_ignSense = Bounce();                                                  // Instantiate a Bounce object

void pulseLed(int speed) {
  analogWrite(PIN_LED, sin( 2 * PI / speed * (millis() - g_eventStartMillis) + 3 * PI / 2) * 128 + 128);
}

void setup() {
  pinMode(PIN_PI_IN, INPUT);

  pinMode(PIN_LED, OUTPUT);

  pinMode(PIN_POWER_CNTRL, OUTPUT);
  digitalWrite(PIN_POWER_CNTRL, 1);

  pinMode(PIN_PI_OUT, OUTPUT);
  digitalWrite(PIN_PI_OUT, 0);

  b_ignSense.attach(PIN_IGN_SENSE, INPUT);                                     // Attach the debouncer to a pin with INPUT_PULLUP mode
  b_ignSense.interval(50);                                                     // Use a debounce interval of 250 milliseconds
}

void loop() {
  b_ignSense.update();                                                         // Update the Bounce instance  
  switch(g_currentState) {
    case WAIT_FOR_PI_BOOT:
      pulseLed(PULSE_DURATION_SLOW);

      if (digitalRead(PIN_PI_IN)) {                                            // Pi signals it has booted
        analogWrite(PIN_LED, 255);
        g_currentState = RUNNING;
      }

      if(millis() - g_eventStartMillis > WAITTIME_FOR_PI_TO_RESPOND) {         // Timeout Pi did not shut down in time, cut power anyways
        g_eventStartMillis = millis();                                         // Reset timeout timer
        g_currentState = SHUTDOWN;
      }

      break;
    case RUNNING:

      if (b_ignSense.fell()) {                                                 // Ignition is switched off shutdown pi
        g_eventStartMillis = millis();                                         // Reset timeout timer
        digitalWrite(PIN_PI_OUT, 1);                                           // Tell pi to shut down
        g_currentState = WAIT_FOR_PI_SHUTDOWN;
      }

      if (!digitalRead(PIN_PI_IN)) {                                           // Pi was switched off, but ignition is still on
        g_eventStartMillis = millis();                                         // Reset timeout timer
        g_currentState = WAIT_FOR_PI_COME_BACK;                                // Wait, maybe it was a reboot
      }

      break;
    case WAIT_FOR_PI_COME_BACK:
      pulseLed(PULSE_DURATION_SUPER_FAST);

      if(digitalRead(PIN_PI_IN)) {                                             // Pi did come back online back to running
        g_currentState = RUNNING;
      }

      if(millis() - g_eventStartMillis > WAITTIME_FOR_PI_TO_RESPOND) {         // Timeout Pi did not come back, cut power
        g_eventStartMillis = millis();                                         // Reset timeout timer
        g_currentState = SHUTDOWN;
      }

      break;
    case WAIT_FOR_PI_SHUTDOWN:
      pulseLed(PULSE_DURATION_FAST);

      if (!digitalRead(PIN_PI_IN)) {                                           // Pi did shut down, cut power
        g_eventStartMillis = millis();                                         // Reset timeout timer
        g_currentState = SHUTDOWN;
      }

      if(millis() - g_eventStartMillis > WAITTIME_FOR_PI_TO_RESPOND) {         // Timeout Pi did not shut down in time, cut power anyways
        g_eventStartMillis = millis();                                         // Reset timeout timer
        g_currentState = SHUTDOWN;
      }

      break;
    case SHUTDOWN:
      analogWrite(PIN_LED, 25);
      if(millis() - g_eventStartMillis > FINAL_WAIT_TIME) {                    // Final wait time to make sure everything shut down
        g_currentState = KILL;
      }
      break;
    case KILL:
      digitalWrite(PIN_LED, 0);
      digitalWrite(PIN_POWER_CNTRL, 0);
      break;
  }
}
