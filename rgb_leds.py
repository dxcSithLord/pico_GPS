from machine import Pin, PWM
from utime import sleep

pins = [0, 1, 2]
colors = ['red', 'green', 'blue']
pwms = [PWM(Pin(pin,Pin.OUT)) for pin in pins]
for pwm in pwms:
    pwm.freq(1000)

def map_color(color):
    return int(color * 65535 / 255)

def set_color(red, green, blue):
    pwms[0].duty_u16(map_color(red))
    pwms[1].duty_u16(map_color(green))
    pwms[2].duty_u16(map_color(blue))

set_color(255, 0, 0)
sleep(0.2)
set_color(0, 255, 0)
sleep(0.2)
set_color(0, 0, 255)
sleep(0.2)
set_color(255, 255, 0)
sleep(0.2)
set_color(0, 255, 255)
sleep(0.2)
set_color(255, 0, 255)
sleep(0.2)
set_color(255,255,255)
sleep(0.2)
set_color(0,0,0)