#!/usr/bin/env python3
"""
Jetson-side serial motor test for ESP32.

Examples:
  python3 motor_straight_test.py --port /dev/ttyUSB0 --base 120 --time 2
  python3 motor_straight_test.py --port /dev/ttyUSB0 --base 120 --fl 1.00 --fr 0.96 --bl 1.02 --br 1.00 --time 2
  python3 motor_straight_test.py --port /dev/ttyUSB0 --interactive
"""

import argparse
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError as exc:
    raise SystemExit(
        "pyserial is required. Install it with: python3 -m pip install pyserial"
    ) from exc


def find_default_port():
    candidates = []
    for port in list_ports.comports():
        device = port.device
        if "USB" in device or "ACM" in device:
            candidates.append(device)
    return candidates[0] if candidates else None


def open_serial(port, baud):
    ser = serial.Serial(port, baudrate=baud, timeout=1.0, write_timeout=1.0)
    time.sleep(2.0)
    ser.reset_input_buffer()
    return ser


def send_command(ser, command, read_for=0.6):
    print(f"> {command}")
    ser.write((command.strip() + "\n").encode("ascii"))
    ser.flush()

    deadline = time.time() + read_for
    lines = []
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if line:
            lines.append(line)
            print(f"< {line}")
            if line in {"OK DONE", "OK STOP"} or line.startswith("ERR"):
                break
    return lines


def run_once(ser, args):
    duration_ms = int(args.time * 1000)
    command = (
        f"RUN {args.base} {args.fl:.4f} {args.fr:.4f} "
        f"{args.bl:.4f} {args.br:.4f} {duration_ms}"
    )
    send_command(ser, command, read_for=args.time + 3.0)


def interactive_loop(ser, args):
    fl = args.fl
    fr = args.fr
    bl = args.bl
    br = args.br
    base = args.base
    seconds = args.time

    print()
    print("Interactive mode")
    print("  Enter: run with current values")
    print("  fl 1.03 / fr 0.96 / bl 1.00 / br 1.02: change one scale")
    print("  base 130: change base PWM")
    print("  time 1.5: change run time")
    print("  set 120 115 122 118: direct wheel PWM values")
    print("  stop: stop motors")
    print("  q: quit")

    while True:
        print()
        print(
            f"current: base={base}, time={seconds:.2f}s, "
            f"fl={fl:.3f}, fr={fr:.3f}, bl={bl:.3f}, br={br:.3f}"
        )
        try:
            text = input("motor-test> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            send_command(ser, "STOP")
            return

        if text in {"q", "quit", "exit"}:
            send_command(ser, "STOP")
            return
        if text == "stop":
            send_command(ser, "STOP")
            continue
        if text == "":
            duration_ms = int(seconds * 1000)
            command = f"RUN {base} {fl:.4f} {fr:.4f} {bl:.4f} {br:.4f} {duration_ms}"
            send_command(ser, command, read_for=seconds + 3.0)
            continue

        parts = text.split()
        if len(parts) == 2 and parts[0] in {"fl", "fr", "bl", "br"}:
            try:
                value = float(parts[1])
            except ValueError:
                print("number expected")
                continue
            if parts[0] == "fl":
                fl = value
            elif parts[0] == "fr":
                fr = value
            elif parts[0] == "bl":
                bl = value
            else:
                br = value
            continue

        if len(parts) == 2 and parts[0] == "base":
            try:
                base = int(parts[1])
            except ValueError:
                print("integer expected")
            continue

        if len(parts) == 2 and parts[0] == "time":
            try:
                seconds = float(parts[1])
            except ValueError:
                print("number expected")
            continue

        if len(parts) == 5 and parts[0] == "set":
            try:
                values = [int(value) for value in parts[1:]]
            except ValueError:
                print("four integer PWM values expected")
                continue
            send_command(ser, "SET " + " ".join(str(value) for value in values))
            continue

        print("Unknown input. Try Enter, fl 1.03, base 130, time 1.5, set ..., stop, q.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run a straight-line motor test through ESP32 serial.")
    parser.add_argument("--port", default=None, help="ESP32 serial port, usually /dev/ttyUSB0 or /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    parser.add_argument("--base", type=int, default=120, help="Base PWM, 0..255. Start around 90-130.")
    parser.add_argument("--time", type=float, default=2.0, help="Run time in seconds")
    parser.add_argument("--fl", type=float, default=1.0, help="Front-left motor scale")
    parser.add_argument("--fr", type=float, default=1.0, help="Front-right motor scale")
    parser.add_argument("--bl", type=float, default=1.0, help="Back-left motor scale")
    parser.add_argument("--br", type=float, default=1.0, help="Back-right motor scale")
    parser.add_argument("--interactive", action="store_true", help="Tune values in a small prompt")
    return parser.parse_args()


def main():
    args = parse_args()
    port = args.port or find_default_port()
    if not port:
        print("Could not find ESP32 serial port. Try --port /dev/ttyUSB0 or --port /dev/ttyACM0.", file=sys.stderr)
        return 2

    print(f"Opening {port} at {args.baud} baud")
    with open_serial(port, args.baud) as ser:
        send_command(ser, "PING")
        if args.interactive:
            interactive_loop(ser, args)
        else:
            run_once(ser, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
