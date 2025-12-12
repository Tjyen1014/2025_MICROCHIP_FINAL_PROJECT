#include <stdlib.h> // for rand()
#include "whac_a_mole.h"

#define GAME_DURATION_SEC 60.0

static int active_mole = -1;
static int prev_player1_state = 0; 
static int prev_player2_state = 0; 
static long spawn_counter = 0;
static long stay_counter = 0;
static long spawn_interval_ticks = 0;
static long stay_time_ticks = 0;
static unsigned long last_tick = 0;

WHAC_A_MOLE_OUTPUT_TABLE WHAC_A_MOLE_UPDATE(WHAC_A_MOLE_OUTPUT_TABLE table) {
    unsigned long current_tick = table.tick100us; //now is Xsec
    unsigned long delta_ticks = current_tick - last_tick; //check does the time go?
    last_tick = current_tick; 

    //init
    table.HIT = 0;
    table.MISS = 0;
    table.NOT_HIT_NOT_MISS = 1;     

    spawn_interval_ticks = 3500; //0.35sec
    stay_time_ticks = 7500; //0.75sec

    //change 1~9 to 0~8
    int input_idx = -1;
    if (table.INPUT >= '1' && table.INPUT <= '9') {
        input_idx = table.INPUT - '1'; 
    }

    // Current Player Logic
    int *current_score = NULL; 
    int current_playing = 0; // 0:no, 1:P1, 2:P2

    //P1 init
    if (table.PLAYER1_STATE == 1 && prev_player1_state != 1) {
        
        table.SCORE_P1 = 0; 
        table.REMAINING_TIME = (long)(GAME_DURATION_SEC * 10000); //1sec/0.0001sec = 10000 ticks
        active_mole = -1;
        spawn_counter = 0;
        for(int j=0; j<9; j++) 
            table.WHAC_A_MOLE[j] = 0;
        srand(table.tick100us);
    }
    //P2 init
    if (table.PLAYER2_STATE == 1 && prev_player2_state != 1) {
        
        table.SCORE_P2 = 0; 
        table.REMAINING_TIME = (long)(GAME_DURATION_SEC * 10000);
        active_mole = -1;
        spawn_counter = 0;
        for(int j=0; j<9; j++) 
            table.WHAC_A_MOLE[j] = 0;
        srand(table.tick100us);
    }

    // set current player
    if (table.PLAYER1_STATE == 1) {

        current_playing = 1;
        current_score = &table.SCORE_P1; //point to P1 score
    } else if (table.PLAYER2_STATE == 1) {

        current_playing = 2;
        current_score = &table.SCORE_P2; //point to P2 score
    }


    if (current_playing != 0) {
        
        //count down
        if (table.REMAINING_TIME > 0) {
            table.REMAINING_TIME -= delta_ticks;
        } 

        // botton check
        if (input_idx != -1) {
            if (active_mole == input_idx) {
                // HIT!
                (*current_score) += 10; 
                table.HIT = 1;
                table.NOT_HIT_NOT_MISS = 0;
                table.WHAC_A_MOLE[input_idx] = 0;
                active_mole = -1;
                spawn_counter = 0;
            } else {
                // MISS!
                (*current_score) -= 5;  
                table.MISS = 1;
                table.NOT_HIT_NOT_MISS = 0;
            }
        }

        //spawn
        if (active_mole == -1) { //no mole
            spawn_counter += delta_ticks; //count to 0.35sec
            if (spawn_counter >= spawn_interval_ticks) {
                spawn_counter = 0; //reset
                active_mole = rand() % 9; 
                table.WHAC_A_MOLE[active_mole] = 1; 
                stay_counter = 0; //start to count how long it stay
            }
        } else { //has mole
            stay_counter += delta_ticks;//count to 0.75sec
            if (stay_counter >= stay_time_ticks) {
                // ESCAPE!
                (*current_score) -= 2; 
                table.MISS = 1; 
                table.NOT_HIT_NOT_MISS = 0;
                table.WHAC_A_MOLE[active_mole] = 0; 
                active_mole = -1;
                spawn_counter = 0;//start to count how long it until spawn
            }
        }
    }

    //no one play
    else {
         for(int j=0; j<9; j++) table.WHAC_A_MOLE[j] = 0;
         active_mole = -1;
    }

    prev_player1_state = table.PLAYER1_STATE;
    prev_player2_state = table.PLAYER2_STATE;
    table.INPUT = 0; 

    return table;
}


WHAC_A_MOLE_OUTPUT_TABLE WHAC_A_MOLE_UPDATE_WHO_WIN(WHAC_A_MOLE_OUTPUT_TABLE table) {
    
    //compare score
    if (table.SCORE_P1 > table.SCORE_P2) {
        table.WINNER = 1; // P1 win
    } 
    else if (table.SCORE_P1 < table.SCORE_P2) {
        table.WINNER = 2; // P2 win
    } 
    else if (table.SCORE_P1 == table.SCORE_P2) {
        table.WINNER = 0; // Draw
    }
    else {
        table.WINNER = -1;//error
    }

    return table;

}
