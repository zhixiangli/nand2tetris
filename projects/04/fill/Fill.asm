// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.
(MAIN)
    @KBD
    D=M
    @BLACK
    D, JGT
    @WHITE
    D, JEQ

(BLACK)
    @R0
    M=-1
    @DRAW
    0;JMP

(WHITE)
    @R0
    M=0
    @DRAW
    0;JMP

(DRAW)
    // i = @SCREEN + (8192 - 1)
    @8191
    D=A
    @SCREEN
    D=A+D
    @i
    M=D

    (LOOP)
        // get color
        @R0
        D=M

        // set color
        @i
        A=M
        M=D

        // i = i - 1
        @i
        M=M-1

        // i >= @SCREEN?
        @SCREEN
        D=A
        @i
        D=M-D
        @MAIN
        D;JLT

    @LOOP
    0;JMP