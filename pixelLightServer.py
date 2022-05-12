#!/usr/bin/env python3

from ledcontroller import LedController
from flask import Flask, request, jsonify
import argparse
import json

device = "/dev/ttyACM0"
baudrate = 9600
port = 1234
groups = ["door", "kitchen", "stairs", "beamer"]
colors = ["red", "green", "blue", "white"]

ledController = LedController()
ledController.setSerialOptions(device=device, baudrate=baudrate)

app = Flask(__name__)

@app.route('/api/serial', methods=['GET'])
def showCurrentState():
    state = ledController.getState()
    # zip and comprehension magic to transmogrify state to what PixelLight.py wants
    color_values = [
        [dict(zip(colors, [int(100*value/255) for value in group])) for group in state]
    ]
    result = dict(zip(groups, zip(*color_values)))
    # unfortunately we created one too many lists
    result = {k:v[0] for (k,v) in result.items()}

    return jsonify(result)

@app.route('/api/set', methods=['POST'])
def setState():
    try:
        request_data = json.loads(request.data)
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

            group_state = group_state + int(255 * value / 100).to_bytes(1, "big")
        state.append(group_state)
    print(state)

    try:
        ledController.setState(state)
    except Exception as e:
        return (str(e), 400)

    return showCurrentState()

app.run(host="0.0.0.0", port=port, debug=True)