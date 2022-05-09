#!/usr/bin/env python3

from ledcontroller import LedController
from flask import Flask, request, jsonify
import json

ledController = LedController()
app = Flask(__name__)

@app.route('/', methods=['GET'])
def showCurrentState():
    state_string = ledController.stateToString(ledController.getState())
    result = {"colors": state_string.split(" ")}
    return jsonify(result)

@app.route('/', methods=['POST'])
def setState():
    try:
        request_data = json.loads(request.data)
    except json.JSONDecodeError:
        return ("no or malformed data supplied", 400)

    try:
        state_values = request_data["colors"]
    except KeyError:
        return ("no colors specified", 400)

    try:
        state = ledController.stateFromString(" ".join(state_values))
        ledController.setState(state)
    except Exception as e:
        return (str(e), 400)

    return showCurrentState()

app.run(debug=True)