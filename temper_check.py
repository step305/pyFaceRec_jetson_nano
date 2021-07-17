import temper_parser
import serial
from parameters import *
import time


def temper_check(temper, stop):
    serial_dev = serial.Serial(port=TEMPER_SENSOR_SERIAL_DEV, baudrate=9600,
                               bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE, xonxoff=False,
                               rtscts=False, dsrdtr=False)
    parser = temper_parser.TemperParserState()
    time.sleep(20)
    while True:
        if stop.is_set():
            break
    data_len = serial_dev.in_waiting
    if data_len > 0:
        buffer =serial_dev.read(size=data_len)
        for next_byte in buffer:
            parser.parse_byte(next_byte)
            if parser.data_ready:
                TA, To1 = parser.packet
                print('Temperature: TA = {:0.2f}, To1 = {:0.2f}'.formta(TA, To1))
                if not temper.full():
                    temper.put((TA, To1))
    serial_dev.close()
    print('Temper thread done')
