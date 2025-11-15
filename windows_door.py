# door_management.py (윈도우 PC 테스트용)
import face_recognition
import pickle
import cv2
# import serial # PC 테스트에서는 주석 처리 (Jetson에서만 사용)
import time

print("[정보] 정답지(encodings.pickle)를 불러오는 중...")
data = pickle.loads(open("encodings.pickle", "rb").read())

# --- Jetson/Serial 관련 코드 주석 처리 ---
# print("[정보] 시리얼 포트 연결 중...")
# try:
#     ser = serial.Serial('COM3', 9600) 
#     print("시리얼 포트 연결 성공.")
# except Exception as e:
#     print(f"시리얼 포트 연결 실패: {e}")
#     ser = None
# --- 여기까지 ---

print("[정보] 카메라를 켭니다...")
cap = cv2.VideoCapture(0) # 0번 카메라 (PC 웹캠)

last_access_time = 0 
ACCESS_DELAY = 5.0 # 5초 딜레이

while True:
    ret, frame = cap.read()
    if not ret:
        print("오류: 프레임을 읽을 수 없습니다.")
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb, model="hog")
    encodings = face_recognition.face_encodings(rgb, boxes)
    names = [] 

    for encoding in encodings:
        matches = face_recognition.compare_faces(data["encodings"], encoding)
        name = "Unknown" 

        if True in matches:
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}
            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1
            name = max(counts, key=counts.get)

        names.append(name)

    current_time = time.time()
    access_granted = False

    if any(name != "Unknown" for name in names) and (current_time - last_access_time > ACCESS_DELAY):
        recognized_name = [name for name in names if name != "Unknown"][0]

        # --- PC 테스트용 출력 ---
        print(f"[인증 성공] {recognized_name} 님! 문을 엽니다. (PC 테스트)")
        # --- 젯슨 코드 주석 처리 ---
        # if ser:
        #     ser.write(b'OPEN') # 'OPEN' 신호를 보냄

        last_access_time = current_time 
        access_granted = True

    for ((top, right, bottom, left), name) in zip(boxes, names):
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        if access_granted and name != "Unknown":
            color = (255, 0, 0)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, color, 2)

    cv2.imshow("Door Management System (PC Test)", frame)

    if cv2.waitKey(1) == ord('q'):
        break

print("[정보] 시스템을 종료합니다.")
cap.release()
cv2.destroyAllWindows()
# if ser:
#     ser.close()