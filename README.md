# Make Sputter by Raspberrypi, PLC(DN32S) 

## 1. Outline

I was internship in Teraleader by 2021.03 ~ 2021.12.

This is my Third Python Project in Teraleader (http://teraleader.co.kr).


## 2. Goal

Sputter : https://en.wikipedia.org/wiki/Sputtering

## 3. Component

Raspberry Pi (Raspberry Pi 3 Model B)

Extension Display (8 inch 1280 x 720)

PLC (LS DN32S)

## 4. WorkFlow

<img width="80%" src="https://user-images.githubusercontent.com/61678329/211231333-fc5a22b3-c498-4dcb-a774-6b7a28c9de1e.png"/>


## 5. Explanation

### Used Library

PyQt5, Pyserial

### Signal Rules

Digital Signal Rules

1. binary number -> hex number # fill 0 to make the number length is 4
2. '\x0501WSS0106%PW012'+ number +'\x04'

Analog Signal Rules

1. number -> hex number # fill 0 to make the number length is 4
2. '\x0501WSS0106%MW'+ address + number +'\x04'

manual : https://www.ls-electric.com/ko/product/view/P01121


