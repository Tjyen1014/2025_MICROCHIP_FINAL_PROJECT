#include <stdio.h>

typedef struct {
    /***
        board: 0 is O, 1 is X, -1 is non-fill
        0,1,2
        3,4,5
        6,7,8
        curplayer: 0 is O, 1 is X (who lead board change this time)
        detwinner: 0 no winner, 1 has winner
        success: the move legal or not
    ***/
    int BOARD[9];
	int CURPLAYER;
	int DETWINNER;
	int SUCCESS;
} TTT_OUTPUT_TABLE;

int PQ[2][3];//playerQueue
int pt[2];

int detwinner(int i){
    if(PQ[i][2]==-1)
        return 0;
    if(PQ[i][0]%3==PQ[i][1]%3 && PQ[i][1]%3==PQ[i][2]%3) // same column
        return 1;
    if(PQ[i][0]/3==PQ[i][1]/3 && PQ[i][1]/3==PQ[i][2]/3) // same row
        return 1;
    if(PQ[i][1]==4 && PQ[i][0]+PQ[i][1]+PQ[i][2]==12)// dia
        return 1;
    return 0; 
}

TTT_OUTPUT_TABLE TTT_START(TTT_OUTPUT_TABLE TTTO_TABLE){
    for(int i=0;i<3;i++)
        for(int j=0;j<3;j++)
            PQ[i][j]=-1;
    for(int i=0;i<9;i++)
        TTTO_TABLE.BOARD[i]=-1;
    pt[0]=0;
    pt[1]=0;
    TTTO_TABLE.CURPLAYER = 0;
    TTTO_TABLE.DETWINNER = 0;
    TTTO_TABLE.SUCCESS = 1;
    return TTTO_TABLE;
}

TTT_OUTPUT_TABLE TTT_UPDATE(TTT_OUTPUT_TABLE TTTO_TABLE,int P1_PRESS,int P2_PRESS,int num){
    if((P1_PRESS==TTTO_TABLE.CURPLAYER)||(P2_PRESS!=TTTO_TABLE.CURPLAYER)){
        TTTO_TABLE.SUCCESS=0;
        return TTTO_TABLE;
    }
    
    if(TTTO_TABLE.BOARD[num] > -1){
        TTTO_TABLE.SUCCESS=0;
        return TTTO_TABLE;
    }
    TTTO_TABLE.SUCCESS = 1;
    TTTO_TABLE.BOARD[num] = TTTO_TABLE.CURPLAYER;
    if(PQ[TTTO_TABLE.CURPLAYER][pt[TTTO_TABLE.CURPLAYER]] > -1)
        TTTO_TABLE.BOARD[PQ[TTTO_TABLE.CURPLAYER][pt[TTTO_TABLE.CURPLAYER]]] = -1;
    PQ[TTTO_TABLE.CURPLAYER][pt[TTTO_TABLE.CURPLAYER]] = num;
    pt[TTTO_TABLE.CURPLAYER] = (pt[TTTO_TABLE.CURPLAYER]+1) % 3;
    TTTO_TABLE.DETWINNER = detwinner(TTTO_TABLE.CURPLAYER);
    TTTO_TABLE.CURPLAYER = (TTTO_TABLE.CURPLAYER + 1) % 2;
    return TTTO_TABLE;
}
