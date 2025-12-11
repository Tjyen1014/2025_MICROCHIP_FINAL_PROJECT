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
# Serial Port Configuration
SERIAL_PORT = 'COM3'   
BAUD_RATE = 9600

# Window Size
WIDTH, HEIGHT = 1024, 768
FPS = 60

# SIMULATION SWITCH 
# True: Runs internal mock script 
# False: Connects to actual UART Hardware
USE_SIMULATION = True  

# --- Color Palette ---
COLOR_BG = (5, 5, 10)           # Deep Void Blue
COLOR_GRID = (0, 60, 60)        # Dim Cyan
COLOR_GLOW = (0, 255, 255)      # Cyan Neon
COLOR_ACCENT = (255, 0, 128)    # Magenta Neon
COLOR_TEXT = (220, 255, 255)    # Pale Cyan
COLOR_INFO = (100, 200, 255)    # Info Text
COLOR_P1 = (0, 255, 128)        # Player 1 Green
COLOR_P2 = (255, 128, 0)        # Player 2 Orange
COLOR_DANGER = (255, 50, 50)    # Critical Red
COLOR_CURSOR = (255, 255, 0)    # TTT Cursor Yellow
COLOR_MOLE_CORE = (255, 50, 50) # Mole Core Red
COLOR_MOLE_GLOW = (255, 100, 0) # Mole Outer Glow
COLOR_DIM = (60, 60, 60)        # Inactive Gray

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
    """
    Manages the 'Digital Atmosphere' background:
    - Breathing Grid
    - Floating Data Particles
    - CRT Vignette
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.offset_y = 0
        self.particles = []
        
        # Initialize floating particles
        for _ in range(50):
            self.particles.append(self.create_particle())

    def create_particle(self):
        """Generate random particle properties."""
        return {
            'x': random.randint(0, self.width),
            'y': random.randint(0, self.height),
            'speed': random.uniform(0.5, 2.0),
            'size': random.randint(2, 4),
            'alpha': random.randint(50, 150) 
        }

    def update(self):
        """Update animation state."""
        self.offset_y = (self.offset_y + 0.5) % 40
        for p in self.particles:
            p['y'] -= p['speed'] 
            if p['y'] < 0:
                p['y'] = self.height
                p['x'] = random.randint(0, self.width)

    def draw(self, surface):
        """Render the background layers."""
        surface.fill(COLOR_BG)
        
        # 1. Pulsing Grid
        pulse = (math.sin(pygame.time.get_ticks() * 0.002) + 1) * 0.5 * 50 + 20 
        grid_color = (0, int(pulse), int(pulse)) 
        
        # Vertical lines
        for x in range(0, self.width, 40):
            pygame.draw.line(surface, grid_color, (x, 0), (x, self.height), 1)
        # Horizontal lines (Scrolling)
        for y in range(0, self.height, 40):
            dy = (y + self.offset_y) % self.height
            pygame.draw.line(surface, grid_color, (0, dy), (self.width, dy), 1)

        # 2. Particles
        for p in self.particles:
            s = pygame.Surface((p['size'], p['size']))
            s.set_alpha(p['alpha'])
            s.fill(COLOR_GLOW)
            surface.blit(s, (p['x'], p['y']))

        # 3. Vignette (Dark Corners)
        pygame.draw.rect(surface, (0,0,0), (0,0,self.width,self.height), 50)

# Global reference
bg_effect = None 




# ==========================================
#   SIMULATION WORKER 
# ==========================================
def simulation_worker():
    """
    Simulates the firmware logic for UI testing.
    Includes full game cycles for TTT, Reaction, and Turn-Based WAM.
    """
    print("[SIM] Starting Simulation Mode...")
    time.sleep(1)
    
    shared_state["scene"] = "START"
    shared_state["connected"] = True
    time.sleep(2)
    
    while True:
        # ==========================================
        # STAGE 1: TIC-TAC-TOE
        # ==========================================
        shared_state["scene"] = "HINT"
        # Simulate Wait -> P1 Ready -> P2 Ready
        shared_state["raw_data"] = ['1', '0', '0']
        time.sleep(1.0)
        shared_state["raw_data"] = ['1', '1', '0'] # P1 Ready
        time.sleep(0.5)
        shared_state["raw_data"] = ['1', '1', '1'] # Both Ready
        time.sleep(1.0)

        shared_state["scene"] = "TTT"
        # Skip details for brevity, assume P1 wins
        shared_state["raw_data"] = ['1','2','1','2','1','2','1','2','1', '1', '1', '4']
        time.sleep(2)

        # ==========================================
        # STAGE 2: REACTION GAME
        # ==========================================
        shared_state["scene"] = "HINT"
        shared_state["raw_data"] = ['2', '1', '1']
        time.sleep(1)

        shared_state["scene"] = "REACT"
        target = 50
        
        # --- Phase 0: Waiting for P1 Start ---
        # S1=0, S2=0
        shared_state["raw_data"] = ['50', '0', '0', '-1', '-1', '-1', '0', '0', '0']
        time.sleep(2.0) # Player 1 hesitation

        # --- Phase 1: P1 Rolling ---
        for i in range(25):
            d1 = random.randint(0, 99)
            # S1=1 (Rolling), S2=0 (Wait)
            data = [str(target), str(d1), '0', '-1', '-1', '-1', '0', '1', '0']
            shared_state["raw_data"] = data
            time.sleep(0.05)
            
        # --- Phase 2: P1 Locked (Result: 48) ---
        p1_final = 48
        # S1=2 (Locked), S2=0 (Wait)
        data = [str(target), str(p1_final), '0', str(p1_final), '-1', '-1', '0', '2', '0']
        shared_state["raw_data"] = data
        time.sleep(1.0) 
        
        # --- Phase 3: Waiting for P2 Start ---
        # S1=2 (Locked), S2=0 (Wait)
        # UI should show "PRESS START" for P2
        time.sleep(2.0) # Player 2 hesitation

        # --- Phase 4: P2 Rolling ---
        for i in range(25):
            d2 = random.randint(0, 99)
            # S1=2 (Locked), S2=1 (Rolling)
            data = [str(target), str(p1_final), str(d2), str(p1_final), '-1', '-1', '0', '2', '1']
            shared_state["raw_data"] = data
            time.sleep(0.05)
            
        # --- Phase 5: P2 Locked & Win Calculation ---
        p2_final = 55
        data = [str(target), str(p1_final), str(p2_final), str(p1_final), str(p2_final), '1', '0', '2', '2']
        shared_state["raw_data"] = data
        time.sleep(3)

        # ==========================================
        # STAGE 3: WHAC-A-MOLE (Turn-Based Logic)
        # ==========================================
        shared_state["scene"] = "HINT"
        shared_state["raw_data"] = ['3', '1', '1']
        time.sleep(2) # Read instructions

        shared_state["scene"] = "WAM"
        
        score1, score2 = 0, 0
        hit_count, miss_count = 0, 0
        moles = ['0'] * 9
        
        # --- Round 1 Setup: Waiting for P1 ---
        # P1St=0, P2St=0
        shared_state["raw_data"] = ['0', '0', 'N', '0', '0', '60000', '-1', '0', '0'] + moles
        time.sleep(2.0) # Wait for P1 push

        # --- Round 1: Player 1 Playing (P1St=1) ---
        for t in range(30000, 0, -1000):
            if t % 2000 == 0: 
                moles = ['0']*9
                moles[random.randint(0,8)] = '1'
            if t % 2000 == 1000: 
                try: 
                    moles[moles.index('1')] = '0'
                    score1 += 10
                    hit_count += 1
                except: pass
            
            data = [str(score1), str(score2), 'N', str(hit_count), str(miss_count), str(t), '-1', '1', '0'] + moles
            shared_state["raw_data"] = data
            time.sleep(4)

        # --- Intermission: Waiting for P2 ---
        # P1St=2 (Done), P2St=0 (Wait)
        for _ in range(20): 
            data = [str(score1), str(score2), 'N', str(hit_count), str(miss_count), '60000', '-1', '2', '0'] + ['0']*9
            shared_state["raw_data"] = data
            time.sleep(0.1)

        # --- Round 2: Player 2 Playing (P2St=1) ---
        for t in range(30000, 0, -1000):
            if t % 2000 == 0: 
                moles = ['0']*9
                moles[random.randint(0,8)] = '1'
            if t % 2000 == 1000: 
                try: 
                    moles[moles.index('1')] = '0'
                    score2 += 15 # P2 is better
                    hit_count += 1
                except: pass
            
            data = [str(score1), str(score2), 'N', str(hit_count), str(miss_count), str(t), '-1', '2', '1'] + moles
            shared_state["raw_data"] = data
            time.sleep(0.1)

        # --- Game Over ---
        winner = '2' # P2 Won
        data = [str(score1), str(score2), 'N', str(hit_count), str(miss_count), '0', winner, '2', '2'] + ['0']*9
        shared_state["raw_data"] = data
        time.sleep(3)

        # --- FINAL END ---
        shared_state["scene"] = "END"
        shared_state["raw_data"] = [winner, '2', '1'] 
        time.sleep(5)

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

# --- Font Setup ---
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

# --- Drawing Helpers ---
def draw_tech_border(surface, rect, color, thickness=2):
    """Draws a box with cut corners."""
    x, y, w, h = rect
    cut = 20
    points = [(x+cut,y), (x+w-cut,y), (x+w,y+cut), (x+w,y+h-cut), (x+w-cut,y+h), (x+cut,y+h), (x,y+h-cut), (x,y+cut)]
    pygame.draw.polygon(surface, color, points, thickness)
    pygame.draw.line(surface, color, (x+cut, y+h+5), (x+w-cut, y+h+5), 1)

def draw_text_center(surface, text, font, color, center_pos):
    """Centers text with shadow."""
    t = font.render(str(text), True, color)
    r = t.get_rect(center=center_pos)
    s = font.render(str(text), True, (0,0,0))
    surface.blit(s, (r.x+2, r.y+2))
    surface.blit(t, r)




# ==========================================
#   SCENE RENDERERS
# ==========================================

def scene_hint(data):
    if len(data)<3: return
    game_id = data[0]
    INSTRUCTIONS = {
        '1': ["MISSION: CONNECT 3 SYMBOLS", "GUIDE: ROTATE KNOB TO AIM, PRESS BTN TO FIRE"],
        '2': ["MISSION: TEMPORAL LOCK", "GUIDE: STOP THE COUNTER CLOSE TO TARGET. P1 FIRST."],
        '3': ["MISSION: NEUTRALIZE MOLES", "GUIDE: TURN-BASED. HIT '1-9' ON KEYPAD."]
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
            pygame.draw.circle(screen, COLOR_P1, (cx,cy), 60, 5)
            pygame.draw.circle(screen, (0,100,50), (cx,cy), 65, 2)
        elif bd[i]=='2':
            o=50
            pygame.draw.line(screen, COLOR_P2, (cx-o,cy-o), (cx+o,cy+o), 8)
            pygame.draw.line(screen, COLOR_P2, (cx+o,cy-o), (cx-o,cy+o), 8)




def scene_react(data):
    if len(data)<9: return
    tgt, p1v, p2v, p1s, p2s = data[0], data[1], data[2], data[7], data[8]
    
    draw_tech_border(screen, (WIDTH//2-200, 100, 400, 200), COLOR_ACCENT, 4)
    draw_text_center(screen, "TARGET", FONT_MAIN, COLOR_ACCENT, (WIDTH//2, 140))
    draw_text_center(screen, tgt, FONT_HUGE, COLOR_TEXT, (WIDTH//2, 210))
    
    # Logic for P1 Display
    c1, st1 = COLOR_DIM, "WAITING"
    if p1s == '0': # Waiting for Start
        if p2s == '0': # If P2 also waiting, it implies P1's turn to start
             c1, st1 = COLOR_ACCENT, "PRESS START"
        # If P2 is running/done, P1 shouldn't happen (Logic error or P1 done)
        # But here logic implies P1 goes first.
    elif p1s == '1': c1, st1 = COLOR_GLOW, "ROLLING..."
    elif p1s == '2': c1, st1 = COLOR_P1, "LOCKED"
    
    # Logic for P2 Display
    c2, st2 = COLOR_DIM, "WAITING"
    if p2s == '0':
        if p1s == '2': # P1 is done, now P2's turn to start
            c2, st2 = COLOR_ACCENT, "PRESS START"
    elif p2s == '1': c2, st2 = COLOR_GLOW, "ROLLING..."
    elif p2s == '2': c2, st2 = COLOR_P2, "LOCKED"

    # Draw Panels
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
    p1s, p2s = data[7], data[8]
    moles = data[9:18]
    
    # Determine Active Player and Status Message
    status_msg = "INTERMISSION"
    if p1s == '0' and p2s == '0':
        status_msg = "PLAYER 1: PRESS START"
        # Highlight P1 box slightly to indicate urgency
    elif p1s == '1': 
        status_msg = "PLAYER 1 PLAYING..."
    elif p1s == '2' and p2s == '0':
        status_msg = "PLAYER 2: PRESS START"
    elif p2s == '1': 
        status_msg = "PLAYER 2 PLAYING..."
    elif p2s == '2': 
        status_msg = "GAME OVER"
        
    draw_text_center(screen, status_msg, FONT_MAIN, COLOR_INFO, (WIDTH//2, 120))

    # Score Headers (Blink if "Press Start")
    blink = (pygame.time.get_ticks() // 300) % 2
    
    c1 = COLOR_DIM
    if p1s == '1': c1 = COLOR_P1
    elif p1s == '0' and p2s == '0': c1 = COLOR_ACCENT if blink else COLOR_DIM # Blink P1
    elif p1s == '2': c1 = COLOR_DIM # Done
    
    c2 = COLOR_DIM
    if p2s == '1': c2 = COLOR_P2
    elif p1s == '2' and p2s == '0': c2 = COLOR_ACCENT if blink else COLOR_DIM # Blink P2
    
    pygame.draw.line(screen, COLOR_GLOW, (0, 80), (WIDTH, 80), 2)
    draw_text_center(screen, f"P1: {s1}", FONT_BIG, c1, (150, 40))
    draw_text_center(screen, f"P2: {s2}", FONT_BIG, c2, (WIDTH-150, 40))
    
    # Time Bar
    try: 
        max_ticks = 60000.0
        current_ticks = float(tm)
        progress = current_ticks / max_ticks
        sec = current_ticks / 10000.0
    except: progress, sec = 0, 0.0
    
    bw = 400
    pygame.draw.rect(screen, (50,50,50), (WIDTH//2-bw//2, 30, bw, 20))
    tc = COLOR_P1 if sec>10 else COLOR_DANGER
    pygame.draw.rect(screen, tc, (WIDTH//2-bw//2, 30, int(bw*progress), 20))
    draw_text_center(screen, f"{sec:.1f}s", FONT_MAIN, (255,255,255), (WIDTH//2, 65))

    # Grid & Moles
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
    if USE_SIMULATION: msg, col = ":: SIMULATION MODE (v1.4) ::", COLOR_ACCENT
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
        
        # Scanlines
        for y in range(0, HEIGHT, 4): pygame.draw.line(screen, (0,0,0,50), (0,y), (WIDTH,y), 1)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit(); sys.exit()

if __name__=="__main__": main()