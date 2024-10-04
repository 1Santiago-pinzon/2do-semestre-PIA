# Este es el código que configura y activa el Bluetooth

import bluetooth
import io
import os
import micropython
import machine
from micropython import const
import struct
import time
from machine import Pin

# Configura un pin para indicar el estado de conexión Bluetooth
pbt = Pin(2, Pin.OUT)
pbt.off()  # Asegúrate de que el pin esté apagado al inicio

# Definición de constantes para manejar interrupciones y características Bluetooth
_IRQ_CENTRAL_CONNECT = const(1)  # Interrupción: conexión central
_IRQ_CENTRAL_DISCONNECT = const(2)  # Interrupción: desconexión central
_IRQ_GATTS_WRITE = const(3)  # Interrupción: escritura en el GATT server

# Definición de banderas para el servicio UART
_FLAG_WRITE = const(0x0008)  # Bandera para escritura
_FLAG_NOTIFY = const(0x0010)  # Bandera para notificación

# UUIDs del servicio y características UART
_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")  # UUID del servicio UART
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),  # UUID para transmisión
    _FLAG_NOTIFY,  # Habilita notificaciones
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),  # UUID para recepción
    _FLAG_WRITE,  # Habilita escritura
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),  # Servicios UART
)

# Definición de constante para apariencia del dispositivo en el escaneo
_ADV_APPEARANCE_GENERIC_COMPUTER = const(128)


class BLEUART:
    def __init__(self, ble, name, rxbuf=1000):
        self._ble = ble  # Almacena la instancia de BLE
        time.sleep(0.5)  # Espera para asegurar la inicialización del BLE
        self._ble.active(True)  # Activa el módulo Bluetooth
        # self._ble.config(mtu=200)  # Opcional: configuración del tamaño máximo de unidad
        self._ble.irq(self._irq)  # Configura la función de manejo de interrupciones
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((_UART_SERVICE,))  # Registra el servicio UART
        
        # Aumenta el tamaño del buffer de recepción y habilita el modo de adición.
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self._connections = set()  # Conjuntos para manejar conexiones
        self._rx_buffer = bytearray()  # Buffer para datos recibidos
        self._handler = None  # Manejador para datos recibidos
        self._disconecthandler = None  # Manejador para desconexiones

        # Genera la carga útil para la publicidad
        self._payload = advertising_payload(
            name=name, appearance=_ADV_APPEARANCE_GENERIC_COMPUTER)
        self._advertise()  # Inicia la publicidad

    def irq(self, handler):
        self._handler = handler  # Asigna el manejador de interrupciones

    def discnthandler(self, handler):
        self._disconecthandler = handler  # Asigna el manejador de desconexiones

    def _irq(self, event, data):
        # Manejo de interrupciones para conexiones y escrituras
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data  # Extrae el manejador de conexión
            print("_IRQ_CENTRAL_CONNECT")  # Imprime en consola cuando se conecta
            pbt.on()  # Enciende el pin de estado
            self._connections.add(conn_handle)  # Agrega la conexión al conjunto
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data  # Extrae el manejador de conexión
            pbt.off()  # Apaga el pin de estado
            print('_IRQ_CENTRAL_DISCONNECT')  # Imprime en consola cuando se desconecta
            if self._disconecthandler:
                self._disconecthandler()  # Llama al manejador de desconexión
            
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)  # Remueve la conexión del conjunto
            self._advertise()  # Comienza a publicitar nuevamente para permitir nuevas conexiones
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data  # Extrae los manejadores de conexión y valor
            if conn_handle in self._connections and value_handle == self._rx_handle:
                self._rx_buffer += self._ble.gatts_read(self._rx_handle)  # Lee y almacena datos en el buffer
                if self._handler:
                    self._handler()  # Llama al manejador de recepción de datos

    def any(self):
        return len(self._rx_buffer)  # Retorna la longitud del buffer de recepción

    def read(self, sz=None):
        if not sz:
            sz = len(self._rx_buffer)  # Si no se especifica tamaño, usa el tamaño del buffer
        result = self._rx_buffer[0:sz]  # Extrae los datos del buffer
        self._rx_buffer = self._rx_buffer[sz:]  # Actualiza el buffer
        return result  # Retorna los datos leídos

    def write(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)  # Envía notificaciones a todos los clientes conectados

    def close(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)  # Desconecta todos los clientes
        self._connections.clear()  # Limpia el conjunto de conexiones

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)  # Comienza la publicidad con la carga útil


# Tipos de anuncios para la carga útil de publicidad
_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_UUID16_MORE = const(0x2)
_ADV_TYPE_UUID32_MORE = const(0x4)
_ADV_TYPE_UUID128_MORE = const(0x6)
_ADV_TYPE_APPEARANCE = const(0x19)


# Genera una carga útil para ser pasada a gap_advertise(adv_data=...).
def advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
    payload = bytearray()  # Inicializa el buffer de carga útil

    def _append(adv_type, value):
        nonlocal payload
        payload += struct.pack("BB", len(value) + 1, adv_type) + value  # Empaqueta el tipo y el valor en el payload

    # Agrega el tipo de anuncio (flags) al payload
    _append(
        _ADV_TYPE_FLAGS,
        struct.pack("B", (0x01 if limited_disc else 0x02) +
                    (0x18 if br_edr else 0x04)),
    )

    if name:
        _append(_ADV_TYPE_NAME, name)  # Agrega el nombre al payload

    if services:
        for uuid in services:
            b = bytes(uuid)  # Convierte el UUID a bytes
            if len(b) == 2:
                _append(_ADV_TYPE_UUID16_COMPLETE, b)  # Agrega UUID de 16 bits completo
            elif len(b) == 4:
                _append(_ADV_TYPE_UUID32_COMPLETE, b)  # Agrega UUID de 32 bits completo
            elif len(b) == 16:
                _append(_ADV_TYPE_UUID128_COMPLETE, b)  # Agrega UUID de 128 bits completo

    # Agrega apariencia del dispositivo al payload
    if appearance:
        _append(_ADV_TYPE_APPEARANCE, struct.pack("<h", appearance))

    return payload  # Retorna la carga útil generada


def demo():
    print("demo")  # Función de demostración simple


# Comprobación del nombre del módulo para ejecutar demo
if __name__ == "__main__":
    demo()  # Llama a la función demo si se ejecuta como script principal
