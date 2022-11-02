#!/usr/bin/env python3

try:
    import serial
except ModuleNotFoundError:
    pass
import argparse
from typing import List, Optional
from threading import Lock

class LedController:
    GROUP_COUNT = 4 # the number of LED groups defined by the STM32 controller
    GAMMA = 2.2 # gamma correction factor for the LED strips for better color rendition
    CHANNEL_COMPENSATION = [1, 1.5, 2, 1] # the LED-strips are somewhat "less than ideal", and blue is a factor of ~3 brighter than red

    def __init__(self) -> None:
        self._device = "/dev/tty.usbserial"  # default device
        self._baudrate = 9600  # default baudrate

        # the state that was most recently sent to the controller, provided that the class instance stays alive
        # defaults to 4x full bright because that's what the controller does when it is powered on
        self._state = self.stateFromHexColors(["ff"])

        # a threading lock is set around serial operations, in case calls are made from threads
        self._lock = Lock()

        try:
            self._serial = serial.Serial(timeout=0, write_timeout=1)
        except NameError:
            print(
                "pySerial module is not installed, so there is no connection with the controller. Try installing it with `python3 -m pip install pyserial`."
            )
            self._serial = None

    def update(self) -> None:
        # it is up to the user of this class to periodocally call this `update` method
        if not self._serial or not self._serial.is_open:
            return

        # flush any pending incoming data
        self._lock.acquire() # make sure this does not happen while another thread is sending data
        self._flushIncomingData()
        self._lock.release()

    def setSerialOptions(self, device: Optional[str], baudrate: Optional[int]) -> None:
        if not self._serial:  # in case pyserial is not available
            return

        if self._serial.is_open:
            raise Exception("serial device is already open")
            return

        if device:
            self._device = device
        if baudrate:
            self._baudrate = baudrate

    def openDevice(self) -> None:
        if not self._serial:  # in case pyserial is not available
            return

        self._serial.port = self._device
        self._serial.baud = self._baudrate
        self._serial.open()  # this may throw its own exception if there's an error opening the device

    def closeDevice(self) -> None:
        if not self._serial:  # in case pyserial is not available
            return

        # flush any pending incoming data
        self._serial.reset_input_buffer()

        if self._serial.is_open:
            self._serial.close()

    def setState(self, state: List[bytes]) -> None:
        if len(state) != self.GROUP_COUNT or not all([len(v) == 4 for v in state]):
            raise ValueError("new state is invalidly defined")

        self._lock.acquire()

        if self._serial and not self._serial.is_open:
            self.openDevice()

        self._state = state

        # Gamma-correct the values sent to the controller
        # NB: the controller expects byte values from 0-100 instead of 0-255, for reasons
        corrected_state = [bytes([int(pow(value/(self.CHANNEL_COMPENSATION[index] * 255), self.GAMMA) * 100) for (index, value) in enumerate(group)]) for group in state]

        if self._serial:
            # prepend state with is single FF "startbyte"
            buffer = b'\xff'+ b''.join(corrected_state)
            # this may throw its own exception if there's an error writing to the serial device
            self._serial.write(buffer)

            # get and ignore response
            self._flushIncomingData()

        self._lock.release()

    def getState(self) -> List[bytes]:
        return self._state

    def parseHexColor(self, hex_color: str) -> bytes:
        hex_bytes = bytes.fromhex(hex_color)
        hex_length = len(hex_bytes)
        if hex_length == 1:
            # RGB and W all equal value
            # input: 0x88 output: 0x88888888
            hex_bytes = hex_bytes * 4
        elif hex_length == 2:
            # RGB all equal, W separate value
            # input: 0x8844 output: 0x88888840
            hex_bytes = hex_bytes[0:1] * 3 + hex_bytes[1:2]
        elif hex_length == 3:
            # RGB only, turn off W
            # input: 0x884422 output: 0x88442200
            hex_bytes = hex_bytes + b"\x00"
        elif hex_length == 4:
            # RGBW as is
            # input: 0x88442211 output: 0x88442211
            pass
        else:
            raise ValueError("only 4 hex bytes are expected per value")

        return hex_bytes


    def stateFromHexColors(self, hex_colors: List[str]) -> List[bytes]:
        if len(hex_colors) == 1:
            # use same value for all groups
            hex_colors = hex_colors * self.GROUP_COUNT
        if len(hex_colors) != self.GROUP_COUNT:
            raise ValueError("only %d or 1 values may be specified" % self.GROUP_COUNT)

        return [self.parseHexColor(value) for value in hex_colors]

    def stateToHexColors(self, state: List[bytes]) -> List[str]:
        return [value.hex() for value in state]

    def _flushIncomingData(self) -> None:
        incoming = b""
        while self._serial.in_waiting:
            incoming += self._serial.read()
        if incoming != b"":
            print("Incoming data from controller: " + repr(incoming))



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
        "--device",
        type=str,
        help="the serial device to connect with, defaults to /dev/tty.usbserial",
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
    if args.device or args.baud:
        ledController.setSerialOptions(device=args.device, baudrate=args.baud)
    if args.colors:
        ledController.setState(ledController.stateFromHexColors(args.colors))

    print("Current colors: %s" % " ".join(ledController.stateToHexColors(ledController.getState())))
