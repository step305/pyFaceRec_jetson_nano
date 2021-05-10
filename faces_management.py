# import tensorflow as tf
import numpy as np
from parameters import *
# from tensorflow.python.saved_model import tag_constants
import pickle
import cv2
import face_detector
import time
import os
from datetime import datetime, timedelta


class KnownPerson:
    def __init__(self, user_name, user_id, face_image, first_seen=None,
                 first_seen_this_interaction=None, last_seen=None, seen_frames = None, save_cnt=None):
        self.name = user_name
        self.user_id = user_id
        self.user_face = face_image
        if first_seen is None:
            self.first_seen = datetime(1, 1, 1)
        else:
            self.first_seen = first_seen
        if first_seen_this_interaction is None:
            self.first_seen_this_interaction = datetime(1, 1, 1)
        else:
            self.first_seen_this_interaction = first_seen_this_interaction
        if last_seen is None:
            self.last_seen = datetime(1, 1, 1)
        else:
            self.last_seen = last_seen
        if seen_frames is None:
            self.seen_frames = 0
        else:
            self.seen_frames = seen_frames
        if save_cnt is None:
            self.save_cnt = 0
        else:
            self.save_cnt = save_cnt


# def liveness_detector_init():
#     saved_model_loaded = tf.saved_model.load('models/saved_model_TFTRT_FP16', tags=[tag_constants.SERVING])
#     liveness_net = saved_model_loaded.signatures['serving_default']
#     ll = pickle.loads(open('models/le.pickle', "rb").read())
#     liveness_labels = ll.classes_
#     return liveness_net, liveness_labels


# def predict_tftrt(model_infer, face, labels):
#     x = tf.constant(face)
#     labeling = model_infer(x)
#     predictions = labeling['activation_5'].numpy()
#     j = np.argmax(predictions)
#     label = labels[j]
#     return label, predictions[0][j]


def recognition_thread(frame_buffer, person_id_queue, led1_event, led2_event, stop):
    import face_recognition
#     from tensorflow.keras.preprocessing.image import img_to_array

    detector = face_detector.FaceDetector()

    with open("models/trained_knn_model.clf", 'rb') as f:
        face_encodings_database = pickle.load(f)

    authorized_users = {}
    face_cnt = 1
    unknown_faces_save_cnt = FACES_SAVE_INTERVAL

#    if LIVENESS_TEST:
#        liveness_net, liveness_labels = liveness_detector_init()

    for class_dir in os.listdir("media/Faces/"):
        face = cv2.imread(os.path.join("media/Faces/", class_dir, "face_ID.jpg"))
        face = cv2.resize(face, (360, 480))
        f = open(os.path.join("media/Faces/", class_dir, "cardID.txt"), "r")
        ID = int(f.read())
        f.close()

        authorized_users[class_dir] = KnownPerson(user_name=class_dir, user_id=ID, face_image=face)

    print("Loaded ID for {} users".format(len(authorized_users)))

    fps = 0
    fps_max = 10
    t0 = time.time()

    while True:
        if stop.is_set():
            break

        if frame_buffer.empty():
            time.sleep(0.01)
            continue

        door_id, door_frame = frame_buffer.get()
        height, width, channels = door_frame.shape
        rgb_small_rgb = detector.get_rgb_image(door_frame)
        found_faces = detector.detect(rgb_small_rgb)

        now_date = datetime.now()
        faces_save_dir = 'Logs/{}_{}_{}_door_{}'.format(now_date.day, now_date.month, now_date.year, door_id)
        unknown_faces_save_dir = '{}/Unknown'.format(faces_save_dir)
        if not os.path.isdir(faces_save_dir):
            os.mkdir(faces_save_dir)
            os.mkdir(unknown_faces_save_dir)

        found_real_faces = []
        scale_x, scale_y = width / detector.inference_size[0], height / detector.inference_size[1]
        for obj in found_faces:
            bbox = obj.bbox
            x0, y0 = int(bbox.xmin), int(bbox.ymin)
            x1, y1 = int(bbox.xmax), int(bbox.ymax)
            w = x1 - x0
            h = y1 - y0
            x0 = int(x0 + w / 10)
            y0 = int(y0 + h / 4)
            x1 = int(x1 - w / 10)
            y1 = int(y1)
            someone_face = door_frame[int(y0*scale_y):int(y1*scale_y), int(x0*scale_x):int(x1*scale_x)]

#            if LIVENESS_TEST:
#                (label, prob) = predict_tftrt(liveness_net, face, liveness_labels)
#            else:
            label = 'real'
            prob = 1.0

            if (label == 'real') & (prob > 0.85):
                found_real_faces.append((y0, x1, y1, x0))
                if unknown_faces_save_cnt <= 0:
                    if LOG_UNKNOWN_FACES:
                        cv2.imwrite("{}/{}_{}_{}_{}.jpg".format(unknown_faces_save_dir,
                                                                now_date.hour, now_date.minute, now_date.second,
                                                                face_cnt),
                                    someone_face)
                        face_cnt += 1
        if unknown_faces_save_cnt <= 0:
            unknown_faces_save_cnt = FACES_SAVE_INTERVAL
        else:
            unknown_faces_save_cnt -= 1

        if found_real_faces:
            if door_id == 0:
                led1_event.set()
            elif door_id == 1:
                led2_event.set()

            face_encodings = face_recognition.face_encodings(rgb_small_rgb, known_face_locations=found_real_faces)
            closest_distances = face_encodings_database.kneighbors(face_encodings, n_neighbors=1)
            are_matches = [closest_distances[0][i][0] <= 0.5 for i in range(len(found_real_faces))]

            for predicted_user, face_location, found in \
                    zip(face_encodings_database.predict(face_encodings), found_real_faces, are_matches):
                y0, x1, y1, x0 = face_location
                if found:
                    person_found = authorized_users.get(predicted_user)
                    if person_found is not None:
                        if authorized_users[predicted_user].save_cnt <= 0:
                            if LOG_KNOWN_USERS:
                                someone_face = door_frame[y0:y1, x0:x1]
                                user_path = '{}/{}'.format(faces_save_dir, predicted_user)
                                if not os.path.isdir(user_path):
                                    os.mkdir(user_path)
                                cv2.imwrite("{}/{}_{}_{}_{}.jpg".format(user_path,
                                                                        now_date.hour, now_date.minute, now_date.second,
                                                                        face_cnt),
                                            someone_face)
                                face_cnt += 1
                                authorized_users[predicted_user]["save_cnt"] = FACES_SAVE_INTERVAL
                        else:
                            authorized_users[predicted_user].save_cnt -= 1

                        authorized_users[predicted_user].last_seen = datetime.now()

                        if authorized_users[predicted_user].first_seen != datetime(1, 1, 1):
                            authorized_users[predicted_user].seen_frames += 1
                            if datetime.now() - authorized_users[predicted_user].first_seen_this_interaction > \
                                    timedelta(minutes=5):
                                authorized_users[predicted_user].first_seen_this_interaction = datetime.now()
                                authorized_users[predicted_user].seen_frames = 0
                        else:
                            authorized_users[predicted_user].first_seen = datetime.now()
                            authorized_users[predicted_user].first_seen_this_interaction = datetime.now()
                else:
                    if unknown_faces_save_cnt <= 0:
                        if LOG_UNKNOWN_FACES:
                            someone_face = door_frame[y0:y1, x0:x1]
                            cv2.imwrite("{}/{}_{}_{}_{}.jpg".format(unknown_faces_save_dir,
                                                                    now_date.hour, now_date.minute, now_date.second,
                                                                    face_cnt),
                                        someone_face)
                            face_cnt += 1

            if unknown_faces_save_cnt <= 0:
                unknown_faces_save_cnt = FACES_SAVE_INTERVAL
            else:
                unknown_faces_save_cnt -= 1

        visitors_data = []
        for known_user in authorized_users:
            if datetime.now() - authorized_users[known_user].last_seen > timedelta(seconds=ROBUST_SEEN_INTERVAL):
                authorized_users[known_user].seen_frames = 0
            if authorized_users[known_user].seen_frames > ROBUST_SEEN_TIMES:
                visitors_data.append((authorized_users[known_user].name,
                                     authorized_users[known_user].user_id,
                                     authorized_users[known_user].last_seen))
        if len(visitors_data) > 0:
            if person_id_queue.empty():
                person_id_queue.put((door_id, visitors_data))

        if fps == fps_max:
            print('Recognition done in {}ms (average)'.format((time.time() - t0) * 1000 / fps))
            t0 = time.time()
            fps = 0
        else:
            fps += 1
