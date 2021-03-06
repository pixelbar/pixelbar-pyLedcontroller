#!/usr/bin/env python3

from ledcontroller import LedController
from flask import Flask, request, jsonify
from threading import Thread
import time
import argparse
import json
import os.path

"""
The PixelLight touchscreen interface communicates with a server on 127.0.0.1:1234
The STM32 controller driving the LED strips is connected on /dev/ttyACM0, and is
communicating at 9600 baud

GET /api/v1/get to get the last sent values
POST /api/v1/set to set new values

data structure:
{
    "door": {"red": 100, "green": 50, "blue": 25, "white": 0}
    "kitchen": {"red": 50, "green": 25, "blue": 0, "white": 100}
    "stairs": {"red": 100, "green": 100, "blue": 100, "white": 0}
    "beamer": {"red": 0, "green": 0, "blue": 0, "white": 100}
}

The new PixelDash interface uses a more compact "v2" API on 127.0.0.1:1234

GET /api/v2 to get the last sent values
POST /api/v2 to set new values

data structure:
{
    "colors": [
        "000000ff", "ff7f3f00", "ffffff00", "7f3f00ff"
    ]
}
The inherent order of the light groups in the v2 API is determined by the light
controller hardware: beamer, door, stairs, kitchen
"""


device = ""
for i in range(0,9):
    device_path = "/dev/ttyACM%d" % i
    if os.path.exists(device_path):
        device = device_path
        break
if device == "":
    print("No ttyACM device found; is the STM32 board connected?")
    exit(1)

baudrate = 9600
port = 1234
groups = ["beamer", "door", "stairs", "kitchen"]
colors = ["red", "green", "blue", "white"]

ledController = LedController()
ledController.setSerialOptions(device=device, baudrate=baudrate)

app = Flask(__name__)

@app.route('/api/v1/get', methods=['GET'])
def showCurrentStateV1():
    state = ledController.getState()
    # convert from bytes (0-255) into ints (0-100)
    color_values = [
        [int(100 * value / 255) for value in group] for group in state
    ]

    # convert from nested list to nested named dict
    result = {
        group: {
            color: color_value for (color, color_value) in zip(colors, group_values)
        } for (group, group_values) in zip(groups, color_values)
    }

    return jsonify(result)

@app.route('/api/v1/set', methods=['POST'])
def setStateV1():
    try:
        request_data = json.loads(request.data.decode())
    except json.JSONDecodeError:
        return ("no or malformed data supplied", 400)

    state = []
    for group in groups:
        group_state = b""
        try:
            values = request_data[group]
        except KeyError:
            return ("no colors specified for group %s" % group, 400)
        for color in colors:
            try:
                value = values[color]
            except KeyError:
                return ("no %s value specified for group %s" % (color, group), 400)
            if value < 0 or value > 100:
                return ("illegal value %s specified for color %s in group %s" % (str(value), color, group))
            group_state = group_state + int(255 * value / 100).to_bytes(1, "big")
        state.append(group_state)

    try:
        ledController.setState(state)
    except Exception as e:
        print(e)
        return (str(e), 400)

    return showCurrentStateV1()

@app.route('/api/v2', methods=['GET'])
def showCurrentStateV2():
    hex_colors = ledController.stateToHexColors(ledController.getState())
    result = {"colors": hex_colors}
    return jsonify(result)


@app.route('/api/v2', methods=['POST'])
def setStateV2():
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
        print(e)
        return (str(e), 400)

    return showCurrentStateV2()


def updateLedController():
    while not closeThread:
        ledController.update()
        time.sleep(5)

updateThread = Thread(target=updateLedController, daemon=True)
closeThread = False
updateThread.start()


app.run(host="0.0.0.0", port=port, debug=False)
closeThread = True
