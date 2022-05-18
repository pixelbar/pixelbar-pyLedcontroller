class GroupState:
    GROUP_COUNT = 4  # the number of LED groups defined by the STM32 controller

    def __init__(
        self,
    ):
        self.groups = [LedState()] * self.GROUP_COUNT

    def set_all_groups(self, byte_vals: list[bytes]):
        assert len(self.groups) == len(
            byte_vals
        ), f"Numer of bytes to set ({len(byte_vals)}) needs to match number of groups ({len(self.groups)})"

        for group, values in zip(self.groups, byte_vals):
            group.from_bytes(values)

    def set_group(self, group: int, byte_vals: bytes):
        assert group >= 0, "whats a negative group?"
        assert group < self.GROUP_COUNT, "too big group"
        self.groups[group].set_rgbw(byte_vals)

    def send_format(self) -> bytes:

        states = [state.byte_repr() for state in self.groups]
        # prepend state with is single FF "startbyte"
        return b"\xff" + b"".join(states)


class LedState:
    def __init__(self):
        self.byte_vals: bytes = b""
        self.set_hex("FF")

    def from_hex(self, hex_vals: str):
        self.set_hex(hex_vals)

    def from_bytes(self, byte_vals: bytes):
        self.set_rgbw(byte_vals)

    def set_hex(self, hex_color: str):
        hex_bytes = bytes.fromhex(hex_color)
        hex_length = len(hex_bytes)
        if hex_length == 1:
            # RGB and W all equal value
            # input: 0x88 output: 0x88888888
            self.set_rgbw(hex_bytes * 4)
        elif hex_length == 2:
            # RGB all equal, W separate value
            # input: 0x8844 output: 0x88888840
            colors = hex_bytes[0:1]
            white = hex_bytes[1:2]
            self.set_rgbw(colors * 3 + white)
        elif hex_length == 3:
            # RGB only, turn off W
            # input: 0x884422 output: 0x88442200
            self.set_rgbw(hex_bytes[0:3] + b"\x00")
        elif hex_length == 4:
            # RGBW as is
            self.set_rgbw(hex_bytes)

        else:
            raise ValueError("only 4 hex bytes are expected per value")

    def byte_repr(self) -> bytes:
        return self.byte_vals

    def to_hex(self) -> list[str]:
        return [hex(a) for a in self.byte_vals]

    def set_rgbw(self, byte_values: bytes):
        assert len(byte_values) == 4
        self.byte_vals = byte_values
