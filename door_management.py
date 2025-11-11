# door_management.py (최종 젯슨 보드용)

import face_recognition
import pickle
import cv2
import time
import serial       # 1. 도어락 제어용 (내일 젯슨에 'sudo pip3 install pyserial' 설치 필요)
import Jetson.GPIO as GPIO # 2. 젯슨 하드웨어 제어용 (내일 'sudo pip3 install Jetson.GPIO' 설치 필요)

# --- 젯슨 하드웨어 설정 ---
# (이 부분은 내일 실제 도어락/LED 연결하고 수정)
DOOR_PIN = 18 # 젯슨 보드의 BOARD 핀 번호 (예시)
GPIO.setmode(GPIO.BOARD) # 핀 번호 기준 설정
GPIO.setup(DOOR_PIN, GPIO.OUT, initial=GPIO.LOW) # 핀을 출력으로 설정

# (이 부분은 내일 도어락 아두이노 연결 포트 확인)
SERIAL_PORT = '/dev/ttyUSB0' # 젯슨(리눅스)의 USB 포트 이름 (윈도우의 'COM3'와 다름)
BAUD_RATE = 9600

# try:
#     ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
#     print(f"[정보] 시리얼 포트({SERIAL_PORT}) 연결 성공.")
# except Exception as e:
#     print(f"[오류] 시리얼 포트 연결 실패: {e}")
#     ser = None
# (위 시리얼 코드는 일단 주석 처리. 내일 아두이노 연결 후 테스트)
# --- 하드웨어 설정 끝 ---


# --- 젯슨 나노 카메라 최적화 함수 ---
# (그냥 cv2.VideoCapture(0)보다 젯슨 전용 GStreamer가 10배 빠름)
def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    display_width=640,  # 인식에 사용할 해상도 (줄이면 속도 향상)
    display_height=360, # 인식에 사용할 해상도 (줄이면 속도 향상)
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
# --- 카메라 설정 끝 ---


print("[정보] 정답지(encodings.pickle)를 불러오는 중...")
data = pickle.loads(open("encodings.pickle", "rb").read())

print("[정보] 젯슨 카메라(GStreamer)를 켭니다...")
# cap = cv2.VideoCapture(0) # (윈도우 방식 - 느림)
cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER) # (젯슨 방식 - 빠름)

if not cap.isOpened():
    print("[오류] 젯슨 카메라를 켤 수 없습니다.")
    exit()

print("[정보] 실시간 얼굴 인식을 시작합니다. ('q' 키 누르면 종료)")

last_access_time = 0 
ACCESS_DELAY = 5.0 # 인증 딜레이 (초)

while True:
    ret, frame = cap.read()
    if not ret:
        print("[오류] 카메라 프레임을 읽을 수 없습니다.")
        break

    # (중요) 실시간 인식을 위해 BGR -> RGB 변환
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 1. 실시간 영상에서 얼굴 찾기
    boxes = face_recognition.face_locations(rgb, model="hog")
    # 2. 찾은 얼굴을 벡터로 변환
    encodings = face_recognition.face_encodings(rgb, boxes)

    names = [] # 현재 프레임에서 인식된 사람들

    # 3. 찾은 얼굴들을 '정답지'와 비교
    for encoding in encodings:
        # (★개선점) 'tolerance=0.5' (기본값 0.6)
        # 0.5로 기준을 더 엄격하게 만들어 '모두를 사용자라고 인식'하는 문제 해결
        matches = face_recognition.compare_faces(
            data["encodings"], encoding, tolerance=0.5
        )
        name = "Unknown" # 기본값

        if True in matches:
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}
            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1
            name = max(counts, key=counts.get) # 가장 많이 매칭된 이름 선택
        
        names.append(name)

    # 4. 도어락 제어 로직
    current_time = time.time()
    access_granted = False
    
    # 만약 'Unknown'이 아닌 사람(등록된 사람)이 있고,
    # 마지막 인증 후 5초가 지났다면
    if any(name != "Unknown" for name in names) and (current_time - last_access_time > ACCESS_DELAY):
        recognized_name = [name for name in names if name != "Unknown"][0]
        
        print(f"[인증 성공] {recognized_name} 님! 문을 엽니다.")
        
        # (★최종) 젯슨 하드웨어 제어!
        GPIO.output(DOOR_PIN, GPIO.HIGH) # 1. 핀에 HIGH 신호 전송 (LED 켜기/릴레이 작동)
        # if ser:
        #     ser.write(b'OPEN') # 2. 시리얼로 'OPEN' 신호 전송 (아두이노)
            
        last_access_time = current_time # 마지막 인증 시간 업데이트
        access_granted = True
        
        # 0.5초 후에 핀을 다시 LOW로 (문 닫힘 신호 또는 LED 끄기)
        # (이 부분은 나중에 'time.sleep' 대신 다른 방식으로 바꿔야 할 수도 있음)
        time.sleep(0.5) 
        GPIO.output(DOOR_PIN, GPIO.LOW)

    # 5. 화면에 결과 표시
    for ((top, right, bottom, left), name) in zip(boxes, names):
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        if access_granted and name != "Unknown":
            color = (255, 0, 0) # 방금 인증됐으면 파란색

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, color, 2)

    cv2.imshow("Door Management System (Jetson)", frame)

    if cv2.waitKey(1) == ord('q'):
        break

# 6. 종료 및 자원 해제
print("[정보] 시스템을 종료합니다.")
cap.release()
cv2.destroyAllWindows()
GPIO.cleanup() # GPIO 핀 초기화
# if ser:
#     ser.close()