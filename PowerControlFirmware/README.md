# ATTINY firmware for power control

This firmeware controls the buck converter to power the PI. It waits for the PI to boot and signals the PI to shut down when the ignition is turned off.

## Pinout

## Implementation

## Flashing in WSL

Create udev rule for USBTiny to give regular users in `dialout` group rights to the device

```
echo 'SUBSYSTEM=="usb", ATTR{idProduct}=="0c9f", ATTR{idVendor}=="1781", MODE="0666", GROUP="dialout"' > /etc/udev/rules.d/99-USBTiny.rules
```

Restart the udev service

```
sudo service udev restart
sudo udevadm control --reload
```

Attach the USB device to the WSL

```
usbipd attach --bus-id X-Y
```

Flash your code