🚀 젯슨 나노 기반 실시간 얼굴 인식 출입 통제 시스템 📸
OOTD 캡스톤 디자인 프로젝트 (팀원: 김서윤 , 박서연, 장지은)

실시간 카메라 영상에서 얼굴을 탐지 및 인식하여, 등록된 사용자일 경우 ⚡️출입문(하드웨어)을 제어⚡️하는 End-to-End 프로토타입입니다.

🔑 주요 기능
✨ 실시간 얼굴 인식: 젯슨 나노에 최적화된 HOG (빠른 탐지) + ResNet (정확한 인식) 모델 사용

👥 다중 사용자 관리: dataset 폴더 구조를 통해 100명 이상의 사용자도 쉽게 등록, 학습 및 관리

🤖 하드웨어 제어: Jetson.GPIO 및 pyserial을 사용하여 도어락 🔐, LED 💡 등 외부 하드웨어와 연동

🎯 높은 정확도: tolerance=0.5 (엄격한 기준) 설정 및 '비교 데이터셋' 확보로 인식 신뢰도 향상

🛠 젯슨 나노 환경 구축 (Installation)
본 프로젝트는 NVIDIA Jetson Nano (JetPack 4.6.1) 🤖 환경을 기준으로 합니다.

NVIDIA Jetson Nano에 JetPack 4.6.1을 설치합니다. (SD 카드 Flashing)

본 프로젝트를 git clone 하거나 USB로 복사합니다.

Bash

git clone [우리 깃허브 레포지토리 주소]
cd pyFaceRec_jetson_nano
필수 라이브러리를 젯슨 보드 터미널에 설치합니다. ⌨️

Bash

# 1. 시스템 업데이트 및 pip3 설치
sudo apt-get update
sudo apt-get install python3-pip

# 2. 캡스톤 필수 라이브러리 5가지
sudo pip3 install face_recognition
sudo pip3 install opencv-python
sudo pip3 install pyserial
sudo pip3 install Jetson.GPIO
sudo pip3 install imutils


⚙️ 사용 방법 (How to Use)
1. (수동) 🖼️ 얼굴 데이터셋 준비
프로젝트 루트에 dataset 폴더를 생성합니다.

인식할 사람의 이름으로 하위 폴더를 생성합니다. (예: dataset/person_A, dataset/person_B)

각 하위 폴더에 다양한 각도와 표정의 얼굴 사진을 10~15장 이상 저장합니다. (💡 신뢰도 향상을 위해 3명 이상, 폴더 3개 이상 권장!)

2. (자동) 🧠 얼굴 학습 (AI 정답지 생성)
dataset 준비가 완료되면, encode_faces.py 스크립트를 실행하여 얼굴 특징을 추출합니다. (encodings.pickle 파일 생성)

Bash

# 젯슨 터미널에서 실행
python3 encode_faces.py
(🚨 데이터셋에 사진을 추가/삭제/변경할 때마다 이 명령어를 다시 실행해야 합니다.)

3. (자동) 🟢 실시간 인식 및 출입 제어 실행
젯슨 보드에 카메라를 연결하고, 메인 프로그램을 실행합니다.

Bash

# 젯슨 터미널에서 실행
python3 door_management.py
q 키를 누르면 프로그램이 종료됩니다.

📁 폴더 구조
.
├── 📂 dataset/              # 1. (생성 필요) 얼굴 학습용 데이터
│   ├── 🧑 person_A/
│   │   ├── 1.jpg
│   │   └── ...
│   └── 👩 person_B/
├── 📜 encode_faces.py       # 2. 얼굴 학습(인코딩) 스크립트
├── 📜 door_management.py    # 3. 실시간 인식 및 도어락 제어 스크립트
├── 🧠 encodings.pickle      # 4. (자동 생성) AI 정답지
├── 📜 test_camera_jetson.py # (선택) 젯슨 카메라 테스트용
└── 📄 README.md             # (현재 파일)



1. Prepare Jetson Nano.
2. chmod +x RTSP_server_build.sh
2a. chmod +x start_Door.sh
3. ./RTSP_server_build.sh
4. USB camera should be in /dev/video0
5. USB Coral should be connected
6. run with ./start_Door.sh
