#include <xc.h>
#pragma config OSC = INTIO67 // Oscillator Selection bits
#pragma config WDT = OFF     // Watchdog Timer Enable bit
#pragma config PWRT = OFF    // Power-up Enable bit
#pragma config BOREN = ON    // Brown-out Reset Enable bit
#pragma config PBADEN = OFF  // Watchdog Timer Enable bit
#pragma config LVP = OFF     // Low Voltage (single -supply) In-Circute Serial Pragramming Enable bit
#pragma config CPD = OFF     // Data EEPROM?Memory Code Protection bit (Data EEPROM code protection off)


typedef struct{
    int PROCESS; //-1 0 1/ 2 3/ 4 5/ 6
    int GAME_STATE;
    int P1_PRESS;
    int P2_PRESS;
    int ADC_VALUE;
} GAME_CONTROL_TABLE;

typedef struct {
    int GAME_STATE;
    int P1_PREPARE;
    int P2_PREPARE;
}HINT_OUTPUT_TABLE;

typedef struct {
	int BOARD[9];
	int CURPLAYER;
	int DETWINNER;
	int SUCCESS;
} TTT_OUTPUT_TABLE;

typedef struct {
	int RANDOM_NUMBER;
	int DISPLAY_NUMBER_1;
	int DISPLAY_NUMBER_2;
    unsigned long tick100us;//0.0001s
    int PLAYER1_STATE;
    int PLAYER2_STATE;
    int P1_RESULT;
    int P2_RESULT;
    int P1_WIN;
    int P2_WIN;
} REACTION_OUTPUT_TABLE;

typedef struct {
	int SCORE_P1;
    int SCORE_P2;
	int WHAC_A_MOLE[9];
	int INPUT[9];
	int HIT;
	int MISS;
	int NOT_HIT_NOT_MISS;
    unsigned long tick100us;//0.0001s
	float REMAINING_TIME;
    int WINNER;
	int PLAYER1_STATE;
	int PLAYER2_STATE;
}WHAC_A_MOLE_OUTPUT_TABLE;


volatile GAME_CONTROL_TABLE GC_TABLE;
volatile TTT_OUTPUT_TABLE TTTO_TABLE;
volatile REACTION_OUTPUT_TABLE REACTO_TABLE;



void delay(volatile unsigned long t) {
    while (t--) {
    }
    return;
}

void CLEAR_PRESS(volatile GAME_CONTROL_TABLE *GC){
    GC->P1_PRESS = 0;
    GC->P2_PRESS = 0;
}

void CONFIG_INITIALIZE(void){

    //output input configuration
    TRISB = 0b00000011; // two button
    TRISA = 1; //adc ouput

    //ADC and ADC INTERUPt SETTING
    ADCON2 = 0b00001000;
    ADCON1 = 0b00001110;
    ADCON0 = 0b00000001;

    PIE1bits.ADIE = 0;
    PIR1bits.ADIF = 0;
    IPR1bits.ADIP = 0;

    //BUTTON INTERUPT SETTING
    INTCONbits.INT0IF = 0; // button 1 RB 0
    INTCONbits.INT0IE = 1;
    INTCON3bits.INT1IF = 0; //button 2 RB 1
    INTCON3bits.INT1IE = 1;
    INTCON3bits.INT1IP = 1;

    //TIMER INTERUPT SETTIMH
    PIR1bits.TMR2IF = 0;
    PIE1bits.TMR2IE = 1;
    IPR1bits.TMR2IP = 0;
    PR2 = 1;  
    T2CON = 0b01111101; //  t2con 還未啓動


    //GENERAL INTERUPRT SETTING
    RCONbits.IPEN = 1;
    INTCONbits.GIEH = 1;
    INTCONbits.GIEL = 1;

    return;

}

void GC_TABLE_INITIALIZE(void){
    GC_TABLE.ADC_VALUE = 0;
    GC_TABLE.GAME_STATE = 1;
    GC_TABLE.P1_PRESS = 0;
    GC_TABLE.P2_PRESS = 0;
    GC_TABLE.PROCESS = -1;
}

void REACTION_OUTPUT_TABLE_INITIALIZE(void){
    REACTO_TABLE.PLAYER1_STATE = 0;
    REACTO_TABLE.PLAYER2_STATE = 0;
    REACTO_TABLE.tick100us = 0;
    REACTO_TABLE.P1_RESULT = -1;
    REACTO_TABLE.P2_RESULT = -1;
    REACTO_TABLE.P1_WIN = 0;
    REACTO_TABLE.P2_WIN = 0;
}

HINT_OUTPUT_TABLE WRITE_HO_TABLE(void){
    HINT_OUTPUT_TABLE HO_TABLE;
    HO_TABLE.GAME_STATE = GC_TABLE.GAME_STATE;
    HO_TABLE.P1_PREPARE = GC_TABLE.P1_PRESS;
    HO_TABLE.P2_PREPARE = GC_TABLE.P2_PRESS;
    return HO_TABLE;
}



void PROCESS_HINT(void){
    HINT_OUTPUT_TABLE HO_TABLE;
    while(GC_TABLE.P1_PRESS != 1 || GC_TABLE.P2_PRESS != 1){
        HO_TABLE = WRITE_HO_TABLE();
        HINT_OUTPUT(HO_TABLE);
    }
    //兩邊準備
    HINT_OUTPUT(HO_TABLE);
    //delay(65535);
    return;
}

void PROCESS_ONE(void){
    TTTO_TABLE = TTT_START(TTTO_TABLE); // include
    while(TTTO_TABLE.DETWINNER == 0){
        if(!ADCON0bits.GO){
            ADCON0bits.GO = 1;
        }
        TTT_OUTPUT(TTTO_TABLE);// include 顯示游戲過程
    }

    if(TTTO_TABLE.DETWINNER == 1){
        PIE1bits.ADIE = 0;
        TTT_OUTPUT(TTTO_TABLE); // include 顯示winner
    }
    //delay(65535);
    return;

}
//process 3 game2
void PROCESS_THREE(void){
    REACTION_OUTPUT_TABLE_INITIALIZE();
    REACTO_TABLE = REACTION_START(); //  填寫 random number
    T2CONbits.TMR2ON = 1;
    while(REACTO_TABLE.PLAYER1_STATE != 2 || REACTO_TABLE.PLAYER2_STATE !=2){
        if((REACTO_TABLE.PLAYER1_STATE == 0 && REACTO_TABLE.PLAYER2_STATE == 0) || (REACTO_TABLE.PLAYER1_STATE == 2 && REACTO_TABLE.PLAYER2_STATE == 0)){
            REACTO_TABLE.tick100us = 0;
            TMR2 =0;
        }
        REACTO_TABLE = REACTION_UPDATE(REACTO_TABLE); //include
        REACTION_OUTPUT(REACTO_TABLE);
    }
    return;
}

void main(void){   
    GC_TABLE_INITIALIZE();
    UART_INITIALIZE();// include
    CONFIG_INITIALIZE();
    START_OUTPUT();//include

    //wait p1 press to start the game;
    while(GC_TABLE.PROCESS != 0){
    }

    //process 0
    if(GC_TABLE.PROCESS == 0 && GC_TABLE.GAME_STATE == 1){
        PROCESS_HINT();
    }

    GC_TABLE.PROCESS++;
    GC_TABLE = CLEAR_PRESS(GC_TABLE);

    //GAME 1 PROCESS 1
    if(GC_TABLE.PROCESS == 1 && GC_TABLE.GAME_STATE == 1){
        PIE1bits.ADIE = 1;
        PROCESS_ONE();// game 1 is playing
    }

    GC_TABLE.PROCESS++;
    GC_TABLE.GAME_STATE++;
    GC_TABLE = CLEAR_PRESS(GC_TABLE);

    if(GC_TABLE.PROCESS == 2 && GC_TABLE.GAME_STATE == 2){
        PROCESS_HINT();
    }

    GC_TABLE.PROCESS++;
    GC_TABLE = CLEAR_PRESS(GC_TABLE);

    if(GC_TABLE.PROCESS == 3 && GC_TABLE.GAME_STATE == 2){
        PROCESS_THREE();
    }



    while(1){
        END_OUTPUT();//include
    }

    
}

void __interrupt(high_priority) Hi_ISR(void)
{
    //delay??
    if(INTCONbits.INT0IF == 1){
        
        if(GC_TABLE.PROCESS == -1){
            GC_TABLE.PROCESS++;
            INTCONbits.INT0IF = 0;
            return;
        }

        if(GC_TABLE.PROCESS == 0 || GC_TABLE.PROCESS == 2 || GC_TABLE.PROCESS == 4){
            GC_TABLE.P1_PRESS = 1;
            INTCONbits.INT0IF = 0;
            return;
        }

        if(GC_TABLE.PROCESS == 1){
            TTTO_TABLE = TTT_UPDATE(TTTO_TABLE,1,0);// update TTT_UPDATE(TTT_OUTPUT_TABLE,P1_PRESS,P2_PRESS) return output table include
            INTCONbits.INT0IF = 0;
            return;
        }

        if(GC_TABLE.PROCESS == 3){
            if(REACTO_TABLE.PLAYER1_STATE == 0 && REACTO_TABLE.PLAYER2_STATE == 0){
                REACTO_TABLE.PLAYER1_STATE = 1 ;
            }
            else if(REACTO_TABLE.PLAYER1_STATE == 1 && REACTO_TABLE.PLAYER2_STATE == 0){
                REACTO_TABLE.PLAYER1_STATE = 2 ;
            }
            // 2 0 donothing
            INTCONbits.INT0IF = 0;
            return;
        }
    }

    if(INTCON3bits.INT1IF ==1){

        if(GC_TABLE.PROCESS == -1){
            INTCON3bits.INT1IF = 0;
            return;
        }
        
        if(GC_TABLE.PROCESS == 0 || GC_TABLE.PROCESS == 2 || GC_TABLE.PROCESS == 4){
            GC_TABLE.P2_PRESS = 1;
            INTCON3bits.INT1IF = 0;
            return;
        }

        if(GC_TABLE.PROCESS == 1){
            TTTO_TABLE = TTT_UPDATE(TTTO_TABLE,0,1);
            INTCON3bits.INT1IF = 0;
            return;
        }

         if(GC_TABLE.PROCESS == 3){
            if(REACTO_TABLE.PLAYER1_STATE == 2 && REACTO_TABLE.PLAYER2_STATE == 0){
                REACTO_TABLE.PLAYER2_STATE = 1 ;
            }
            else if(REACTO_TABLE.PLAYER1_STATE == 2 && REACTO_TABLE.PLAYER2_STATE == 1){
                REACTO_TABLE.PLAYER2_STATE = 2;
            }
            // 2 2 donothing
            INTCON3bits.INT1IF = 0;
            return;
         }
    }
   
}

void __interrupt(low_priority) Lo_ISR(void)
{
    if(PIR1bits.ADIF == 1){
        GC_TABLE.ADC_VALUE = (ADRESH << 2) + (ADRESL >> 6);
        PIR1bits.ADIF = 0;
        return;
    }

    if(PIR1bits.TMR2IF == 1){
        REACTO_TABLE.tick100us++;
        PIR1bits.TMR2IF = 0;
        return;
        
    }
}
