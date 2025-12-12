# Serial Communication Protocol Specification

**Interface:** UART (Universal Asynchronous Receiver-Transmitter)

## Connection Settings
The receiving application must configure the serial port with the following parameters:

| Parameter | Value |
| :--- | :--- |
| **Baud Rate** | **2400** bps |
| **Port** | COM? |

---

## Packet Structure
All data packets are transmitted as **ASCII strings** using a Comma-Separated Values format enclosed by start and end delimiters.

**General Format:**
`$<HEADER>,<DATA_1>,<DATA_2>,...,<DATA_N>*`

* **Start Delimiter:** `$` (ASCII 0x24)
* **Separator:** `,` (ASCII 0x2C)
* **End Delimiter:** `*` (ASCII 0x2A)
* **Line Ending:** packets are followed by `\r\n` (CR+LF), but the parser should rely on `*` as the terminator.

---

## Message Definitions

### 1. System Startup
Sent once when the microcontroller initializes or resets.

* **Format:** `$START*`

### 2. Game Preparation (Hint Screen)
Sent continuously during the waiting phase before any game stage starts.

* **Format:** `$HINT,<Game_State>,<P1_Ready>,<P2_Ready>*`

| Index | Name | Type | Description / Enumeration |
| :--- | :--- | :--- | :--- |
| 0 | Header | String | `$HINT` |
| 1 | Game_State | Int | `1`: Tic-Tac-Toe (Stage 1)<br>`2`: Reaction Game (Stage 2)<br>`3`: Whac-A-Mole (Stage 3) |
| 2 | P1_Ready | Int | `0`: Waiting<br>`1`: Ready (Button Pressed) |
| 3 | P2_Ready | Int | `0`: Waiting<br>`1`: Ready (Button Pressed) |

### 3. Tic-Tac-Toe Game State ($TTT)
* **Format:** `$TTT,<B0>,<B1>,...,<B8>,<CurPlayer>,<Winner>,<Cursor>*`

| Index | Name | Protocol Value | Description |
| :--- | :--- | :--- | :--- |
| 0 | Header | String | `$TTT` |
| 1 - 9 | Board[0]..[8] | **0 / 1 / 2** | **0**: Empty<br>**1**: Player 1 (O)<br>**2**: Player 2 (X)<br>*(Note: Firmware handles internal -1 conversion)* |
| 10 | Current_Player | **1 / 2** | **1**: Player 1's turn<br>**2**: Player 2's turn |
| 11 | Winner | **0 / 1 / 2** | **0**: In Progress / Draw<br>**1**: Player 1 Wins<br>**2**: Player 2 Wins |
| **12** | **Cursor_Position** | **0 - 8** | Current grid position targeted by the potentiometer (ADC). |

> **Note:** The UI simply renders the board state as received.

### 4. Reaction Game State ($REACT)
* **Format:** `$REACT,<RndNum>,<Disp1>,<Disp2>,<P1Res>,<P2Res>,<Win>,<Time>,<P1St>,<P2St>*`

| Index | Name | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | Header | String | `$REACT` |
| 1 | Target_Number | Int | The fixed target number (e.g., 50). |
| 2 | Display_1 | Int | Current number shown on Player 1's screen. |
| 3 | Display_2 | Int | Current number shown on Player 2's screen. |
| 4 | P1_Result | Int | P1's final locked number (`-1` if not finished). |
| 5 | P2_Result | Int | P2's final locked number (`-1` if not finished). |
| 6 | Winner | Int | `-1`: In Progress<br>`1`: Player 1 (Closer to target)<br>`2`: Player 2 (Closer to target) |
| 7 | Time_Tick | Long | Game timer (Unit: 100us). |
| 8 | **P1_State** | **Int** | **0**: Waiting / Idle<br>**1**: **Rolling** (Number is changing, press to stop)<br>**2**: **Locked** (Turn finished, result fixed) |
| 9 | **P2_State** | **Int** | **0**: Waiting / Idle<br>**1**: **Rolling** (Number is changing, press to stop)<br>**2**: **Locked** (Turn finished, result fixed) |

### 5. Whac-A-Mole Game State ($WAM)
* **Format:** `$WAM,<S1>,<S2>,<Input>,<Hit>,<Miss>,<Time>,<Win>,<P1St>,<P2St>,<M0>...<M8>*`

| Index | Name | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | Header | String | `$WAM` |
| 1 | Score_P1 | Int | Current score of Player 1. |
| 2 | Score_P2 | Int | Current score of Player 2. |
| 3 | Last_Input | Char | The key currently processed (e.g., '1'-'9').<br>Returns **'N'** if no input (empty). |
| 4 | Hit_Flag | Int | **0**: No Action<br>**1**: **Hit Event** (Just happened this tick) |
| 5 | Miss_Flag | Int | **0**: No Action<br>**1**: **Miss Event** (Wrong key or Timeout) |
| 6 | Remaining_Time | Long | Time remaining. |
| 7 | Winner | Int | `-1`: In Progress<br>`0`: Draw<br>`1`: Player 1<br>`2`: Player 2 |
| 8 | **P1_State** | **Int** | **0**: Wait/Idle<br>**1**: Playing<br>**2**: Done |
| 9 | **P2_State** | **Int** | **0**: Wait/Idle<br>**1**: Playing<br>**2**: Done |
| 10 - 18 | Mole[0]..[8] | Int | **0**: Hole is empty<br>**1**: Mole is visible |

### 4.6. Final Results ($END)
Sent continuously when all games are completed.

* **Format:** `$END,<WhoWin>,<P1WinAmt>,<P2WinAmt>*`

| Index | Name | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | Header | String | `$END` |
| 1 | Overall_Winner | Int | `0`: Draw<br>`1`: Player 1 Champion<br>`2`: Player 2 Champion |
| 2 | P1_Win_Count | Int | Total games won by Player 1. |
| 3 | P2_Win_Count | Int | Total games won by Player 2. |

---

## 5. Typical Data Flow
The following sequence illustrates a standard game session:

1.  **Boot:** `$START*`
2.  **Wait P1:** `$HINT,1,0,0*` (Stage 1 Preparation)
3.  **Wait P2:** `$HINT,1,1,0*`
4.  **Game 1 Start:** `$TTT,0,0,0,0,0,0,0,0,0,1,0,4*` (Empty board, P1 turn, Cursor at 4)
5.  **P1 Move:** `$TTT,1,0,0,0,0,0,0,0,0,2,0,2*` (Center occupied, P2 turn, Cursor at 2)
6.  **P1 Win:** `$TTT,1,2,1,0,2,0,0,0,0,2,1,2*` (Winner=1, Game Over)
7.  **Transition 2:** `$HINT,2,0,0*` (Preparing for Stage 2)
8.  **Game 2:** `$REACT,50,0,0,-1,-1,-1,12345,0,0*`
9.  **Transition 3:** `$HINT,3,0,0*` (Preparing for Stage 3)
10. **Game 3:** `$WAM,0,0,N,0,0,600000,-1,0,0,1,0...*`
11. **End:** `$END,1,2,1*` (P1 is the Champion)