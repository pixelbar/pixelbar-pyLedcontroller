#!/usr/bin/env python3
import argparse
from app.ledcontroller import LedController

parser = argparse.ArgumentParser(
    description="Adjust the RGBW lighting at the pixelbar.",
    epilog="Either 1 or 4 colors can be specified. If 1 color is specified, the same color is used for all 4 groups. "
    + "Colors can be specified as either 1, 2, 3 or 4 hexadecimal bytes. "
    + "1 byte will be interpreted as the same value for all R,G,B and W led; "
    + "2 bytes will be interpreted as a value for R, G, and B, and the other value for W; "
    + "3 bytes will be interpreted as an R, G, B value and will turn off W; "
    + "4 bytes will used for R, G, B, W as is.",
)
parser.add_argument(
    "--device",
    type=str,
    help="the serial device to connect with, defaults to /dev/tty.usbserial",
)
parser.add_argument(
    "--baud", type=int, help="the serial communication speed, defaults to 9600"
)
parser.add_argument(
    "colors",
    metavar="color",
    type=str,
    nargs="+",
    help="set of either 1 or 4 space-delimited hexadecimal color values, can be specified as 1,2,3 or 4 hex-bytes",
)
args = parser.parse_args()

ledController = LedController()
if args.device or args.baud:
    ledController.setSerialOptions(device=args.device, baudrate=args.baud)
if args.colors:
    ledController.setState(ledController.stateFromHexColors(args.colors))

print(f"Current colors: {ledController.getHexState()}")
