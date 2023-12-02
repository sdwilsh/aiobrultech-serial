![Lint](https://github.com/sdwilsh/aiobrultech-serial/workflows/Lint/badge.svg)
![Build](https://github.com/sdwilsh/aiobrultech-serial/workflows/Build/badge.svg)
![PyPI](https://img.shields.io/pypi/v/aiobrultech_serial)
![Supported Python Versions](https://img.shields.io/pypi/pyversions/aiobrultech_serial)

# What is aiobrultech-serial?

This library talks to devices from [Brultech Research](https://www.brultech.com/)
over their serial port, using
[siobrultech-protocols](https://github.com/sdwilsh/siobrultech-protocols) to
decode the data.

## Installation

```
pip install aiobrultech-serial
```

## Usage

```python
from aiobrultech_serial import connect


async with connect("/dev/ttyUSB0") as connection:
    async for packet in connection.packets():
        print(f"{packet}")
```

Look at [`scripts/dump.py`](https://github.com/sdwilsh/aiobrultech-serial/blob/main/scripts/dump.py)
for a fuller example.

### API Calls

This library also supports getting and setting information on the attached
device. It supports all of the API calls available in
[siobrultech-protocols](https://github.com/sdwilsh/siobrultech-protocols).

## Development

### Setup

```
python3.11 -m venv .venv
source .venv/bin/activate

# Install Requirements
pip install -r requirements.txt

# Install Dev Requirements
pip install -r requirements-dev.txt

# One-Time Install of Commit Hooks
pre-commit install
```

### Testing

Tests are run with `pytest`.
