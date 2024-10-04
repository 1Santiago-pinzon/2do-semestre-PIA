# Este codigo hace que funcionen los componentes de la casa

import machine, bluetooth
from BLE import BLEUART
import time
import _thread

p12 = machine.Pin(12)
pwm12 = machine.PWM(p12)
pwm12.freq(50)

p25 = machine.Pin(25)
pwm25 = machine.PWM(p25)
pwm25.freq(500)

p26 = machine.Pin(26)
pwm26 = machine.PWM(p26)
pwm26.freq(500)

motor_flag = False
servo_flag = False
led_flag = False


led = machine.Pin(32, machine.Pin.OUT)
led.value(0)

def rutina_motor():
    global pwm25, pwm26, motor_flag
    while True:
        if motor_flag:
            pwm25.duty(int(2**10 / 2))
            pwm26.duty(0)
            time.sleep(5)
            pwm25.duty(int(2**10 - 1))
            pwm26.duty(0)
            time.sleep(5)
            pwm26.duty(int(2**10 / 2))
            pwm25.duty(0)
            time.sleep(5)
            pwm26.duty(int(2**10 - 1))
            pwm25.duty(0)
            time.sleep(5)
        else:
            pwm26.duty(0)
            pwm25.duty(0)
            time.sleep(0.001)
        time.sleep(0.001)

_thread.start_new_thread(rutina_motor, ())

def rutina_servo():
    global pwm12, servo_flag
    while True:
        if servo_flag:
            pwm12.duty(26)
            time.sleep(1)
            pwm12.duty(51)
            time.sleep(1)
            pwm12.duty(102)
            time.sleep(1)
            pwm12.duty(128)
            time.sleep(1)
        time.sleep(0.001)

_thread.start_new_thread(rutina_servo, ())

nombreBluetooth = "Prueba"


ble = bluetooth.BLE()
buart = BLEUART(ble, nombreBluetooth)

def on_RX():
    global servo_flag, motor_flag, led_flag

    rxbuffer = buart.read().decode().rstrip('\x00')
    rxbuffer = rxbuffer.replace("\n", "").replace("\r", "")

    if rxbuffer == "motor on":
        motor_flag = True
    if rxbuffer == "motor off":
        motor_flag = False
    if rxbuffer == "servo on":
        servo_flag = True
    if rxbuffer == "servo off":
        servo_flag = False
    if rxbuffer == "led on":
        led_flag = True
        led.value(1)
        buart.write("LED encendido\n")
    if rxbuffer == "led off":
        led_flag = False
        led.value(0)
        buart.write("LED apagado\n")

    print(rxbuffer)

def on_Disconect():
    print("APP Desconectada")

buart.irq(handler=on_RX)
buart.discnthandler(handler=on_Disconect)

while True:
    temp = "hola"
    buart.write("EMA01 dice: " + str(temp) + "\n")
    time.sleep(1)
