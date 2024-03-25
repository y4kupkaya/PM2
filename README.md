
# PM2 Python Library for Process Management

## Introduction

This Python library provides a seamless integration with PM2, enabling users to automate the launching and management of processes using PM2 through Python. Designed to cater to developers and system administrators who require a programmable interface to control their processes with the power and flexibility of Python, this library simplifies interactions with PM2, making it more accessible and versatile.

## Features

- **Easy Process Management:** Start, stop, restart, and delete processes with simple Python functions.
- **Automatic Process Launch:** Automatically launch multiple processes with predefined configurations.
- **Real-time Process Monitoring:** Retrieve real-time information about process status, CPU, and memory usage.
- **Flexible Configuration:** Configure processes programmatically, including environment variables, names, and log file locations.
- **Event Handling:** Listen to and handle PM2 events directly within your Python scripts.

## Installation

To install the PM2 Python Library, run the following command:

```bash
pip install pm2
```

## Quick Start

To get started with the PM2 Python Library, here's a simple example that demonstrates how to start a process:

```python
from pm2 import PM2, AioPM2
import asyncio

pm2 = PM2()
aiopm2 = AioPM2()


# Sync Methods
def pm2_manager():
    # List all processes
    processes = pm2.list()
    print(processes)

    # Start a process
    pm2.start(
        "your_script.py",
        name="Script-Name",
        extra_args=["-arg1", "value1"],
        name="YourProcessName",
    )
    # Restart a process
    pm2.restart(name="Script-Name")  # or pid=12345 or pm_id=1

    # Stop a process
    pm2.stop(name="Script-Name")  # or pid=12345 or pm_id=1

    # Delete a process
    pm2.delete(name="Script-Name")  # or pid=12345 or pm_id=1


# Async Methods
async def pm2_manager():
    # List all processes
    processes = await aiopm2.list()
    print(processes)

    # Start a process
    await aiopm2.start(
        "your_script.py",
        name="Script-Name",
        extra_args=["-arg1", "value1"],
        name="Script-Name",
    )

    # Restart a process
    await aiopm2.restart(name="Script-Name")  # or pid=12345 or pm_id=1

    # Stop a process
    await aiopm2.stop(name="Script-Name")  # or pid=12345 or pm_id=1

    # Delete a process
    await aiopm2.delete(name="Script-Name")  # or pid=12345 or pm_id=1


# Run the function
pm2_manager()
# or
asyncio.run(pm2_manager())
```

Replace `'your_script.py'`, `'Script-Name'`, and the args as necessary to fit your needs.

## Contributing

Contributions are welcome! If you would like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature.
3. Add your changes and commit them.
4. Push to your branch.
5. Create a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/y4kupkaya/pm2/LICENSE) file for details.

## Acknowledgments

- Thanks to the PM2 team for creating such a powerful process manager.
- This library was inspired by the need to simplify process management in Python projects.
