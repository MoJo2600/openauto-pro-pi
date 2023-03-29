
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
#define FINAL_WAIT_TIME 500

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
Bounce g_ignSense = Bounce();                                                  // Instantiate a Bounce object

// pin states
int g_ignitionOn = true;
int g_piOn = false;

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

  g_ignSense.attach(PIN_IGN_SENSE, INPUT);                                     // Attach the debouncer to a pin with INPUT_PULLUP mode
  g_ignSense.interval(150);                                                    // Use a debounce interval of 150 milliseconds
}

void switchState(State newState) {
  g_eventStartMillis = millis();                                               // Reset timeout timer
  g_currentState = newState;                                                   // Set new state
}

void loop() {
  if (g_ignSense.changed()) {                                                  // Get current pin states
    g_ignitionOn = g_ignSense.read();
  }
  g_piOn = digitalRead(PIN_PI_IN);

  switch(g_currentState) {
    case WAIT_FOR_PI_BOOT:
      pulseLed(PULSE_DURATION_SLOW);

      if (g_piOn) {                                                             // Pi signals it has booted
        switchState(RUNNING);
        return;
      }

      if(millis() - g_eventStartMillis > WAITTIME_FOR_PI_TO_RESPOND) {          // Timeout Pi did not shut down in time, cut power anyways
        switchState(SHUTDOWN);
        return;
      }

      break;
    case RUNNING:
      analogWrite(PIN_LED, 255);

      if (g_ignitionOn == false) {                                              // Ignition is switched off shutdown pi
        digitalWrite(PIN_PI_OUT, 1);                                            // Tell pi to shut down
        switchState(WAIT_FOR_PI_SHUTDOWN);
        return;
      }

      if (g_piOn == false) {                                                    // Pi was switched off, but ignition is still on
        switchState(WAIT_FOR_PI_COME_BACK);
        return;
      }

      break;
    case WAIT_FOR_PI_COME_BACK:                                                 // Ignition is on, but pi shut down - maybe a reboot?
      pulseLed(PULSE_DURATION_SUPER_FAST);

      if(g_piOn) {                                                              // Pi did come back online back to running
        switchState(RUNNING);
        return;
      }

      if(millis() - g_eventStartMillis > WAITTIME_FOR_PI_TO_RESPOND) {         // Timeout Pi did not come back, cut power
        switchState(SHUTDOWN);
        return;
      }

      break;
    case WAIT_FOR_PI_SHUTDOWN:                                                  // We told the pi to shut down, now we wait for shutdown
      pulseLed(PULSE_DURATION_FAST);

      if (g_piOn == false) {                                                    // Pi did shut down, cut power
        switchState(SHUTDOWN);
        return;
      }

      if(millis() - g_eventStartMillis > WAITTIME_FOR_PI_TO_RESPOND) {         // Timeout Pi did not shut down in time, cut power anyways
        switchState(SHUTDOWN);
        return;
      }

      break;
    case SHUTDOWN:
      analogWrite(PIN_LED, 25);

      if(millis() - g_eventStartMillis > FINAL_WAIT_TIME) {                    // Final wait time to make sure everything shut down
        switchState(KILL);
        return;
      }

      break;
    case KILL:
      digitalWrite(PIN_LED, 0);
      digitalWrite(PIN_POWER_CNTRL, 0);                                        // Shut down the power circuit

      // Usually shutting down the power circuit will shut down the attiny as well and the program ends here
      // It might happen, that the user restarts the engine during this time. If so, we want to
      // enable the power circuitry again after a clean shutdown
      delay(100);
      if (g_ignitionOn == true) {
        digitalWrite(PIN_POWER_CNTRL, 1);                                    // Enable the power circuit
        digitalWrite(PIN_PI_OUT, 0);
        switchState(WAIT_FOR_PI_BOOT);
      }

      break;
  }
  g_ignSense.update();                                                         // Update the Bounce instance
}
