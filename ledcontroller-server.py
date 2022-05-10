#!/usr/bin/env python3

from ledcontroller import LedController
from flask import Flask, request, jsonify
import argparse
import json

parser = argparse.ArgumentParser(
    description="Minimal REST server to adjust the RGBW lighting at the pixelbar."
)
parser.add_argument(
    "--port",
    type=int,
    default=5000,
    help="the port the server listens to, defaults to 5000"
)
parser.add_argument(
    "--device",
    type=str,
    help="the serial device to connect with, defaults to /dev/tty.usbserial",
)
parser.add_argument(
    "--baud",
    type=int,
    help="the serial communication speed, defaults to 9600"
)
args = parser.parse_args()

ledController = LedController()
if args.device or args.baud:
    ledController.setSerialOptions(device=args.device, baudrate=args.baud)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def showCurrentState():
    hex_colors = ledController.stateToHexColors(ledController.getState())
    result = {"colors": hex_colors}
    return jsonify(result)

@app.route('/', methods=['POST'])
def setState():
    try:
        request_data = json.loads(request.data)
    except json.JSONDecodeError:
        return ("no or malformed data supplied", 400)

    try:
        hex_colors = request_data["colors"]
    except KeyError:
        return ("no colors specified", 400)

    try:
        state = ledController.stateFromHexColors(hex_colors)
        ledController.setState(state)
    except Exception as e:
        return (str(e), 400)

    return showCurrentState()

app.run(port=args.port, debug=True)