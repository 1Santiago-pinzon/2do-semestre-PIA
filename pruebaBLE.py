import machine,bluetooth
from BLE import BLEUART
import time

nombreBluetooth="Prueba"

#Instancias de objetos
ble=bluetooth.BLE()
buart=BLEUART(ble,nombreBluetooth)


def on_RX():
    
    rxbuffer=buart.read().decode().rstrip('\x00')
    rxbuffer=rxbuffer.replace("\n","")
    rxbuffer=rxbuffer.replace("\r","")
    
    print(rxbuffer)
    
def on_Disconect():
    print("APP Desconectada")
    
    
    
    
buart.irq(handler=on_RX)
buart.discnthandler(handler=on_Disconect)
    

while True:
    
    temp="hola"
    buart.write("EMA01 dice: "+str(temp)+"\n")
    time.sleep(1)
