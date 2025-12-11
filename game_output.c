#include <xc.h>
#include <stdio.h>
#include <string.h>
#include "shared_structs.h"  // Required for table definitions
#include "uart.h"            // Required for UART_Write_Text

// ==========================================
//  Helper Functions
// ==========================================

/**
 * Maps TTT internal logic values to Protocol values.
 * Internal Logic: -1 (Empty), 0 (Player 1), 1 (Player 2)
 * Protocol:        0 (Empty), 1 (Player 1), 2 (Player 2)
 */
int map_ttt_val(int logic_val) {
    if (logic_val == -1) return 0; // Empty
    if (logic_val == 0)  return 1; // Player 1
    if (logic_val == 1)  return 2; // Player 2
    return 0; // Default safety
}

// ==========================================
//  1. START_OUTPUT
//  Function: Indicates system boot.
//  Protocol: $START*
// ==========================================
void START_OUTPUT(void) {
    UART_Write_Text("$START*");
    UART_Write_Text("\r\n");
}

// ==========================================
//  2. HINT_OUTPUT
//  Function: Updates game stage and player readiness.
//  Protocol: $HINT,<Game_State>,<P1_Ready>,<P2_Ready>*
// ==========================================
void HINT_OUTPUT(HINT_OUTPUT_TABLE table) {
    char buffer[50];
    
    sprintf(buffer, "$HINT,%d,%d,%d*", 
            table.GAME_STATE, 
            table.P1_PREPARE, 
            table.P2_PREPARE);
            
    UART_Write_Text(buffer);
    UART_Write_Text("\r\n");
}

// ==========================================
//  3. TTT_OUTPUT (Updated v1.4)
//  Function: Updates board, winner, and cursor.
//  Protocol: $TTT,<B0>...<B8>,<CurPlayer>,<Winner>,<Cursor>*
//  Note: 'table.CURSOR' is already 0-8 (mapped by main logic).
// ==========================================
void TTT_OUTPUT(TTT_OUTPUT_TABLE table) {
    char buffer[100];
    
    // --- 1. Winner Logic Correction ---
    // In logic core, 'CURPLAYER' swaps immediately after a winning move.
    // So if DETWINNER is 1, the winner is actually the PREVIOUS player.
    int protocol_winner = 0; // 0: In Progress
    
    if (table.DETWINNER == 1) {
        if (table.CURPLAYER == 0) {
            protocol_winner = 2; // Current is P1 (0), so P2 (1) won
        } else {
            protocol_winner = 1; // Current is P2 (1), so P1 (0) won
        }
    } else {
        protocol_winner = 0;
    }

    // --- 2. Current Player Mapping ---
    // Logic: 0/1 -> Protocol: 1/2
    int protocol_cur_player = table.CURPLAYER + 1;

    int cursor_pos = table.CURSOR;

    // --- 4. Packet Generation ---
    sprintf(buffer, "$TTT,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d*",
            map_ttt_val(table.BOARD[0]), 
            map_ttt_val(table.BOARD[1]), 
            map_ttt_val(table.BOARD[2]),
            map_ttt_val(table.BOARD[3]), 
            map_ttt_val(table.BOARD[4]), 
            map_ttt_val(table.BOARD[5]),
            map_ttt_val(table.BOARD[6]), 
            map_ttt_val(table.BOARD[7]), 
            map_ttt_val(table.BOARD[8]),
            protocol_cur_player,
            protocol_winner,
            cursor_pos);
            
    UART_Write_Text(buffer);
    UART_Write_Text("\r\n");
}

// ==========================================
//  4. REACTION_OUTPUT
//  Function: Updates precision game state.
//  Protocol: $REACT,<Target>,<D1>,<D2>,<R1>,<R2>,<Win>,<Time>,<S1>,<S2>*
// ==========================================
void REACTION_OUTPUT(REACTION_OUTPUT_TABLE table) {
    char buffer[120];
    

    sprintf(buffer, "$REACT,%d,%d,%d,%d,%d,%d,%lu,%d,%d*",
            table.RANDOM_NUMBER,
            table.DISPLAY_NUMBER_1,
            table.DISPLAY_NUMBER_2,
            table.P1_RESULT,
            table.P2_RESULT,
            table.WINNER,
            table.tick100us,
            table.PLAYER1_STATE,
            table.PLAYER2_STATE);
            
    UART_Write_Text(buffer);
    UART_Write_Text("\r\n");
}

// ==========================================
//  5. WHAC_A_MOLE_OUTPUT (Updated v1.4)
//  Function: Updates turn-based WAM state.
//  Protocol: $WAM,<S1>,<S2>,<In>,<Hit>,<Miss>,<Time>,<Win>,<P1St>,<P2St>,<M0>...<M8>*
// ==========================================
void WHAC_A_MOLE_OUTPUT(WHAC_A_MOLE_OUTPUT_TABLE table) {
    char buffer[160]; // Large buffer for safety
    
    // Handle Empty Input (avoid sending null char)
    char safe_input = (table.INPUT == 0) ? 'N' : table.INPUT;

    sprintf(buffer, "$WAM,%d,%d,%c,%d,%d,%ld,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d*",
            table.SCORE_P1,
            table.SCORE_P2,
            safe_input,
            table.HIT,
            table.MISS,
            table.REMAINING_TIME,
            table.WINNER,
            table.PLAYER1_STATE,  // Index 8: P1 State
            table.PLAYER2_STATE,  // Index 9: P2 State
            // Moles start at Index 10
            table.WHAC_A_MOLE[0], table.WHAC_A_MOLE[1], table.WHAC_A_MOLE[2],
            table.WHAC_A_MOLE[3], table.WHAC_A_MOLE[4], table.WHAC_A_MOLE[5],
            table.WHAC_A_MOLE[6], table.WHAC_A_MOLE[7], table.WHAC_A_MOLE[8]);
            
    UART_Write_Text(buffer);
    UART_Write_Text("\r\n");
}

// ==========================================
//  6. END_OUTPUT
//  Function: Displays final results.
//  Protocol: $END,<Win>,<P1W>,<P2W>*
// ==========================================
void END_OUTPUT(END_OUTPUT_TABLE table) {
    char buffer[50];
    
    sprintf(buffer, "$END,%d,%d,%d*",
            table.WHO_WIN,
            table.P1_WIN_AMOUNT,
            table.P2_WIN_AMOUNT);
            
    UART_Write_Text(buffer);
    UART_Write_Text("\r\n");
}