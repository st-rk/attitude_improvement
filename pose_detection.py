import cv2
import mediapipe as mp
import matplotlib.pyplot as plt

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Webカメラ入力の場合：
cap = cv2.VideoCapture(0)

# 出力用設定
output_path = "test_video_.mp4"
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
size = (width, height)
frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
fmt = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
writer = cv2.VideoWriter(output_path, fmt, frame_rate, size)

# 右足首の奥行座標を入れるリスト
z_list = []

with mp_pose.Pose(min_detection_confidence=0.5,
                    min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # ビデオをロードする場合は、「continue」ではなく「break」を使用してください
            continue

        # 後で自分撮りビューを表示するために画像を水平方向に反転し、BGR画像をRGBに変換
        frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        # パフォーマンスを向上させるには、オプションで、参照渡しのためにイメージを書き込み不可としてマーク
        frame.flags.writeable = False
        results = pose.process(frame)   # 推論処理

        # 画像にポーズアノテーションを描画
        frame.flags.writeable = True
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.imshow('MediaPipe Pose', frame)
        
        # 動画書き込み
        writer.write(frame)

        # キー入力を1ms待って、k が113（q）だったらBreakする
        k = cv2.waitKey(1)
        if k == 113:
            break

        # 右足首の座標取得
        if results.pose_landmarks != None:
            right_ankle_vec = results.pose_landmarks.landmark[27]
            print(right_ankle_vec)
            z_list.append(right_ankle_vec.z)
        else:
            print("None Landmarks")
            z_list.append(-1)
        print("-------------------")

writer.release()
cap.release()
cv2.destroyAllWindows()

# 奥行座標のグラフ
#plt.plot(z_list)
#plt.savefig(f"right_ankle_z_coor.png")
#plt.show()
