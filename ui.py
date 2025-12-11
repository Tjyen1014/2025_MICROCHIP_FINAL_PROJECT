import pygame
import serial
import threading
import sys
import time
import random
import math

# ==========================================
#   CONFIG & SETTINGS
# ==========================================
SERIAL_PORT = 'COM3'   
BAUD_RATE = 9600
WIDTH, HEIGHT = 1024, 768
FPS = 60

# ★★★ SIMULATION SWITCH ★★★
USE_SIMULATION = True  

# --- Color Palette ---
COLOR_BG = (5, 5, 10)           
COLOR_GRID = (0, 60, 60)        
COLOR_GLOW = (0, 255, 255)      
COLOR_ACCENT = (255, 0, 128)    
COLOR_TEXT = (220, 255, 255)    
COLOR_INFO = (100, 200, 255)    
COLOR_P1 = (0, 255, 128)        
COLOR_P2 = (255, 128, 0)        
COLOR_DANGER = (255, 50, 50)    
COLOR_CURSOR = (255, 255, 0)    
COLOR_MOLE_CORE = (255, 50, 50) 
COLOR_MOLE_GLOW = (255, 100, 0) 
COLOR_DIM = (60, 60, 60)        

# ==========================================
#   SHARED STATE
# ==========================================
shared_state = {
    "connected": False,
    "scene": "WAITING",
    "raw_data": [],
    "last_update": 0
}

# ==========================================
#   VISUAL EFFECTS SYSTEM
# ==========================================
class BackgroundEffect:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.offset_y = 0
        self.particles = []
        for _ in range(50): self.particles.append(self.create_particle())

    def create_particle(self):
        return {
            'x': random.randint(0, self.width),
            'y': random.randint(0, self.height),
            'speed': random.uniform(0.5, 2.0),
            'size': random.randint(2, 4),
            'alpha': random.randint(50, 150) 
        }

    def update(self):
        self.offset_y = (self.offset_y + 0.5) % 40
        for p in self.particles:
            p['y'] -= p['speed'] 
            if p['y'] < 0:
                p['y'] = self.height
                p['x'] = random.randint(0, self.width)

    def draw(self, surface):
        surface.fill(COLOR_BG)
        pulse = (math.sin(pygame.time.get_ticks() * 0.002) + 1) * 0.5 * 50 + 20 
        grid_color = (0, int(pulse), int(pulse)) 
        for x in range(0, self.width, 40): pygame.draw.line(surface, grid_color, (x, 0), (x, self.height), 1)
        for y in range(0, self.height, 40):
            dy = (y + self.offset_y) % self.height
            pygame.draw.line(surface, grid_color, (0, dy), (self.width, dy), 1)
        for p in self.particles:
            s = pygame.Surface((p['size'], p['size'])); s.set_alpha(p['alpha']); s.fill(COLOR_GLOW)
            surface.blit(s, (p['x'], p['y']))
        pygame.draw.rect(surface, (0,0,0), (0,0,self.width,self.height), 50)

bg_effect = None 




# ==========================================
#   SIMULATION WORKER (FULL SCENARIO MOCK)
# ==========================================
def simulation_worker():
    """
    Simulates a comprehensive game session covering all edge cases.
    - TTT: Cursor movement, strategic placement, win condition.
    - REACT: Waiting, Rolling, Locking, Winner calc.
    - WAM: Hits, Misses (Wrong Input), Timeouts (No Input), Turn switching.
    """
    print("[SIM] Starting Full Scenario Simulation ...")
    time.sleep(1)
    
    shared_state["scene"] = "START"
    shared_state["connected"] = True
    time.sleep(2)
    
    while True:
        # ==========================================
        # SCENARIO 1: TIC-TAC-TOE
        # ==========================================
        shared_state["scene"] = "HINT"
        # 1. Wait for P1
        shared_state["raw_data"] = ['1', '0', '0']
        time.sleep(1.0)
        # 2. P1 Ready, Wait for P2
        shared_state["raw_data"] = ['1', '1', '0']
        time.sleep(0.5)
        # 3. Both Ready -> Go
        shared_state["raw_data"] = ['1', '1', '1']
        time.sleep(1.0)

        shared_state["scene"] = "TTT"
        board = [0] * 9
        # Scripted Match: P1 (O) vs P2 (X)
        # Sequence: P1(4 center) -> P2(0 top-left) -> P1(3 mid-left) -> P2(5 mid-right) -> P1(2 top-right) -> P2(1 top-mid) -> P1(6 bot-left WIN)
        moves = [4, 0, 3, 5, 2, 1, 6] 
        current_p = 1
        
        for move in moves:
            # A. Cursor Wandering (Simulate thinking)
            start_cursor = random.randint(0, 8)
            for _ in range(5): 
                sim_cursor = random.randint(0, 8)
                # Protocol: [B0..B8, CurP, Win, Cursor]
                data = [str(x) for x in board] + [str(current_p), '0', str(sim_cursor)]
                shared_state["raw_data"] = data
                time.sleep(0.1) # Fast movement
            
            # B. Cursor Lock on Target
            data = [str(x) for x in board] + [str(current_p), '0', str(move)]
            shared_state["raw_data"] = data
            time.sleep(0.5) # Hesitation before press

            # C. Move Executed
            board[move] = current_p
            next_p = 2 if current_p == 1 else 1
            data = [str(x) for x in board] + [str(next_p), '0', str(move)]
            shared_state["raw_data"] = data
            
            current_p = next_p
            time.sleep(0.5) # Post-move pause
        
        # D. Winner Announcement
        # P1 connects 3 (indices 2, 4, 6 diagonal? No, indices 0,3,6 vertical logic depending on prev moves. 
        # Actually in this script: 4, 0, 3, 5, 2, 1, 6.
        # P1 has: 4, 3, 2, 6. (2,4,6 is diagonal!) -> P1 Wins.
        data = [str(x) for x in board] + ['2', '1', '6'] 
        shared_state["raw_data"] = data
        time.sleep(4)

        # ==========================================
        # SCENARIO 2: REACTION GAME
        # ==========================================
        shared_state["scene"] = "HINT"
        shared_state["raw_data"] = ['2', '0', '0'] # Reset readiness
        time.sleep(1)
        shared_state["raw_data"] = ['2', '1', '1'] # Fast ready
        time.sleep(1)

        shared_state["scene"] = "REACT"
        target = 50
        
        # Phase 0: Initial State
        shared_state["raw_data"] = ['50', '0', '0', '-1', '-1', '-1', '0', '0', '0']
        time.sleep(1.5)

        # Phase 1: P1 Rolling
        # Protocol: [Target, D1, D2, R1, R2, Win, Time, S1, S2]
        for i in range(30):
            d1 = random.randint(0, 99)
            data = [str(target), str(d1), '0', '-1', '-1', '-1', '0', '1', '0']
            shared_state["raw_data"] = data
            time.sleep(0.05)
            
        # Phase 2: P1 Locked (Result: 48, Diff: 2)
        p1_final = 48
        data = [str(target), str(p1_final), '0', str(p1_final), '-1', '-1', '0', '2', '0']
        shared_state["raw_data"] = data
        time.sleep(1.5) 
        
        # Phase 3: P2 Start Prompt
        # (State remains same, handled by UI logic to show 'PRESS START')
        time.sleep(1.0)

        # Phase 4: P2 Rolling
        for i in range(30):
            d2 = random.randint(0, 99)
            data = [str(target), str(p1_final), str(d2), str(p1_final), '-1', '-1', '0', '2', '1']
            shared_state["raw_data"] = data
            time.sleep(0.05)
            
        # Phase 5: P2 Locked & Win (Result: 55, Diff: 5) -> P1 Wins
        p2_final = 55
        data = [str(target), str(p1_final), str(p2_final), str(p1_final), str(p2_final), '1', '0', '2', '2']
        shared_state["raw_data"] = data
        time.sleep(4)

        # ==========================================
        # SCENARIO 3: WHAC-A-MOLE (COMPLEX)
        # ==========================================
        shared_state["scene"] = "HINT"
        shared_state["raw_data"] = ['3', '1', '1']
        time.sleep(3) # Read instructions

        shared_state["scene"] = "WAM"
        
        score1, score2 = 0, 0
        moles = ['0'] * 9
        
        # === ROUND 1: PLAYER 1 (30s Simulation) ===
        # P1State=1, P2State=0
        for t in range(30000, 0, -1000):
            hit_flag = '0'
            miss_flag = '0'
            seconds_left = t / 1000.0
            
            # Logic: Spawn mole every 2 sec
            if t % 2000 == 0: 
                moles = ['0']*9
                moles[random.randint(0,8)] = '1'
            
            # Logic: 1 sec after spawn, decide fate
            if t % 2000 == 1000:
                mole_idx = -1
                if '1' in moles: mole_idx = moles.index('1')
                
                if mole_idx != -1:
                    # Case A: Perfect Hit (First 20s)
                    if seconds_left > 10:
                        moles[mole_idx] = '0'
                        score1 += 10
                        hit_flag = '1'
                    # Case B: Miss/Wrong Input (Next 5s)
                    elif seconds_left > 5:
                        miss_flag = '1' # Mole stays up, but miss event fires
                    # Case C: Timeout (Last 5s)
                    else:
                        moles[mole_idx] = '0' # Disappears naturally
                        miss_flag = '1' # Count as miss

            # Protocol: [S1, S2, In, Hit, Miss, Time, Win, P1St, P2St, M0..M8]
            data = [str(score1), str(score2), 'N', hit_flag, miss_flag, str(t), '-1', '1', '0'] + moles
            shared_state["raw_data"] = data
            time.sleep(0.1)

        # === INTERMISSION ===
        # P1State=2, P2State=0
        for _ in range(20): 
            data = [str(score1), str(score2), 'N', '0', '0', '60000', '-1', '2', '0'] + ['0']*9
            shared_state["raw_data"] = data
            time.sleep(0.1)

        # === ROUND 2: PLAYER 2 (30s Simulation) ===
        # P1State=2, P2State=1
        for t in range(30000, 0, -1000):
            hit_flag = '0'
            miss_flag = '0'
            seconds_left = t / 1000.0
            
            if t % 2000 == 0: 
                moles = ['0']*9
                moles[random.randint(0,8)] = '1'
            
            if t % 2000 == 1000: 
                mole_idx = -1
                if '1' in moles: mole_idx = moles.index('1')
                
                if mole_idx != -1:
                    # P2 is surprisingly good
                    moles[mole_idx] = '0'
                    score2 += 15 
                    hit_flag = '1'
            
            data = [str(score1), str(score2), 'N', hit_flag, miss_flag, str(t), '-1', '2', '1'] + moles
            shared_state["raw_data"] = data
            time.sleep(0.1)

        # === GAME OVER ===
        winner = '2' if score2 > score1 else '1'
        shared_state["scene"] = "END"
        # Protocol: [Winner, P1_Wins, P2_Wins]
        shared_state["raw_data"] = [winner, '2', '1'] 
        time.sleep(6)





# ==========================================
#   UART WORKER
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
                        if line.startswith('$') and line.endswith('*'):
                            parts = line[1:-1].split(',')
                            shared_state["scene"] = parts[0]
                            shared_state["raw_data"] = parts[1:]
                            shared_state["last_update"] = time.time()
                    except: pass
                else: time.sleep(0.005)
        except:
            shared_state["connected"] = False
            time.sleep(1)




# ==========================================
#   GRAPHICS ENGINE
# ==========================================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PIC-18F CONTROL SYSTEM // CLASSIFIED")
clock = pygame.time.Clock()

try:
    FONT_MAIN = pygame.font.SysFont("consolas", 28, bold=True)
    FONT_BIG = pygame.font.SysFont("consolas", 60, bold=True)
    FONT_HUGE = pygame.font.SysFont("consolas", 100, bold=True)
    FONT_SMALL = pygame.font.SysFont("consolas", 18)
except:
    FONT_MAIN = pygame.font.SysFont(None, 28)
    FONT_BIG = pygame.font.SysFont(None, 60)
    FONT_HUGE = pygame.font.SysFont(None, 100)
    FONT_SMALL = pygame.font.SysFont(None, 20)



def draw_tech_border(surface, rect, color, thickness=2):
    x, y, w, h = rect
    cut = 20
    points = [(x+cut,y), (x+w-cut,y), (x+w,y+cut), (x+w,y+h-cut), (x+w-cut,y+h), (x+cut,y+h), (x,y+h-cut), (x,y+cut)]
    pygame.draw.polygon(surface, color, points, thickness)
    pygame.draw.line(surface, color, (x+cut, y+h+5), (x+w-cut, y+h+5), 1)



def draw_text_center(surface, text, font, color, center_pos):
    t = font.render(str(text), True, color)
    r = t.get_rect(center=center_pos)
    s = font.render(str(text), True, (0,0,0))
    surface.blit(s, (r.x+2, r.y+2))
    surface.blit(t, r)



# --- SCENES ---
def scene_hint(data):
    if len(data)<3: return
    game_id = data[0]
    INSTRUCTIONS = {
        '1': ["MISSION: CONNECT 3 SYMBOLS", "GUIDE: ROTATE Varieble Resistor TO AIM, PRESS BTN TO FIRE"],
        '2': ["MISSION: TEMPORAL LOCK", "GUIDE: STOP THE COUNTER CLOSE TO TARGET. P1 FIRST."],
        '3': ["MISSION: NEUTRALIZE MOLES", "GUIDE: TURN-BASED. HIT THE BUTTON."]
    }
    title = {'1': "01: TIC-TAC-TOE", '2': "02: PRECISION TEST", '3': "03: WHAC-A-MOLE"}.get(game_id, "UNKNOWN")
    
    draw_tech_border(screen, (WIDTH//2-300, 60, 600, 80), COLOR_ACCENT, 3)
    draw_text_center(screen, title, FONT_BIG, COLOR_TEXT, (WIDTH//2, 100))
    lines = INSTRUCTIONS.get(game_id, ["", ""])
    draw_text_center(screen, lines[0], FONT_MAIN, COLOR_INFO, (WIDTH//2, 180))
    draw_text_center(screen, lines[1], FONT_MAIN, (150, 255, 150), (WIDTH//2, 220))
    
    c1 = COLOR_P1 if data[1]=='1' else COLOR_DIM
    draw_tech_border(screen, (150, 350, 300, 200), c1, 3)
    draw_text_center(screen, "PLAYER 1", FONT_BIG, c1, (300, 410))
    draw_text_center(screen, "READY" if data[1]=='1' else "WAITING", FONT_MAIN, c1, (300, 470))
    c2 = COLOR_P2 if data[2]=='1' else COLOR_DIM
    draw_tech_border(screen, (WIDTH-450, 350, 300, 200), c2, 3)
    draw_text_center(screen, "PLAYER 2", FONT_BIG, c2, (WIDTH-300, 410))
    draw_text_center(screen, "READY" if data[2]=='1' else "WAITING", FONT_MAIN, c2, (WIDTH-300, 470))



def scene_ttt(data):
    if len(data) < 11: return
    bd, cp, win = data[0:9], data[9], data[10]
    cursor = int(data[11]) if len(data) > 11 else -1
    info, col = f"TURN: P{cp}", COLOR_GLOW
    if win=='1': info, col = "WINNER: PLAYER 1", COLOR_P1
    elif win=='2': info, col = "WINNER: PLAYER 2", COLOR_P2
    elif win=='3': info, col = "DRAW", (255,255,0)
    
    draw_text_center(screen, info, FONT_BIG, col, (WIDTH//2, 80))
    sz, sx, sy, cs = 450, (WIDTH-450)//2, 200, 150
    for i in range(1,3):
        pygame.draw.line(screen, COLOR_GRID, (sx+i*cs, sy), (sx+i*cs, sy+sz), 5)
        pygame.draw.line(screen, COLOR_GRID, (sx, sy+i*cs), (sx+sz, sy+i*cs), 5)
    for i in range(9):
        cx, cy = sx+(i%3)*cs+cs//2, sy+(i//3)*cs+cs//2
        if i==cursor and win=='0':
            blink = (pygame.time.get_ticks() // 200) % 2
            cc = COLOR_CURSOR if blink else (100, 100, 0)
            draw_tech_border(screen, (cx-65, cy-65, 130, 130), cc, 4)
        if bd[i]=='1':
            pygame.draw.circle(screen, COLOR_P1, (cx,cy), 60, 5); pygame.draw.circle(screen, (0,100,50), (cx,cy), 65, 2)
        elif bd[i]=='2':
            o=50; pygame.draw.line(screen, COLOR_P2, (cx-o,cy-o), (cx+o,cy+o), 8); pygame.draw.line(screen, COLOR_P2, (cx+o,cy-o), (cx-o,cy+o), 8)



def scene_react(data):
    if len(data)<9: return
    tgt, p1v, p2v, p1s, p2s = data[0], data[1], data[2], data[7], data[8]
    draw_tech_border(screen, (WIDTH//2-200, 100, 400, 200), COLOR_ACCENT, 4)
    draw_text_center(screen, "TARGET", FONT_MAIN, COLOR_ACCENT, (WIDTH//2, 140))
    draw_text_center(screen, tgt, FONT_HUGE, COLOR_TEXT, (WIDTH//2, 210))
    
    c1, st1 = COLOR_DIM, "WAITING"
    if p1s=='0' and p2s=='0': c1, st1 = COLOR_ACCENT, "PRESS START"
    elif p1s=='1': c1, st1 = COLOR_GLOW, "ROLLING..."
    elif p1s=='2': c1, st1 = COLOR_P1, "LOCKED"
    
    c2, st2 = COLOR_DIM, "WAITING"
    if p2s=='0' and p1s=='2': c2, st2 = COLOR_ACCENT, "PRESS START"
    elif p2s=='1': c2, st2 = COLOR_GLOW, "ROLLING..."
    elif p2s=='2': c2, st2 = COLOR_P2, "LOCKED"

    draw_tech_border(screen, (100, 350, 300, 250), c1)
    draw_text_center(screen, "PLAYER 1", FONT_BIG, c1, (250, 390))
    draw_text_center(screen, st1, FONT_MAIN, (200,200,200), (250, 440))
    draw_text_center(screen, p1v, FONT_HUGE, (255,255,255), (250, 520))
    
    draw_tech_border(screen, (WIDTH-400, 350, 300, 250), c2)
    draw_text_center(screen, "PLAYER 2", FONT_BIG, c2, (WIDTH-250, 390))
    draw_text_center(screen, st2, FONT_MAIN, (200,200,200), (WIDTH-250, 440))
    draw_text_center(screen, p2v, FONT_HUGE, (255,255,255), (WIDTH-250, 520))



def scene_wam(data):
    if len(data) < 18: return
    s1, s2, inp, tm = data[0], data[1], data[2], data[5]
    hit, miss = data[3], data[4]
    p1s, p2s = data[7], data[8]
    moles = data[9:18]
    
    col_p1 = COLOR_P1 if p1s == '1' else COLOR_DIM
    col_p2 = COLOR_P2 if p2s == '1' else COLOR_DIM
    pygame.draw.line(screen, COLOR_GLOW, (0, 80), (WIDTH, 80), 2)
    draw_text_center(screen, f"P1: {s1}", FONT_BIG, col_p1, (150, 40))
    draw_text_center(screen, f"P2: {s2}", FONT_BIG, col_p2, (WIDTH-150, 40))
    
    status_msg = "INTERMISSION"
    if p1s == '0' and p2s == '0': status_msg = "PLAYER 1: PRESS START"
    elif p1s == '1': status_msg = "PLAYER 1 PLAYING..."
    elif p1s == '2' and p2s == '0': status_msg = "PLAYER 2: PRESS START"
    elif p2s == '1': status_msg = "PLAYER 2 PLAYING..."
    elif p2s == '2': status_msg = "GAME OVER"
    draw_text_center(screen, status_msg, FONT_MAIN, COLOR_INFO, (WIDTH//2, 120))

    if hit == '1':
        draw_text_center(screen, "PERFECT HIT!", FONT_BIG, (0, 255, 0), (WIDTH//2, 220))
    elif miss == '1':
        draw_text_center(screen, "MISS!", FONT_BIG, (255, 0, 0), (WIDTH//2, 220))

    try: 
        max_ticks = 60000.0; cur = float(tm); progress = cur / max_ticks; sec = cur / 10000.0
    except: progress, sec = 0, 0.0
    bw = 400
    pygame.draw.rect(screen, (50,50,50), (WIDTH//2-bw//2, 30, bw, 20))
    tc = COLOR_P1 if sec>10 else COLOR_DANGER
    pygame.draw.rect(screen, tc, (WIDTH//2-bw//2, 30, int(bw*progress), 20))
    draw_text_center(screen, f"{sec:.1f}s", FONT_MAIN, (255,255,255), (WIDTH//2, 65))

    sx, sy, gap = (WIDTH-400)//2, 220, 140
    for i in range(9):
        cx, cy = sx+(i%3)*gap+70, sy+(i//3)*gap+70
        is_mole = (moles[i]=='1')
        pygame.draw.circle(screen, (30,40,50), (cx,cy), 60, 2)
        pygame.draw.line(screen, (30,40,50), (cx-70,cy), (cx-50,cy), 2)
        pygame.draw.line(screen, (30,40,50), (cx+50,cy), (cx+70,cy), 2)
        pygame.draw.line(screen, (30,40,50), (cx,cy-70), (cx,cy-50), 2)
        pygame.draw.line(screen, (30,40,50), (cx,cy+50), (cx,cy+70), 2)
        if is_mole:
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 5
            mc = COLOR_MOLE_CORE
            if p1s=='1': mc = COLOR_P1
            elif p2s=='1': mc = COLOR_P2
            pygame.draw.circle(screen, COLOR_MOLE_GLOW, (cx,cy), 45+pulse)
            pygame.draw.circle(screen, mc, (cx,cy), 35)
            pygame.draw.circle(screen, (255,255,255), (cx,cy), 15)
            pygame.draw.line(screen, (0,0,0), (cx-10,cy), (cx+10,cy), 2)
            pygame.draw.line(screen, (0,0,0), (cx,cy-10), (cx,cy+10), 2)
        else:
            pygame.draw.circle(screen, (15,20,25), (cx,cy), 20)
        draw_text_center(screen, str(i+1), FONT_SMALL, (100,100,100), (cx+50, cy+50))



def scene_end(data):
    if len(data)<3: return
    win, w1, w2 = data[0], data[1], data[2]
    draw_tech_border(screen, (100, 150, WIDTH-200, 400), (255,215,0), 5)
    title, champ, cc = "MISSION COMPLETE", "DRAW GAME", (200,200,200)
    if win=='1': champ, cc = "CHAMPION: PLAYER 1", COLOR_P1
    elif win=='2': champ, cc = "CHAMPION: PLAYER 2", COLOR_P2
    draw_text_center(screen, title, FONT_BIG, (255,255,255), (WIDTH//2, 220))
    draw_text_center(screen, champ, FONT_HUGE, cc, (WIDTH//2, 320))
    draw_text_center(screen, f"P1 WINS: {w1}  |  P2 WINS: {w2}", FONT_MAIN, COLOR_GLOW, (WIDTH//2, 450))



def scene_waiting():
    draw_text_center(screen, "SYSTEM INITIALIZING...", FONT_BIG, COLOR_GLOW, (WIDTH//2, HEIGHT//2-50))
    msg, col = f"CONNECTING TO {SERIAL_PORT}...", COLOR_DANGER
    if shared_state["connected"]:
        msg, col = "CONNECTION ESTABLISHED", COLOR_P1
        bw = (pygame.time.get_ticks()//5)%300
        pygame.draw.rect(screen, col, (WIDTH//2-150, HEIGHT//2+80, bw, 10))
    if USE_SIMULATION: msg, col = ":: SIMULATION MODE  ::", COLOR_ACCENT
    draw_text_center(screen, msg, FONT_MAIN, col, (WIDTH//2, HEIGHT//2+50))



def main():
    global bg_effect
    bg_effect = BackgroundEffect(WIDTH, HEIGHT)
    if USE_SIMULATION: t = threading.Thread(target=simulation_worker, daemon=True)
    else: t = threading.Thread(target=serial_worker, daemon=True)
    t.start()
    run = True
    while run:
        for e in pygame.event.get():
            if e.type==pygame.QUIT or (e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE): run=False
        bg_effect.update()
        bg_effect.draw(screen)
        sc, dt = shared_state["scene"], shared_state["raw_data"]
        
        if not shared_state["connected"]: scene_waiting()
        elif sc=="START" or sc=="WAITING": scene_waiting()
        elif sc=="HINT": scene_hint(dt)
        elif sc=="TTT": scene_ttt(dt)
        elif sc=="REACT": scene_react(dt)
        elif sc=="WAM": scene_wam(dt)
        elif sc=="END": scene_end(dt)
        
        for y in range(0, HEIGHT, 4): pygame.draw.line(screen, (0,0,0,50), (0,y), (WIDTH,y), 1)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit(); sys.exit()

if __name__=="__main__": main()