"""Bounded serial capture for the owner's ESP32 bench checks (macOS)."""
import argparse
import array
import fcntl
import os
from pathlib import Path
import select
import termios
import time

parser = argparse.ArgumentParser()
parser.add_argument('--port', default='/dev/cu.usbserial-0001')
parser.add_argument('--seconds', type=float, default=8)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--reset', action='store_true', help='Reset via USB RTS; release DTR boot selection.')
parser.add_argument('--send', choices=['x', 'p'], help='Send the bench sketch stop/replay command without resetting.')
args = parser.parse_args()
assert 0 < args.seconds <= 30
fd = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
chunks = []
size = 0
try:
    config = termios.tcgetattr(fd)
    config[0] = 0
    config[1] = 0
    config[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    config[3] = 0
    config[4] = termios.B115200
    config[5] = termios.B115200
    config[6][termios.VMIN] = 0
    config[6][termios.VTIME] = 1
    termios.tcsetattr(fd, termios.TCSANOW, config)
    # macOS custom baud may persist after esptool; explicitly set IOSSIOSPEED.
    fcntl.ioctl(fd, 0x80045402, array.array('I', [115200]))
    if args.reset:
        fcntl.ioctl(fd, termios.TIOCMBIC, array.array('I', [termios.TIOCM_DTR]))
        fcntl.ioctl(fd, termios.TIOCMBIS, array.array('I', [termios.TIOCM_RTS]))
        time.sleep(0.15)
        fcntl.ioctl(fd, termios.TIOCMBIC, array.array('I', [termios.TIOCM_RTS | termios.TIOCM_DTR]))
    elif args.send:
        # Release EN/boot controls in case the macOS driver asserted them on open.
        # Do not pulse either line when sending a command to a running sketch.
        fcntl.ioctl(fd, termios.TIOCMBIC, array.array('I', [termios.TIOCM_RTS | termios.TIOCM_DTR]))
        time.sleep(0.25)
    termios.tcflush(fd, termios.TCIFLUSH)
    if args.send:
        os.write(fd, args.send.encode('ascii'))
        termios.tcdrain(fd)
    deadline = time.monotonic() + args.seconds
    while size < 65536:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        readable, _, _ = select.select([fd], [], [], min(1, remaining))
        if readable:
            try:
                data = os.read(fd, min(8192, 65536 - size))
            except BlockingIOError:
                continue
            if data:
                chunks.append(data)
                size += len(data)
finally:
    os.close(fd)
data = b''.join(chunks)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_bytes(data)
lines = data.decode('utf-8', 'replace').splitlines()
readable = [line for line in lines if line and all(32 <= ord(c) <= 126 or c == '\t' for c in line)]
print(f'Captured {len(data)} bytes; {len(readable)} readable lines.')
for line in readable[-20:]:
    print(line[:240])
