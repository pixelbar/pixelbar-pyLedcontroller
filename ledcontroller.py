#!/usr/bin/env python3

try:
    import serial
except ModuleNotFoundError:
    pass
import re
import argparse
from typing import List, Optional


class LedController:
    GROUP_COUNT = 4

    def __init__(self) -> None:
        self._port = "/dev/tty.usbserial"  # default port
        self._baudrate = 9600  # default baudrate

        # the state that was most recently sent to the controller, provided that the class instance stays alive
        # defaults to 4x full bright because that's what the controller does when it is powered on
        self._state = self.stateFromString("ff")

        try:
            self._serial = serial.Serial()
        except NameError:
            print(
                "pySerial module is not installed, so there is no connection with the controller. Try installing it with `python -m pip install pyserial`."
            )
            self._serial = None

    def setSerialOptions(self, port: Optional[str], baudrate: Optional[int]) -> None:
        if not self._serial:  # in case pyserial is not available
            return

        if self._serial.is_open:
            raise Exception("serial port is already open")
            return

        if port:
            self._port = port
        if baudrate:
            self._baudrate = baudrate

    def openPort(self) -> None:
        if not self._serial:  # in case pyserial is not available
            return

        self._serial.port = self._port
        self._serial.baud = self._baudrate
        self._serial.open()  # this may throw its own exception if there's an error opening the port

    def closePort(self) -> None:
        if not self._serial:  # in case pyserial is not available
            return

        if self._serial.is_open:
            self._serial.close()

    def setState(self, state: List[bytes]) -> None:
        if len(state) != self.GROUP_COUNT or not all([len(v) == 4 for v in state]):
            raise ValueError("new state is invalidly defined")

        if self._serial and not self._serial.is_open:
            self.openPort()

        self._state = state

        if self._serial:
            # this may throw its own exception if there's an error writing to the serial port
            self._serial.write(255)  # 'start byte', mandated by the controller
            for value in self._state:
                self._serial.write(self._state[value])

    def getState(self) -> List[bytes]:
        return self._state

    def stateFromString(self, state_string: str) -> List[bytes]:
        values = state_string.split(" ")
        if len(values) == 1:
            # use same value for all groups
            values = values * self.GROUP_COUNT
        if len(values) != self.GROUP_COUNT:
            raise ValueError("only %d or 1 values may be specified" % self.GROUP_COUNT)

        result = []
        for value in values:
            value_bytes = bytes.fromhex(value)
            value_lenght = len(value_bytes)
            if value_lenght == 1:
                # RGB and W all equal value
                # input: 0x88 output: 0x88888888
                value_bytes = value_bytes * 4
            elif value_lenght == 2:
                # RGB all equal, W separate value
                # input: 0x8844 output: 0x88888840
                value_bytes = value_bytes[0:1] * 3 + value_bytes[1:2]
            elif value_lenght == 3:
                # RGB only, turn off W
                # input: 0x884422 output: 0x88442200
                value_bytes = value_bytes + b"\x00"
            elif value_lenght == 4:
                # RGBW as is
                # input: 0x88442211 output: 0x88442211
                pass
            else:
                raise ValueError("only 4 hex bytes are expected per value")
            result.append(value_bytes)

        return result

    def stateToString(self, state: List[bytes]) -> str:
        return " ".join([l.hex() for l in state])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Adjust the RGBW lighting at the pixelbar.",
        epilog="Either 1 or 4 colors can be specified. If 1 color is specified, the same color is used for all 4 groups. " +
            "Colors can be specified as either 1, 2, 3 or 4 hexadecimal bytes. " +
            "1 byte will be interpreted as the same value for all R,G,B and W led; " +
            "2 bytes will be interpreted as a value for R, G, and B, and the other value for W; " +
            "3 bytes will be interpreted as an R, G, B value and will turn off W; " +
            "4 bytes will used for R, G, B, W as is."
    )
    parser.add_argument(
        "--port",
        type=str,
        help="the serial port to connect with, defaults to /dev/tty.usbserial",
    )
    parser.add_argument(
        "--baud",
        type=int,
        help="the serial communication speed, defaults to 9600"
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
    if args.port or args.baud:
        ledController.setSerialOptions(port=args.port, baudrate=args.baud)
    if args.colors:
        ledController.setState(ledController.stateFromString(" ".join(args.colors)))

    print("Current colors: %s" % ledController.stateToString(ledController.getState()))
