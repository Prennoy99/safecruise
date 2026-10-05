"""Spike 2 (M0, ADR-002): send one CAN frame on a vcan interface and receive it back.

Usage: python tools/spikes/vcan_roundtrip.py [CHANNEL]   (default vcan0)
Exit code 0 if the frame arrives unchanged within the timeout, 1 otherwise.
"""

import sys

import can

TIMEOUT_S = 1.0


def main(channel: str = "vcan0") -> int:
    sent = can.Message(arbitration_id=0x123, data=bytes(range(8)), is_extended_id=False)
    with (
        can.Bus(interface="socketcan", channel=channel, receive_own_messages=False) as rx,
        can.Bus(interface="socketcan", channel=channel) as tx,
    ):
        tx.send(sent)
        got = rx.recv(timeout=TIMEOUT_S)
    ok = got is not None and got.arbitration_id == sent.arbitration_id and got.data == sent.data
    print(f"{channel}: sent {sent}")
    print(f"{channel}: received {got}")
    print("round trip OK" if ok else "round trip FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
