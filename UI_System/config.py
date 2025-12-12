import time

# ==========================================
#   SYSTEM CONFIGURATION
# ==========================================
# Serial Port Settings
# Windows: 'COM3', 'COM4' | Mac/Linux: '/dev/ttyUSB0'
SERIAL_PORT = 'COM3'   
BAUD_RATE = 2400

# Window Resolution & Performance
WIDTH, HEIGHT = 1300, 800
FPS = 60

# SIMULATION SWITCH
# True: Runs internal mock script (No hardware needed).
# False: Connects to actual UART hardware.
# This can be overridden by command line arguments.
USE_SIMULATION = True  

# ==========================================
#   COLOR PALETTE
# ==========================================
COLOR_BG = (5, 5, 10)           # Deep Void Blue (Background)
COLOR_GRID = (0, 60, 60)        # Dim Cyan (Grid Lines)
COLOR_GLOW = (0, 255, 255)      # Cyan Neon (Main Borders)
COLOR_ACCENT = (255, 0, 128)    # Magenta Neon (Alerts/Titles)
COLOR_TEXT = (220, 255, 255)    # Pale Cyan (General Text)
COLOR_INFO = (100, 200, 255)    # Info/Instruction Text
COLOR_P1 = (0, 255, 128)        # Player 1 Green
COLOR_P2 = (255, 128, 0)        # Player 2 Orange
COLOR_DANGER = (255, 50, 50)    # Critical Red (Alerts)
COLOR_CURSOR = (255, 255, 0)    # Tic-Tac-Toe Cursor Yellow
COLOR_MOLE_CORE = (255, 50, 50) # WAM Mole Inner Core
COLOR_MOLE_GLOW = (255, 100, 0) # WAM Mole Outer Glow
COLOR_DIM = (60, 60, 60)        # Inactive Element Gray

# ==========================================
#   SHARED STATE (THREAD-SAFE)
# ==========================================
# This dictionary acts as the bridge between the UART thread (Worker) 
# and the Pygame thread (Main UI).
shared_state = {
    "connected": False,      # Connection Status (True if Serial/Sim is active)
    "scene": "WAITING",      # Current Scene Key: START, HINT, TTT, REACT, WAM, END
    "raw_data": [],          # List of parsed data strings from UART
    "last_update": 0         # Timestamp of the last received packet
}