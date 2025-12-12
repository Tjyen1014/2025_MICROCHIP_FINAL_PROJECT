import pygame
import threading
import sys
import argparse
from config import *
from managers import BackgroundEffect, SoundManager, DataManager
from workers import serial_worker, simulation_worker
import scenes 

def main():
    # 1. Parse Command Line Arguments
    # Example: python main.py --p1 "Tony" --p2 "Steve" --sim
    parser = argparse.ArgumentParser()
    parser.add_argument("--p1", default="PLAYER 1", help="Name of Player 1")
    parser.add_argument("--p2", default="PLAYER 2", help="Name of Player 2")
    parser.add_argument("--sim", action="store_true", help="Force Simulation Mode")
    args = parser.parse_args()
    
    # 2. Initialize System
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("PIC-18F CONTROL SYSTEM")
    clock = pygame.time.Clock()
    
    # Initialize Managers
    bg_effect = BackgroundEffect(WIDTH, HEIGHT)
    sound_mgr = SoundManager()
    data_mgr = DataManager(args.p1, args.p2)
    
    # 3. Start Backend Thread
    # Priority: Command Line Arg > Config File
    is_sim_mode = args.sim or USE_SIMULATION
    
    if is_sim_mode:
        t = threading.Thread(target=simulation_worker, daemon=True)
    else:
        t = threading.Thread(target=serial_worker, daemon=True)
    t.start()
    
    # 4. Main Game Loop
    run = True
    while run:
        # Event Handling
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                run = False
        
        # Render Background
        bg_effect.update()
        bg_effect.draw(screen)
        
        # Get Current State
        sc = shared_state["scene"]
        dt = shared_state["raw_data"]
        
        # Update Sound Logic
        sound_mgr.update(sc, dt, shared_state["last_update"])
        
        # Handle Data Persistence on Game Over
        if sc == "END":
            # Pass data to manager to save (implement debounce logic if needed)
            pass 

        # Scene Routing (Dispatch to scenes.py)
        if not shared_state["connected"]: scenes.scene_waiting(screen)
        elif sc == "START" or sc == "WAITING": scenes.scene_waiting(screen)
        elif sc == "HINT": scenes.scene_hint(screen, dt)
        elif sc == "TTT": scenes.scene_ttt(screen, dt)
        elif sc == "REACT": scenes.scene_react(screen, dt)
        elif sc == "WAM": scenes.scene_wam(screen, dt)
        elif sc == "END": scenes.scene_end(screen, dt, data_mgr)
        
        # Scanlines Overlay
        for y in range(0, HEIGHT, 4): 
            pygame.draw.line(screen, (0,0,0,50), (0,y), (WIDTH,y), 1)
            
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()