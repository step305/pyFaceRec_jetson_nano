import time
import serial
from datetime import datetime
import os
from parameters import *
import Jetson.GPIO as GPIO


def door_relay(relay_id, state):
    if (relay_id > 0) & (relay_id < 5):
        if state == 'on':
            GPIO.output(GPIO_RELAY_PINS[relay_id-1], GPIO.HIGH)
        elif state == 'off':
            GPIO.output(GPIO_RELAY_PINS[relay_id - 1], GPIO.LOW)


def door_lock_thread(person_id, led1_event, led2_event, disp_off_event, stop):
    if USE_WIEGAND:
        wiegand_port = serial.Serial(port='/dev/ttyACM0', baudrate=9600)

    snd_allowed = ('gst-launch-1.0 filesrc location=media/allowed.ogg ! oggdemux ! '
                   'vorbisdec ! audioconvert ! audioresample ! pulsesink &')

    GPIO.setmode(GPIO.BCM)
    for pin in GPIO_RELAY_PINS:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    time2led1_off = time.time()
    time2led2_off = time.time()
    time2next_door_open = time.time()

    while True:
        if stop.is_set():
            break
        now_time = time.time()

        if led1_event.is_set():
            disp_off_event.set()
            led1_event.clear()
            time2led1_off = now_time + LEDON_REMAIN_TIME
            if USE_WIEGAND:
                str_cmd = "$1: card=0 :command=2\n"
                wiegand_port.write(str_cmd.encode('ascii'))
                time.sleep(0.01)
            door_relay(2, 'on')

        if led2_event.is_set():
            led2_event.clear()
            time2led2_off = now_time + LEDON_REMAIN_TIME
            if USE_WIEGAND:
                str_cmd = "$3: card=0 :command=2\n"
                wiegand_port.write(str_cmd.encode('ascii'))
                time.sleep(0.01)
            door_relay(4, 'on')

        if time2led1_off < (now_time + 1):
            if USE_WIEGAND:
                str_cmd = "$1: card=0 :command=3\n"
                wiegand_port.write(str_cmd.encode('ascii'))
                time.sleep(0.01)
            door_relay(2, 'off')

        if time2led2_off < (now_time + 1):
            if USE_WIEGAND:
                str_cmd = "$3: card=0 :command=3\n"
                wiegand_port.write(str_cmd.encode('ascii'))
                time.sleep(0.01)
            door_relay(4, 'off')

        if person_id.empty():
            time.sleep(0.05)
            continue

        door_id, pers_id_data = person_id.get()

        if len(pers_id_data) > 0:
            nowDate = datetime.now()
            log_filepath = 'Logs/log_{}_{}_{}.txt'.format(nowDate.day, nowDate.month, nowDate.year)
            user_name, user_id, user_timestamp = pers_id_data[0]

            if time2next_door_open < (now_time + 1):
                if USE_WIEGAND:
                    if SEND_CARD_ID:
                        str_cmd = "$0: card={} :command=5\n".format(user_id)
                        wiegand_port.write(str_cmd.encode('ascii'))
                        time.sleep(0.1)
                    str_cmd = "$2: card=0 :command=2\n"
                    wiegand_port.write(str_cmd.encode('ascii'))
                    time.sleep(0.01)
                    str_cmd = "$0: card=0 :command=2\n"
                    wiegand_port.write(str_cmd.encode('ascii'))
                    time.sleep(0.01)
                door_relay(3, 'on')
                door_relay(1, 'on')
                print('Unlocked for {}'.format(user_name))

                os.system(snd_allowed)
                time.sleep(1)

                if USE_WIEGAND:
                    str_cmd = "$2: card=0 :command=3\n"
                    wiegand_port.write(str_cmd.encode('ascii'))
                    time.sleep(0.01)
                    str_cmd = "$0: card=0 :command=3\n"
                    wiegand_port.write(str_cmd.encode('ascii'))
                    time.sleep(0.01)
                door_relay(3, 'off')
                door_relay(1, 'off')
                print('Locked the door')

                time2next_door_open = time.time() + DOOR_SLEEP_TIME

            if LOG_DOOR_EVENTS:
                log_file = open(log_filepath, 'a')
                log_file.write("{}.{}.{} Users detected at door #{}:\n".format(nowDate.day,
                                                                               nowDate.month,
                                                                               nowDate.year,
                                                                               door_id))
                for id_data in pers_id_data:
                    user_name, user_id, user_timestamp = id_data
                    log_file.write("{}:{}:{} - {} (#{})\n".format(user_timestamp.hour,
                                                                  user_timestamp.minute,
                                                                  user_timestamp.second,
                                                                  user_name,
                                                                  user_id))
                log_file.close()
    if USE_WIEGAND:
        wiegand_port.close()
