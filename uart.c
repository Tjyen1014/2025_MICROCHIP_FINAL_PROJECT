#include <xc.h>
    //setting TX/RX

char mystring[20];
int lenStr = 0;
volatile int string_ready = 0;
void UART_Initialize() {
           
    TRISCbits.TRISC6 = 1;            
    TRISCbits.TRISC7 = 1;            
    
    //  Setting baud rate 2400 for 1MHz
    TXSTAbits.SYNC = 0;           
    BAUDCONbits.BRG16 = 1;          
    TXSTAbits.BRGH = 0;
    SPBRG = 25;      
    
   //   Serial enable
    RCSTAbits.SPEN = 1;              
    PIR1bits.TXIF = 0;
    PIR1bits.RCIF = 0;
    TXSTAbits.TXEN = 1;           
    RCSTAbits.CREN = 1;             
    PIE1bits.TXIE = 0;       
    IPR1bits.TXIP = 0;             
    PIE1bits.RCIE = 1;              
    IPR1bits.RCIP = 1;    
    
}

void UART_Write(unsigned char data)  // Output on Terminal
{
    while(!TXSTAbits.TRMT);
    TXREG = data;              //write to TXREG will send data 
}


void UART_Write_Text(char* text) { // Output on Terminal, limit:10 chars
    for(int i=0;text[i]!='\0';i++)
        UART_Write(text[i]);
}

void ClearBuffer(){
    for(int i = 0; i < 10 ; i++)
        mystring[i] = '\0';
    lenStr = 0;
}

void MyusartRead()
{
    unsigned char data = RCREG;
    UART_Write(data);
    if(data == '\r') 
    {
        UART_Write('\n');  
        lenStr = 0; 
        string_ready=1;
    }
    else 
    {
        if(lenStr < 19) 
        {
            mystring[lenStr] = data;
            lenStr++;
        }
    }
    
    return ;
}

char *GetString(){
    return mystring;
}