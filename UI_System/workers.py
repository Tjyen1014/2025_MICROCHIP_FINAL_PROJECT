import time
import serial
import random
from config import *

# ==========================================
#   SIMULATION WORKER (MOCK DATA)
# ==========================================
def simulation_worker():
    """
    Runs a scripted game scenario for testing UI without hardware.
    Covers TTT, Reaction, and Whac-A-Mole .
    """
    print("[SIM] Starting Simulation Mode ...")
    time.sleep(1)
    
    shared_state["scene"] = "START"
    shared_state["connected"] = True
    time.sleep(2)
    
    while True:
        # ----------------------------------------
        # STAGE 1: TIC-TAC-TOE
        # ----------------------------------------
        shared_state["scene"] = "HINT"
        shared_state["raw_data"] = ['1', '0', '0']; time.sleep(1)
        shared_state["raw_data"] = ['1', '1', '1']; time.sleep(1)

        shared_state["scene"] = "TTT"
        board = [0]*9
        # Scripted moves where P1 wins
        moves = [4, 0, 3, 5, 2, 1, 6] 
        current_p = 1
        
        for move in moves:
            # Simulate Cursor Thinking
            for _ in range(3):
                sim_cursor = random.randint(0, 8)
                data = [str(x) for x in board] + [str(current_p), '0', str(sim_cursor)]
                shared_state["raw_data"] = data
                shared_state["last_update"] = time.time()
                time.sleep(0.15)
            
            # Cursor Lock
            data = [str(x) for x in board] + [str(current_p), '0', str(move)]
            shared_state["raw_data"] = data
            shared_state["last_update"] = time.time()
            time.sleep(0.4)

            # Move Executed
            board[move] = current_p
            next_p = 2 if current_p == 1 else 1
            data = [str(x) for x in board] + [str(next_p), '0', str(move)]
            shared_state["raw_data"] = data
            shared_state["last_update"] = time.time()
            
            current_p = next_p
            time.sleep(0.5)
        
        # Winner Detected
        data = [str(x) for x in board] + ['2', '1', '6'] 
        shared_state["raw_data"] = data
        shared_state["last_update"] = time.time()
        time.sleep(3)

        # ----------------------------------------
        # STAGE 2: REACTION GAME
        # ----------------------------------------
        shared_state["scene"] = "HINT"
        shared_state["raw_data"] = ['2', '1', '1']; time.sleep(2)

        shared_state["scene"] = "REACT"
        target = 50
        
        # P1 Rolling
        for i in range(20):
            d1 = random.randint(0, 99)
            data = [str(target), str(d1), '0', '-1', '-1', '-1', '0', '1', '0']
            shared_state["raw_data"] = data
            shared_state["last_update"] = time.time()
            time.sleep(0.05)
            
        # P1 Locked
        p1_final = 48
        data = [str(target), str(p1_final), '0', str(p1_final), '-1', '-1', '0', '2', '0']
        shared_state["raw_data"] = data
        shared_state["last_update"] = time.time()
        time.sleep(1.5)
        
        # P2 Start Prompt
        time.sleep(1.0)

        # P2 Rolling
        for i in range(20):
            d2 = random.randint(0, 99)
            data = [str(target), str(p1_final), str(d2), str(p1_final), '-1', '-1', '0', '2', '1']
            shared_state["raw_data"] = data
            shared_state["last_update"] = time.time()
            time.sleep(0.05)
            
        # P2 Locked & Result
        p2_final = 55
        data = [str(target), str(p1_final), str(p2_final), str(p1_final), str(p2_final), '1', '0', '2', '2']
        shared_state["raw_data"] = data
        shared_state["last_update"] = time.time()
        time.sleep(4)

        # ----------------------------------------
        # STAGE 3: WHAC-A-MOLE (COMPLEX)
        # ----------------------------------------
        shared_state["scene"] = "HINT"
        shared_state["raw_data"] = ['3', '1', '1']; time.sleep(3)

        shared_state["scene"] = "WAM"
        score1, score2 = 0, 0
        moles = ['0'] * 9
        
        # Round 1: Player 1
        for t in range(20000, 0, -1000): # Shortened to 20s
            hf, mf = '0', '0'
            if t % 2000 == 0: 
                moles = ['0']*9
                moles[random.randint(0,8)] = '1'
            
            if t % 2000 == 1000:
                try: 
                    moles[moles.index('1')] = '0'
                    score1 += 10
                    hf = '1' # Hit Flag
                except: mf = '1' # Miss Flag
            
            data = [str(score1), str(score2), 'N', hf, mf, str(t), '-1', '1', '0'] + moles
            shared_state["raw_data"] = data
            shared_state["last_update"] = time.time()
            time.sleep(0.6)

        # Intermission
        for _ in range(15): 
            data = [str(score1), str(score2), 'N', '0', '0', '60000', '-1', '2', '0'] + ['0']*9
            shared_state["raw_data"] = data
            time.sleep(0.6)

        # Round 2: Player 2
        for t in range(20000, 0, -1000):
            hf, mf = '0', '0'
            if t % 2000 == 0: 
                moles = ['0']*9
                moles[random.randint(0,8)] = '1'
            if t % 2000 == 1000: 
                try: 
                    moles[moles.index('1')] = '0'
                    score2 += 15 # P2 is better
                    hf = '1'
                except: pass
            
            data = [str(score1), str(score2), 'N', hf, mf, str(t), '-1', '2', '1'] + moles
            shared_state["raw_data"] = data
            shared_state["last_update"] = time.time()
            time.sleep(0.6)

        # End Game
        winner = '2'
        shared_state["scene"] = "END"
        shared_state["raw_data"] = [winner, '2', '1'] 
        shared_state["last_update"] = time.time()
        time.sleep(6)

# ==========================================
#   UART WORKER (REAL CONNECTION)
# ==========================================
def serial_worker():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
            print(f"[SYSTEM] Link Established: {SERIAL_PORT}")
            shared_state["connected"] = True
            
            while True:
                if ser.in_waiting:
                    try:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        # Validate Protocol
                        if line.startswith('$') and line.endswith('*'):
                            parts = line[1:-1].split(',')
                            shared_state["scene"] = parts[0]
                            shared_state["raw_data"] = parts[1:]
                            shared_state["last_update"] = time.time()
                    except: pass
                else:
                    time.sleep(0.005) # Prevent CPU hogging
        except:
            shared_state["connected"] = False
            time.sleep(1) # Retry logic