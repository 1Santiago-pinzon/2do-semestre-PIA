# Este código hace que funcionen los componentes de la casa

import machine, bluetooth  # Importa las librerías necesarias
from BLE import BLEUART  # Importa la clase BLEUART para la comunicación Bluetooth
import time  # Importa el módulo time para manejar delays
import _thread  # Importa el módulo para trabajar con hilos

# Configuración de pines y PWM para controlar los componentes
p12 = machine.Pin(12)  # Pin para el servo
pwm12 = machine.PWM(p12)  # Configura PWM en el pin 12
pwm12.freq(50)  # Establece la frecuencia de PWM a 50 Hz

p25 = machine.Pin(25)  # Pin para el motor
pwm25 = machine.PWM(p25)  # Configura PWM en el pin 25
pwm25.freq(500)  # Establece la frecuencia de PWM a 500 Hz

p26 = machine.Pin(26)  # Otro pin para el motor
pwm26 = machine.PWM(p26)  # Configura PWM en el pin 26
pwm26.freq(500)  # Establece la frecuencia de PWM a 500 Hz

# Flags para el estado de los componentes
motor_flag = False  # Estado del motor
servo_flag = False  # Estado del servo
led_flag = False  # Estado del LED

# Configuración del LED
led = machine.Pin(32, machine.Pin.OUT)  # Pin para el LED
led.value(0)  # Inicializa el LED apagado

def rutina_motor():
    global pwm25, pwm26, motor_flag  # Declaración de variables globales
    while True:
        if motor_flag:  # Si el motor está activado
            # Ciclo de control del motor
            pwm25.duty(int(2**10 / 2))  # Ajusta la potencia del motor
            pwm26.duty(0)  # Detiene el segundo motor
            time.sleep(5)  # Espera 5 segundos
            pwm25.duty(int(2**10 - 1))  # Aumenta la potencia del motor
            pwm26.duty(0)  # Detiene el segundo motor
            time.sleep(5)  # Espera 5 segundos
            pwm26.duty(int(2**10 / 2))  # Ajusta la potencia del segundo motor
            pwm25.duty(0)  # Detiene el primer motor
            time.sleep(5)  # Espera 5 segundos
            pwm26.duty(int(2**10 - 1))  # Aumenta la potencia del segundo motor
            pwm25.duty(0)  # Detiene el primer motor
            time.sleep(5)  # Espera 5 segundos
        else:
            # Si el motor no está activado, apaga ambos motores
            pwm26.duty(0)
            pwm25.duty(0)
            time.sleep(0.001)  # Pequeña pausa para evitar sobrecarga del CPU
        time.sleep(0.001)  # Pausa para evitar sobrecarga del CPU

# Inicia el hilo para la rutina del motor
_thread.start_new_thread(rutina_motor, ())

def rutina_servo():
    global pwm12, servo_flag  # Declaración de variables globales
    while True:
        if servo_flag:  # Si el servo está activado
            # Ciclo de control del servo
            pwm12.duty(26)  # Mueve el servo a una posición
            time.sleep(1)  # Espera 1 segundo
            pwm12.duty(51)  # Mueve el servo a otra posición
            time.sleep(1)  # Espera 1 segundo
            pwm12.duty(102)  # Mueve el servo a otra posición
            time.sleep(1)  # Espera 1 segundo
            pwm12.duty(128)  # Mueve el servo a otra posición
            time.sleep(1)  # Espera 1 segundo
        time.sleep(0.001)  # Pausa para evitar sobrecarga del CPU

# Inicia el hilo para la rutina del servo
_thread.start_new_thread(rutina_servo, ())

# Nombre del dispositivo Bluetooth
nombreBluetooth = "Prueba"

# Inicializa el Bluetooth y el servicio BLEUART
ble = bluetooth.BLE()
buart = BLEUART(ble, nombreBluetooth)

def on_RX():
    global servo_flag, motor_flag, led_flag  # Declaración de variables globales

    # Lee los datos recibidos por Bluetooth
    rxbuffer = buart.read().decode().rstrip('\x00')  # Lee y decodifica el buffer
    rxbuffer = rxbuffer.replace("\n", "").replace("\r", "")  # Limpia el buffer

    # Control de los componentes basado en el comando recibido
    if rxbuffer == "motor on":
        motor_flag = True  # Activa el motor
    if rxbuffer == "motor off":
        motor_flag = False  # Desactiva el motor
    if rxbuffer == "servo on":
        servo_flag = True  # Activa el servo
    if rxbuffer == "servo off":
        servo_flag = False  # Desactiva el servo
    if rxbuffer == "led on":
        led_flag = True  # Activa el LED
        led.value(1)  # Enciende el LED
        buart.write("LED encendido\n")  # Envía respuesta al cliente
    if rxbuffer == "led off":
        led_flag = False  # Desactiva el LED
        led.value(0)  # Apaga el LED
        buart.write("LED apagado\n")  # Envía respuesta al cliente

    print(rxbuffer)  # Imprime el comando recibido en la consola

def on_Disconect():
    print("APP Desconectada")  # Mensaje cuando se desconecta la aplicación

# Configura las interrupciones para manejar datos y desconexiones
buart.irq(handler=on_RX)  # Maneja la recepción de datos
buart.discnthandler(handler=on_Disconect)  # Maneja la desconexión

# Bucle principal para enviar mensajes
while True:
    temp = "hola"  # Mensaje temporal para enviar
    buart.write("EMA01 dice: " + str(temp) + "\n")  # Envía el mensaje por Bluetooth
    time.sleep(1)  # Espera 1 segundo antes de enviar el siguiente mensaje
