# pixelbar-pyLedcontroller
A python tool to adjust the RGBW lighting at the pixelbar.

## setup
The script uses pySerial to communicate with the STM32 controller board. This can be installed with the following command:
```
python3 -m pip install pyserial
```
The user must be privileged to use serial devices. As a better alternative than to run the command as root, add the user to the `dialout` group:
```
sudo adduser $USER dialout
```

## usage
```
python3 ledcontroller.py [-h] [--device DEVICE] [--baud BAUD] color [color ...]
```

Adjust the RGBW lighting at the pixelbar.

positional arguments:
  color        set of either 1 or 4 space-delimited hexadecimal color values, can be specified as 1,2,3 or 4 hex-bytes

options:
  -h, --help   show this help message and exit
  --device DEVICE  the serial device to connect with, defaults to /dev/tty.usbserial
  --baud BAUD  the serial communication speed, defaults to 9600

Either 1 or 4 colors can be specified. If 1 color is specified, the same color is used for all 4 groups.

Colors can be specified as either 1, 2, 3 or 4 hexadecimal bytes.
- 1 byte will be interpreted as the same value for all R,G,B and W led;
- 2 bytes will be interpreted as a value for R, G, and B, and a value for W;
- 3 bytes will be interpreted as a R, G, B value and will turn off W;
- 4 bytes will used for R, G, B, W as is.

## examples
```
python3 ledcontroller.py 7f
```
Set all ledgroups to half-brightness RGB and W.

```
python3 ledcontroller.py --device /dev/ttyUSB0 40a0
```
Set all ledgroups to a mix of 25% cool white (provided by the RGB leds) and 60% warm white (provided by the white leds). Use device /dev/ttyUSB0 instead of the default device.

```
python3 ledcontroller.py ff0000 00ff00 0000ff 000000ff
```
Set the first group to red, the second group to green, the third group to blue and the fourth group to warm white. Note that the 4th value has 4 hex bytes, and the rgb led is turned off.

## REST server
A minimal REST server is provided as `ledcontroller-server.py`. It uses the LedController class also used for the command-line implementation above.
To run it To use the minimal ledcontroller REST server (), the Flask module must be installed:
```
python3 -m pip install flask
```
The server has a `GET` and a `POST` endpoint on device 5000, both returning the latest colors sent to the controller through the server-script.
To set the colors, use the POST endpoint with the following json data structure:
```
{
	"colors": ["80a0", "ff", "ff", "ff0000"]
}
```
All the same color formats as the command-line implementation are supported (1,2,3 or 4 HEX bytes).

## controller
All this assumes a controller that receives color commands via serial, with the following packet-structure:

* A start byte `0xFF`
* For each of the 4 LED groups a series of 4 bytes, respectively R,G,B,W

example-packet, resulting from `ledcontroller.py 8040`:
```
FF 80 80 80 40 80 80 80 40 80 80 80 40 80 80 80 40
```