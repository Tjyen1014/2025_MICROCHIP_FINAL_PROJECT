import pygame
import csv
import os
import random
import math
import time
from config import *

# ==========================================
#   DATA MANAGER
# ==========================================
class DataManager:
    """
    Handles data persistence. Saves game results to a CSV file.
    """
    def __init__(self, p1_name="PLAYER 1", p2_name="PLAYER 2"):
        self.p1_name = p1_name
        self.p2_name = p2_name
        self.filename = "game_history.csv"
        self._init_file()

    def _init_file(self):
        """Creates the CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Winner", "P1_Name", "P2_Name", "P1_Score", "P2_Score"])
            except IOError as e:
                print(f"[ERR] Failed to init CSV: {e}")

    def save_game(self, winner_code, s1, s2):
        """Appends a new game record to the CSV."""
        winner_name = "DRAW"
        if winner_code == '1': winner_name = self.p1_name
        elif winner_code == '2': winner_name = self.p2_name
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.filename, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, winner_name, self.p1_name, self.p2_name, s1, s2])
            print(f"[DATA] Game saved. Winner: {winner_name}")
        except IOError as e:
            print(f"[ERR] Failed to save game: {e}")

# ==========================================
#   SOUND MANAGER
# ==========================================
class SoundManager:
    """
    Handles audio playback. Implements edge-detection to prevent
    the 'machine gun effect' (playing sound every frame).
    """
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.load_assets()
        
        # State trackers for edge detection
        self.last_cursor = -1
        self.last_scene = "WAITING"
        self.last_packet_time = 0
        self.last_p1_state = -1
        self.last_p2_state = -1
        self.last_p1_ready = '0'
        self.last_p2_ready = '0'
        self.last_board = ['0'] * 9 
        
        # Start BGM
        if os.path.exists('assets/bgm.mp3'):
            try:
                pygame.mixer.music.load('assets/bgm.mp3')
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1) # Loop forever
                print("[AUDIO] BGM Started")
            except Exception: pass

    def load_assets(self):
        """Loads WAV/MP3 files into memory."""
        files = {
            'hint':   'assets/hint.mp3',
            'button': 'assets/button.mp3',
            'move':   'assets/move.mp3',
            'place':  'assets/place.mp3',
            'hit':    'assets/hit.mp3',
            'miss':   'assets/miss.mp3',
            'win':    'assets/win.mp3'
        }
        for name, path in files.items():
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    self.sounds[name].set_volume(0.5)
                except: print(f"[WARN] Failed to load {path}")
            else:
                print(f"[WARN] Sound missing: {path}")

    def play(self, name):
        """Plays a sound effect if available."""
        if name in self.sounds:
            self.sounds[name].play()

    def update(self, scene, data, last_ts):
        """
        Called every frame to check for state changes and trigger sounds.
        """
        is_new_packet = (last_ts != self.last_packet_time)
        self.last_packet_time = last_ts
        
        # Scene Transition Sound
        if scene == "HINT" and self.last_scene != "HINT":
            self.play('hint')
        
        # HINT: Ready Button Press
        if scene == "HINT" and len(data) > 2:
            if (data[1] == '1' and self.last_p1_ready == '0') or \
               (data[2] == '1' and self.last_p2_ready == '0'):
                self.play('button')
            self.last_p1_ready, self.last_p2_ready = data[1], data[2]

        # TTT: Cursor Move & Place Piece
        if scene == "TTT" and len(data) > 11:
            try:
                # 1. Cursor Movement
                cur = int(data[11])
                if data[10] == '0' and cur != self.last_cursor and cur != -1:
                    self.play('move')
                self.last_cursor = cur
                
                # 2. Place Piece Logic
                current_board = data[0:9]
                if current_board != self.last_board:
                    if not (all(x == '0' for x in current_board) and self.last_scene != "TTT"):
                        self.play('place')
                self.last_board = current_board

            except: pass
            
        # REACT: State Change (Rolling -> Locked)
        elif scene == "REACT" and len(data) > 8:
            # P1 State Change
            if (self.last_p1_state == '0' and data[7] == '1') or \
               (self.last_p1_state == '1' and data[7] == '2'):
                self.play('button')
            # P2 State Change
            if (self.last_p2_state == '0' and data[8] == '1') or \
               (self.last_p2_state == '1' and data[8] == '2'):
                self.play('button')
            self.last_p1_state, self.last_p2_state = data[7], data[8]

        # WAM: Hit/Miss Events (Only on new packet)
        elif scene == "WAM" and len(data) > 5 and is_new_packet:
            if data[3] == '1': self.play('hit')
            elif data[4] == '1': self.play('miss')

        # END: Win Sound
        if scene == "END" and self.last_scene != "END":
            self.play('win')
            
        self.last_scene = scene

# ==========================================
#   VISUAL EFFECTS (ULTIMATE CLEAN v2)
# ==========================================
class BackgroundEffect:
    """
    Manages background animations:
    - Breathing Sun with Atmosphere
    - 3D Perspective Grid with Horizon Fog
    - Starfield & Shooting Stars
    """
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.particles = []
        self.shooting_stars = []
        
        # Create starfield
        for _ in range(40):
            self.particles.append({
                'x': random.randint(0, width),
                'y': random.randint(0, height // 2),
                'speed': random.uniform(0.1, 0.5),
                'size': random.randint(1, 2)
            })

    def update(self):
        """Updates physics for all background elements."""
        # 1. Update Stars
        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < 0:
                p['y'] = self.h // 2
                p['x'] = random.randint(0, self.w)
        
        # 2. Spawn Shooting Stars
        if random.random() < 0.02:
            self.shooting_stars.append({
                'x': random.randint(0, self.w),
                'y': random.randint(0, self.h // 3),
                'len': random.randint(20, 50),
                'speed': random.randint(15, 25),
                'angle': 0.8
            })
            
        # 3. Move Shooting Stars
        for s in self.shooting_stars:
            s['x'] += s['speed']
            s['y'] += s['speed'] * 0.6
            
        self.shooting_stars = [s for s in self.shooting_stars if s['x'] < self.w and s['y'] < self.h // 2]

    def draw(self, surface):
        """Renders the atmospheric Synthwave scene."""
        surface.fill(COLOR_BG)
        
        horizon_y = self.h // 2
        center_x = self.w // 2
        time_sec = pygame.time.get_ticks() / 1000.0

        # --- 1. SYNTHWAVE SUN (Pulsing) ---
        # Breathing effect
        pulse = math.sin(time_sec * 2) * 3
        sun_radius = 130 + int(pulse)
        sun_center_y = horizon_y - 20
        
        # A. Sun Back Glow (Atmosphere)
        glow_radius = sun_radius + 40
        glow_surf = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        # Draw soft glow layers
        for i in range(20):
            alpha = max(0, 30 - i*2)
            rad = sun_radius + i*2
            pygame.draw.circle(glow_surf, (255, 0, 128, alpha), (glow_radius, glow_radius), rad)
        surface.blit(glow_surf, (center_x - glow_radius, sun_center_y - glow_radius))

        # B. Sun Body Gradient
        for r in range(sun_radius, 0, -2):
            ratio = r / sun_radius
            r_col, g_col, b_col = 255, int(200 * ratio), int(100 * (1 - ratio))
            pygame.draw.circle(surface, (r_col, g_col, b_col), (center_x, sun_center_y), r)
            
        # C. Sun Blinds (Stripes)
        blind_offset = (time_sec * 25) % 20
        for y in range(sun_center_y - sun_radius, sun_center_y + sun_radius, 12):
            stripe_y = y + blind_offset
            # Clip to sun bounds (approx)
            if stripe_y > sun_center_y + sun_radius: continue
            if stripe_y < sun_center_y - sun_radius: continue
            # Only draw on lower half
            if stripe_y > sun_center_y - 40:
                h = max(2, int((stripe_y - (sun_center_y-40)) / 8))
                pygame.draw.rect(surface, COLOR_BG, (center_x - sun_radius, stripe_y, sun_radius*2, h))

        # --- 2. STARS ---
        for p in self.particles:
            alpha = random.randint(100, 255)
            col = (alpha, alpha, alpha)
            pygame.draw.circle(surface, col, (int(p['x']), int(p['y'])), p['size'])

        # --- 3. PERSPECTIVE GRID (FLOOR) ---
        # Floor Background
        floor_surf = pygame.Surface((self.w, self.h - horizon_y))
        floor_surf.set_alpha(220)
        floor_surf.fill((15, 5, 25)) 
        surface.blit(floor_surf, (0, horizon_y))
        
        # Sun Reflection
        reflect_surf = pygame.Surface((sun_radius*2, sun_radius), pygame.SRCALPHA)
        pygame.draw.ellipse(reflect_surf, (255, 100, 50, 40), (0, 0, sun_radius*2, sun_radius))
        surface.blit(reflect_surf, (center_x - sun_radius, horizon_y))

        # Vertical Lines
        for i in range(-12, 13):
            base_x = center_x + i * 180 
            # Fade vertical lines near horizon for depth
            pygame.draw.line(surface, (0, 70, 90), (center_x + i*10, horizon_y), (base_x, self.h), 1)

        # Horizontal Lines
        speed = 0.8
        scroll_offset = (time_sec * speed) % 1.0
        num_lines = 12
        for i in range(num_lines):
            normalized_pos = (i + scroll_offset) / num_lines
            perspective_y = normalized_pos * normalized_pos
            y = horizon_y + int(perspective_y * (self.h - horizon_y))
            val = int(normalized_pos * 255)
            line_col = (0, val, val)
            if y < self.h:
                pygame.draw.line(surface, line_col, (0, y), (self.w, y), 2 if normalized_pos > 0.8 else 1)

        # --- 4. EFFECTS OVERLAY ---
        # Shooting Stars
        for s in self.shooting_stars:
            end_x = s['x'] - s['len']
            end_y = s['y'] - (s['len'] * 0.6)
            pygame.draw.line(surface, (200, 255, 255), (s['x'], s['y']), (end_x, end_y), 2)

        # Horizon Haze (Fog)
        fog_surf = pygame.Surface((self.w, 100), pygame.SRCALPHA)
        for i in range(100):
            # Gradient alpha: 0 (top) -> 100 (middle) -> 0 (bottom)
            alpha = 100 - abs(i - 50) * 2
            pygame.draw.line(fog_surf, (50, 0, 100, alpha), (0, i), (self.w, i))
        surface.blit(fog_surf, (0, horizon_y - 50))

        # Horizon Glow Line
        pygame.draw.line(surface, (255, 0, 128), (0, horizon_y), (self.w, horizon_y), 3) 

        # Vignette
        pygame.draw.rect(surface, (0, 0, 0), (0, 0, self.w, self.h), 50)