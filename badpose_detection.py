import cv2
import mediapipe as mp
import math
from pydub import AudioSegment
import simpleaudio

sound_file_path = "sound\カーソル移動11.wav"
mp_pose = mp.solutions.pose

class SoundPlayer:
    """SoundPlayer module."""

    @classmethod
    def play(cls, filename, audio_format="mp3", wait=False, stop=False):
        """Play audio file."""

        if stop:
            simpleaudio.stop_all()

        seg = AudioSegment.from_file(filename, audio_format)
        playback = simpleaudio.play_buffer(
            seg.raw_data,
            num_channels=seg.channels,
            bytes_per_sample=seg.sample_width,
            sample_rate=seg.frame_rate
        )

        if wait:
            playback.wait_done()

def calculate_angle(a, b):
    # ベクトルの内積と大きさを計算
    dot_product = a['x'] * b['x'] + a['y'] * b['y'] + a['z'] * b['z']
    magnitude_a = math.sqrt(a['x'] ** 2 + a['y'] ** 2 + a['z'] ** 2)
    magnitude_b = math.sqrt(b['x'] ** 2 + b['y'] ** 2 + b['z'] ** 2)
    angle = math.degrees(math.acos(dot_product / (magnitude_a * magnitude_b)))
    return angle

# Webカメラ入力の場合：
cap = cv2.VideoCapture(0)
fps = cap.get(cv2.CAP_PROP_FPS)
bad_pose_frame_counter = 0

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        frame.flags.writeable = False
        results = pose.process(frame)

        frame.flags.writeable = True
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
            if angle_shoulder_hip > 30:
                print("猫背です")
            
            # 首の判定
            if angle_shoulder_nose > 30:
                print("首が前に出ています")
            
            # 猫背と首の判定
            if angle_shoulder_hip > 30 and angle_shoulder_nose > 30:
                print("猫背で首が前に出ています")
                bad_pose_frame_counter = bad_pose_frame_counter + 1
                SoundPlayer.play(sound_file_path, audio_format="wav")

        cv2.imshow('MediaPipe Pose', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
print(f"姿勢の悪かった時間 : {bad_pose_frame_counter/fps}")