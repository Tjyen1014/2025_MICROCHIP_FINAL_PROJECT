# PIC18F Game System - PC UI Execution Guide

This document explains how to execute the Python UI interface on a computer, supporting both **Simulation Mode (No Hardware)** and **Real Hardware Mode (Connected to PIC board)**.

## 1. Prerequisites

Before starting, please ensure that **Python 3.x** is installed on your computer.

### Install Required Packages

Please open the Terminal or Command Prompt (CMD) and enter the following command to install `pygame` (graphics engine) and `pyserial` (communication module):

```
pip install pygame pyserial
```

## 2. Configuration and Mode Switching

Open the `main_ui.py` file. The **CONFIG & SETTINGS** block at the top is the main configuration area.

### Core Switch: Simulation vs. Real

```
# SIMULATION SWITCH 
# True:  Enable "Simulation Mode". Automatically plays a pre-recorded game script, no hardware connection required.
# False: Enable "Real Hardware Mode". Attempts to connect to the SERIAL_PORT defined below.
USE_SIMULATION = True
```

### Port Settings (Required for Real Hardware Mode only)

If you set `USE_SIMULATION` to `False`,  must change `SERIAL_PORT` to the actual port where your PIC board is connected.

```
# Windows users typically use 'COM3', 'COM4', etc.
# Mac/Linux users typically use '/dev/ttyUSB0' or '/dev/tty.usbmodem...'
SERIAL_PORT = 'COM3'
BAUD_RATE = 9600       # Do not change, must match the PIC Firmware
```

## 3. Execution

In the terminal, navigate to the folder containing the program and run:

```
python ui.py
```