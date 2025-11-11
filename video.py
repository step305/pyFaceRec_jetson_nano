import cv2
import time
import numpy as np
import os
from parameters import *


def transform_frame(temp_image, empty_frame):
    pre_frame = empty_frame
    angle = 110
    (he, we, c) = empty_frame.shape
    empty_frame_yc = int(he / 2)
    empty_frame_xc = int(we / 2)
    (h, w, c) = temp_image.shape
    half_h = int(h / 2)
    half_w = int(w / 2)
    pre_frame[empty_frame_yc - half_h:empty_frame_yc + half_h,
              empty_frame_xc - half_w:empty_frame_xc + half_w, :] = temp_image

    transformation_matrix = cv2.getRotationMatrix2D((empty_frame_xc, empty_frame_yc), angle, 1)
    transformed_image = cv2.warpAffine(pre_frame, transformation_matrix, (we, he))
    return transformed_image


def cam_thread(door_id, frame_buffer, led_event, stop): # temper_queue 인자 제거
    door_stream_port = DOOR_STREAM_PORTS[door_id]
    door_rtsp_port = DOOR_RTSP_PORTS[door_id]
    window_name = 'FaceRec'

    if USB_CAMERA_FORMAT == 'NV12':
        capture_pipeline = (
            'v4l2src device={} do-timestamp=true ! '
            'video/x-raw, width=1920, height=1080, framerate={}/1, format=NV12 ! '
            'videoscale ! video/x-raw, width={}, height={}, format=NV12 ! '
            'videoconvert ! video/x-raw, format=BGR ! '
            'appsink'.format(USB_CAMERA, USB_CAMERA_FPS, USB_CAMERA_FRAME_SHAPE[0], USB_CAMERA_FRAME_SHAPE[1])
        )
    elif USB_CAMERA_FORMAT == 'MJPEG':
        capture_pipeline = (
            'v4l2src device={} ! '
            'image/jpeg, width={}, height={}, framerate={}/1, format=MJPG ! '
            'jpegparse ! jpegdec ! videoconvert ! video/x-raw, format=BGR ! '
            'appsink'.format(USB_CAMERA, USB_CAMERA_FRAME_SHAPE[0], USB_CAMERA_FRAME_SHAPE[1], USB_CAMERA_FPS)
        )
    else:
        print('Error! Wrong USB camera format!')
        return

    cam = cv2.VideoCapture(capture_pipeline, cv2.CAP_GSTREAMER)

    writer_pipeline = (
        'appsrc ! videoconvert ! video/x-raw, format=NV12 ! '
        'nvvidconv ! video/x-raw(memory:NVMM), width={}, height={}, format=NV12 ! '
        'nvv4l2h265enc bitrate={} maxperf-enable=1 '
        'preset-level=1 insert-sps-pps=1 profile=1 iframeinterval=1 ! '
        'h265parse ! rtph265pay ! udpsink host=127.0.0.1 '
        'port={} async=0 sync=0'.format(VIDEO_OUT_FRAME_SHAPE[0], VIDEO_OUT_FRAME_SHAPE[1],
                                        VIDEO_OUT_BITRATE, door_stream_port)
    )
    disp_pipeline = (
        'appsrc ! videoconvert ! video/x-raw, format=RGBA ! '	
        'nvvidconv ! nvegltransform ! nveglglessink'
    )

    disp_writer = cv2.VideoWriter(disp_pipeline, cv2.CAP_GSTREAMER, 0, 30, (VIDEO_OUT_FRAME_SHAPE[0], VIDEO_OUT_FRAME_SHAPE[1]))

    udp_writer = cv2.VideoWriter(writer_pipeline, cv2.CAP_GSTREAMER, 0, 30, (VIDEO_OUT_FRAME_SHAPE[0], VIDEO_OUT_FRAME_SHAPE[1]))

    mask = cv2.imread('media/mask.jpg', 0)
    mask = cv2.resize(mask, (DISPLAY_SIZE[0], DISPLAY_SIZE[1]))
    Logo = cv2.imread('media/logo.jpg')
    Logo = cv2.resize(Logo, (DISPLAY_SIZE[0], DISPLAY_SIZE[1]))
    screen_saver = cv2.VideoCapture('media/clip.mp4')
    print('Load camera process...')

    final_w = DISPLAY_SIZE[0]
    final_h = DISPLAY_SIZE[1]
    final_frame_cam_frame_x0 = 0
    black_frame = np.zeros((final_h, final_h, 3), np.uint8)
    final_frame = np.zeros((final_h, final_w, 3), np.uint8)
    aspect_x = ASPECT_RATIO[0]
    aspect_y = ASPECT_RATIO[1]
    diag = int(np.sqrt(aspect_x ** 2 + aspect_y ** 2))
    step = int(final_h / diag) - 1
    cam_resize_x = step * aspect_x
    cam_resize_y = step * aspect_y

    time.sleep(10)
    print('Loaded camera process! Press q to quit.')

    os.system('./RTSPserver inPort:{} outPort:{} &'.format(door_stream_port, door_rtsp_port))

    if SHOW_ON_DISPLAY:
        os.system('xrandr -o normal')
        os.system('v4l2-ctl -d {} -c zoom_absolute=160'.format(USB_CAM_NUM))
        os.system('v4l2-ctl -d {} -c pan_absolute=0'.format(USB_CAM_NUM))
        os.system('v4l2-ctl -d {} -c tilt_absolute=0'.format(USB_CAM_NUM))
        os.system('v4l2-ctl -d {} -c brightness=140'.format(USB_CAM_NUM))
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    t0 = time.monotonic()
    frames_cnt = 0
    skip_frames = SKIP_FRAMES_MAX
    time2screen_off = time.time()
    saver_frame_counter = 0
    # temper_str = '' 온도 관련 변수 제거
    # temper_str_color = (0, 255, 0) 온도 관련 변수 제거
    # temper_str_expire = time.time() 온도 관련 변수 제거

    while True:
        ret, frame = cam.read()
        if not ret:
            continue

        if frame_buffer.empty():
            if skip_frames == 0:
                small_frame = cv2.resize(frame, (FRAME_SIZE_FOR_DNN[0], FRAME_SIZE_FOR_DNN[1]))
                if not frame_buffer.full():
                    frame_buffer.put((door_id, small_frame))
                    skip_frames = SKIP_FRAMES_MAX
            else:
                skip_frames -= 1

        now_time = time.time()

        if led_event.is_set():
            led_event.clear()
            time2screen_off = now_time + ACTIVE_REMAIN_TIME

        if time2screen_off < (now_time + 1):
            rr, frame_saver = screen_saver.read()
            saver_frame_counter += 1
            if saver_frame_counter == screen_saver.get(cv2.CAP_PROP_FRAME_COUNT):
                saver_frame_counter = 0  # Or whatever as long as it is the same as next line
                screen_saver.set(cv2.CAP_PROP_POS_FRAMES, 0)
            time.sleep(1.0 / 50.0)
            frame = frame_saver

        # --- 온도 관련 코드 제거 시작 ---
        # if not temper_queue.empty():
        #     (ta, to1) = temper_queue.get()
        #     temper_str = 'TA = {:0.1f}: To = {"0.1f}'.format(ta, to1)
        #     if to1 < 37:
        #         temper_str_color = (0, 255, 0)
        #     else:
        #         temper_str_color = (0, 0, 255)
        #     temper_str_expire = time.time() + ACTIVE_REMAIN_TIME
        # if temper_str_expire > time.time():
        #     frame = cv2.putText(final_frame, temper_str, (50, 600), cv2.FONT_HERSHEY_SIMPLEX, 1,
        #                         color=temper_str_color,
        #                         thickness=2)
        # --- 온도 관련 코드 제거 끝 ---

        rot_frame = cv2.resize(frame, (cam_resize_x, cam_resize_y))
        rot_frame = cv2.flip(rot_frame, 1)
        rot_frame = transform_frame(rot_frame, black_frame)
        final_frame[0:final_h,
                    final_frame_cam_frame_x0:final_frame_cam_frame_x0 + final_h - FINAL_FRAME_DELTA_MINUS] = \
            rot_frame[:, FINAL_FRAME_DELTA_MINUS:]

        final_frame = cv2.bitwise_and(final_frame, final_frame, mask=mask)
        final_frame = cv2.bitwise_or(final_frame, Logo)
        final_frame = cv2.flip(final_frame, -1)

        if SHOW_ON_DISPLAY:
            film_frame = cv2.resize(final_frame, (1680, 1050))
            #disp_writer.write(final_frame)
            cv2.imshow(window_name, film_frame)

        udp_frame = cv2.resize(final_frame, (VIDEO_OUT_FRAME_SHAPE[0], VIDEO_OUT_FRAME_SHAPE[1]))
        udp_writer.write(udp_frame)

        frames_cnt += 1
        if frames_cnt >= 60:
            t1 = time.monotonic()
            print('Video FPS={:.1f}'.format(frames_cnt / (t1 - t0)))
            frames_cnt = 0
            t0 = t1

        if SHOW_ON_DISPLAY:
            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                stop.set()
                break
        if stop.is_set():
            break

    cam.release()
    screen_saver.release()
    os.system('pkill RTSPserver')
    if SHOW_ON_DISPLAY:
        cv2.destroyAllWindows()
