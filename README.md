# pi_robot

`pi_robot` is a simple Python application that uses the Raspberry Pi to control a physical robot using OpenAI's realtime API. The robot has basic body parts like a mouth, ears, eyes, eyebrows, etc. that can be linked to simple physical hardware like LEDs and servo motors via the Pi's GPIO pins.

## Prerequisites

- A Raspberry Pi board (any model that supports Raspberry Pi OS)
- A USB drive (16GB or larger recommended)
- A power supply for the Raspberry Pi
- A USB microphone and speaker
- An internet connection

## Steps to Set Up and Run `pi_robot`

### 1. Install Dependencies

Open a terminal on the Raspberry Pi and run the following commands:

```sh
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install portaudio19-dev python3-dev
```

### 2. Connect USB Microphone and Speaker

Ensure your USB microphone and speaker are connected. You can verify their detection using:

```sh
arecord -l  # Lists available recording devices
aplay -l    # Lists available playback devices
```

### 3. Clone the Repository

Clone the `pi_robot` repository from GitHub:

```sh
git clone git@github.com:jimmingcheng/pi_robot.git
cd pi_robot
```

### 4. Build the Project

Run the `make` command to compile and set up the project:

```sh
make
```

### 5. Set Up Config File

Copy the sample configuration file and edit it as needed:

```sh
cp sample_config.yaml config.yaml
vi config.yaml
```

### 6. Run `pi_robot`

Start the `pi_robot` application using the Python virtual environment:

```sh
venv/bin/python -m pi_robot.robot
```

## Notes

- Ensure that SSH is enabled on the Raspberry Pi if you want to access it remotely.
- You may need to configure additional hardware settings depending on the functionality of `pi_robot`.
- If you encounter permission issues with `git clone`, ensure that your SSH keys are correctly set up on GitHub.
- Configure the USB microphone and speaker settings in `alsamixer` if needed.

---
This guide provides a basic setup for running `pi_robot`. Modify as needed based on your specific Raspberry Pi model and configuration.


