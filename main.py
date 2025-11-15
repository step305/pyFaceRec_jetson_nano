#!/usr/bin/env python3
from multiprocessing import Process
import multiprocessing
from time import sleep
from parameters import *
import video
import door_management
import faces_management
# import temper_check 제거됨


if __name__ == '__main__':
    multiprocessing.set_start_method('forkserver')

    stop_event = multiprocessing.Event()
    stop_event.clear()
    led1_event = multiprocessing.Event()
    led1_event.clear()
    led2_event = multiprocessing.Event()
    led2_event.clear()
    led3_event = multiprocessing.Event()
    led3_event.clear()

    frame_buffer = multiprocessing.Manager().Queue(1)
    person_id_queue = multiprocessing.Manager().Queue(1)
    # temper_queue = multiprocessing.Manager().Queue(1) 제거됨

    camera_process = Process(target=video.cam_thread,
                             args=(0, frame_buffer, led3_event, stop_event), daemon=True) # temper_queue 인자 제거
    camera_process.start()

    recognition_process = Process(target=faces_management.recognition_thread,
                                  args=(frame_buffer, person_id_queue,
                                        led1_event, led2_event, stop_event), daemon=True)
    recognition_process.start()

    door_lock_process = Process(target=door_management.door_lock_thread,
                                args=(person_id_queue, led1_event, led2_event, led3_event, stop_event), daemon=True)
    door_lock_process.start()

    # temper_sensor_process 관련 코드 제거됨

    while True:
        try:
            if stop_event.is_set():
                break
            sleep(1)
        except KeyboardInterrupt:
            stop_event.set()

    # temper_sensor_process.terminate() 제거됨
    camera_process.terminate()
    recognition_process.terminate()
    sleep(DOOR_SLEEP_TIME)
    door_lock_process.terminate()
