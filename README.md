# Automotive power hat for OpenAuto

This hat is designed to work together with OpenAuto Pro and deliver some functionality which makes integrating OpenAuto into your car easier.

![front](documentation/powerhat_front.png)

## Work in progress - a word of warning

I'm not an electronics professional and this board is currently work in progress. If somebody is willing to do a indepth review with me I would be very glad. Reach out to me on twitter [@MoJo2600](https://twitter.com/MoJo2600).

## Features

* Integrated 5A Power Supply
* Wide range power input (+7.5V to +40V)
* On-/Off circuit with ignition sensing
* 2 Digital inputs for e.g. reverse signal
* I2S sound
* RTC clock
* CSI to HDMI adapters to connect a display and camera
  * I2C bus availabe on the display connector for a light sensor
* Designed to fit exactly onto a [Geekworm x825](https://wiki.geekworm.com/index.php/X825) SSD V1 (Not tested with V2 but should fit)

## Connections
the following pins are used on the pi.

|Connection     | Pin |
|---------------|-----|
|I2C            |BCM23|
|I2C            |BCM24|
|REVERSE        |BCM8 |
|LIGHT          |BCM25|
|PI UP          |BCM23|
|SHUTDOWN       |BCM24|
|I2S DAC MUTE   |BCM16|
|I2S DAC BITCLK |BCM18|
|I2S DAC LRCLK  |BCM19|
|I2S DAC DATAIN |BCM21|

## History

Here is a picture of prototype V1 with a Mouseberry power supply.

![v1](documentation/v1.jpg)

## Disclaimer

Due to the fact we are not providing a product in the legal sense, we are also not providing any warranty in any aspect.
