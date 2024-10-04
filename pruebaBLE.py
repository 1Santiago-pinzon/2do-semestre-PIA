# Este comprueba que se esta conectado a bluetooth

#Se llaman las librerias
import machine,bluetooth
from BLE import BLEUART
import time
#Se le asigna el nombre del ESP32 como "Prueba"
nombreBluetooth="Prueba"

#Instancias de objetos
ble=bluetooth.BLE()    # Inicializa el módulo Bluetooth
buart=BLEUART(ble,nombreBluetooth)    # Crea una instancia de BLEUART con el nombre definido


def on_RX():
    # Función que se llama cuando se recibe un mensaje por Bluetooth
    rxbuffer=buart.read().decode().rstrip('\x00')    # Lee y decodifica el mensaje recibido
    rxbuffer=rxbuffer.replace("\n","")     # Elimina saltos de línea
    rxbuffer=rxbuffer.replace("\r","")    # Elimina retornos de carro
    
    print(rxbuffer)    # Imprime el mensaje recibido en la consola
    
def on_Disconect():
    # Función que se llama cuando se pierde la conexión
    print("APP Desconectada")    # Informa que la aplicación se ha desconectado
    
    
    
# Configura las interrupciones
buart.irq(handler=on_RX)    # Configura la función on_RX para manejar la recepción de datos
buart.discnthandler(handler=on_Disconect)    # Configura la función on_Disconect para manejar la desconexión
    
# Bucle principal
while True:
    
    temp="hola"    # Variable que almacena un mensaje a enviar
    buart.write("EMA01 dice: "+str(temp)+"\n")    # Envía el mensaje a través de Bluetooth
    time.sleep(1)     #Espera 1 segundo antes de enviar el siguiente mensaje
