# test_camera_jetson.py
import cv2

# 위 2단계 코드에서 복사해 온 GStreamer 함수
def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    display_width=640,
    display_height=360,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d !"
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 !"
        "nvvidconv flip-method=%d !"
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx !"
        "videoconvert !"
        "video/x-raw, format=(string)BGR !"
        "appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

print("[정보] 젯슨 카메라(GStreamer) 테스트를 시작합니다...")
cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("[오류] 젯슨 카메라를 켤 수 없습니다.")
else:
    print("[성공] 카메라가 켜졌습니다. 'q' 키를 누르면 종료됩니다.")
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow("Jetson Camera Test", frame)
            if cv2.waitKey(1) == ord('q'):
                break
        else:
            print("[오류] 프레임을 읽을 수 없습니다.")
            break

cap.release()
cv2.destroyAllWindows()