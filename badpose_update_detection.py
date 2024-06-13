import cv2
import mediapipe as mp
import math
from pygame import mixer

sound_of_bad_posture = "sound\sound_of_bad_posture.mp3"
sound_of_good_posture = "sound\sound_of_good_posture.mp3"

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def calculate_angle(a, b):
    # ベクトルの内積と大きさを計算
    dot_product = a['x'] * b['x'] + a['y'] * b['y'] + a['z'] * b['z']
    magnitude_a = math.sqrt(a['x'] ** 2 + a['y'] ** 2 + a['z'] ** 2)
    magnitude_b = math.sqrt(b['x'] ** 2 + b['y'] ** 2 + b['z'] ** 2)
    angle = math.degrees(math.acos(dot_product / (magnitude_a * magnitude_b)))
    return angle

# 状態を記録する変数
prev_posture_state = None

# Webカメラ入力の場合：
cap = cv2.VideoCapture(0)
fps = cap.get(cv2.CAP_PROP_FPS)
input_wait_time = 1                             # 入力を何ms待つか
good_posture_frame_counter = 0                   # 姿勢の良かったフレームの数
bad_posture_frame_counter = 0                   # 姿勢の悪かったフレームの数
one_frame_second = 1/fps + input_wait_time/1000 # 1フレームあたりの時間/s

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        frame.flags.writeable = False
        results = pose.process(frame)

        # 画像にポーズアノテーションを描画
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        if results.pose_landmarks:
            # ランドマークの取得
            nose = results.pose_landmarks.landmark[0]
            left_shoulder = results.pose_landmarks.landmark[11]
            right_shoulder = results.pose_landmarks.landmark[12]
            left_hip = results.pose_landmarks.landmark[23]
            right_hip = results.pose_landmarks.landmark[24]

            # 肩の中間点の計算
            mid_shoulder = {
                'x': (left_shoulder.x + right_shoulder.x) / 2,
                'y': (left_shoulder.y + right_shoulder.y) / 2,
                'z': (left_shoulder.z + right_shoulder.z) / 2
            }

            # 腰の中間点の計算
            mid_hip = {
                'x': (left_hip.x + right_hip.x) / 2,
                'y': (left_hip.y + right_hip.y) / 2,
                'z': (left_hip.z + right_hip.z) / 2
            }

            # ベクトルの計算
            shoulder_to_hip = {
                'x': mid_hip['x'] - mid_shoulder['x'],
                'y': mid_hip['y'] - mid_shoulder['y'],
                'z': mid_hip['z'] - mid_shoulder['z']
            }

            shoulder_to_nose = {
                'x': nose.x - mid_shoulder['x'],
                'y': nose.y - mid_shoulder['y'],
                'z': nose.z - mid_shoulder['z']
            }

            # 垂直方向のベクトル
            vertical = {
                'x': 0,
                'y': 1,
                'z': 0
            }

            # 角度の計算
            angle_shoulder_hip = calculate_angle(shoulder_to_hip, vertical)
            angle_shoulder_nose = calculate_angle(shoulder_to_nose, vertical)

            # 猫背の判定
            # 猫背の角度を設定
            current_posture_state = {
                'is_hunched': angle_shoulder_hip > 30,
            }

            # 状態が変化した場合のみ出力
            if current_posture_state != prev_posture_state:
                if current_posture_state['is_hunched']:
                    print("猫背です")
                    mixer.init()
                    mixer.music.load(sound_of_bad_posture)
                    mixer.music.play()
                    
                if not current_posture_state['is_hunched']:
                    print("良い姿勢です")
                    mixer.init()
                    mixer.music.load(sound_of_good_posture)
                    mixer.music.play()

                prev_posture_state = current_posture_state
        
        # 姿勢が良かった時間
        if  not current_posture_state['is_hunched']:
            good_posture_frame_counter = good_posture_frame_counter + 1
            
        # 姿勢が悪かった時間
        if current_posture_state['is_hunched']:
            bad_posture_frame_counter = bad_posture_frame_counter + 1
            
        # 姿勢が良かった時間の割合(%)
        good_posture_ratio = 0
        
        total_frames = good_posture_frame_counter + bad_posture_frame_counter
        if total_frames > 0:
            good_posture_ratio = (good_posture_frame_counter / total_frames) * 100
        else:
            good_posture_ratio = 0
            
        # 秒数を分に変換する関数
        def convert_minutes(seconds):
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return minutes, remaining_seconds

        cv2.imshow('MediaPipe Pose', frame)
        k = cv2.waitKey(input_wait_time)
        if k == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
if good_posture_frame_counter*one_frame_second >= 60:
    good_posture_minutes, good_posture_seconds = convert_minutes(good_posture_frame_counter * one_frame_second)
    print(f"姿勢が良かった時間 : {good_posture_minutes:.0f}分 {good_posture_seconds:.0f}秒")
else:
    print(f"姿勢が良かった時間 : {good_posture_frame_counter*one_frame_second:.0f}秒")
    
if bad_posture_frame_counter*one_frame_second >= 60:
    bad_posture_minutes, bad_posture_seconds = convert_minutes(bad_posture_frame_counter * one_frame_second)
    print(f"姿勢が悪かった時間 : {bad_posture_minutes:.0f}分 {bad_posture_seconds:.0f}秒")
else:
    print(f"姿勢が悪かった時間 : {bad_posture_frame_counter*one_frame_second:.0f}秒")

print(f"姿勢が良かった時間の割合 : {good_posture_ratio:.0f}%")
