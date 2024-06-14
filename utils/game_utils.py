import cv2
import mediapipe as mp
import numpy as np

import utils.image_utils as image_utils


# 関節のxyz座標を取得する(左上を原点とした絶対座標)
def take_coordinates(coordinates, image):
    '''
    0: 手首
    1: 親指 付け根
    2: 親指 第1関節
    3: 親指 第2関節
    4: 親指 先端
    5: 人差し指 付け根 ***
    6: 人差し指 第1関節
    7: 人差し指 第2関節
    8: 人差し指 先端 ***
    9: 中指 付け根
    10: 中指 第1関節
    11: 中指 第2関節
    12: 中指 先端
    13: 薬指 付け根
    14: 薬指 第1関節
    15: 薬指 第2関節
    16: 薬指 先端
    17: 小指 付け根
    18: 小指 第1関節
    19: 小指 第2関節
    20: 小指 先端
    '''
    if coordinates == None:
        return 0
    
    image_width, image_height = image.shape[1], image.shape[0]
    
    keypoints = []

    for data_point in coordinates:
        xyz_datapoints = data_point.landmark
        for xyz in xyz_datapoints:
            X_value = round(xyz.x * image_width, 2)
            Y_value = round(xyz.y * image_height, 2)
            Z_value = round(xyz.z, 3)
            xyz = [X_value, Y_value, Z_value]
            keypoints.append(xyz)

    return keypoints


# 人差し指の付け根を原点とする相対座標を取得する
def relative_coordinates(keypoints):
    if keypoints == 0:
        return 0
    
    x = keypoints[5][0]
    y = keypoints[5][1]
    z = keypoints[5][2]

    relative_keypoints = []

    for i in range(len(keypoints)):
        relative_keypoints.append([round(keypoints[i][0] - x, 2), round(keypoints[i][1] - y, 2), round(keypoints[i][2] - z, 3)])

    return relative_keypoints


# 打ったかどうか判定
def is_shot(prev_relative_keypoints, relative_keypoints, prev_angle, angle):

    # 一コマのうちに20度以上指を動かしたら撃つと判定する
    if abs(prev_angle) - abs(angle) >= 20:
        return True
    # この判定法はキャリブレーションが必要、、、
    elif abs(prev_angle) < 10 and prev_relative_keypoints[8][1] - relative_keypoints[8][1] >= 10:
        return True
    else:
        return False


# 命中したかどうか判定
def is_hit(keypoints, range_multiplier, target_point, target_size):
    aim_point = get_aim_point(keypoints, range_multiplier)

    # 射線とターゲットの距離が一定範囲内にあれば命中と判定
    if np.linalg.norm(np.array(aim_point) - np.array(target_point)) <= target_size:
        return True
    else:
        return False


# 指定された座標にターゲットを描画する
# point(x, y): ターゲットの中心座標
def put_target(image, point, size):
    # target.pngのサイズをもとに、当たり判定と矛盾がないようにサイズを決めている
    # target.pngのサイズが480×480で、的のサイズが410×410のため、410/480倍している
    # また、半径で指定されているので、直径に変換するために2倍している
    # 変数宣言の括弧の要素"(... ,) * 2"はタプルを2回繰り返すことを示している
    image_size = (int(size*2*480/410),) * 2

    target_image = cv2.imread("src/target.png", cv2.IMREAD_UNCHANGED)
    target_image = cv2.cvtColor(target_image, cv2.COLOR_BGRA2RGBA)
    target_image = cv2.resize(target_image, image_size)

    image_utils.put_image(image, target_image, point)


# 指定された座標にtarget_bangを描画する
# point(x, y): target_bangの中心座標
def put_bang(image, point, size):
    # target.pngのサイズをもとに、当たり判定と矛盾がないようにサイズを決めている
    # target.pngのサイズが480×480で、的のサイズが410×410のため、410/480倍している
    # また、半径で指定されているので、直径に変換するために2倍している
    image_size = (int(size*2*480/410),) * 2

    bang_image = cv2.imread("src/target_bang.png", cv2.IMREAD_UNCHANGED)
    bang_image = cv2.cvtColor(bang_image, cv2.COLOR_BGRA2RGBA)
    bang_image = cv2.resize(bang_image, image_size)

    image_utils.put_image(image, bang_image, point)


# 人差し指の先端と付け根の角度を取得する
def get_angle(relative_keypoints):
    if relative_keypoints == 0:
        return 0

    X = relative_keypoints[8][0]
    Y = relative_keypoints[8][1]

    try:
        m = Y/X
    except ZeroDivisionError:
        m = 0
    
    angle = np.arctan(m) * 180 / (np.pi)

    # 上方向を0度として、-180度から180度の範囲になるように変換
    if X > 0:
        angle = angle + 90
    elif X <= 0:
        angle = angle - 90
    
    return round(angle, 1)


# デバッグ用のグラフィックを描画
def put_debug_info(image, keypoints, relative_keypoints, mp_info, results):
    # 検出された手の骨格をカメラ画像に重ねて描画
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_info[0].draw_landmarks(
                image,
                hand_landmarks,
                mp_info[2].HAND_CONNECTIONS,
                mp_info[1].get_default_hand_landmarks_style(),
                mp_info[1].get_default_hand_connections_style())
    
    # 人差し指の付け根
    point1 = (int((keypoints[5][0])), int((keypoints[5][1])))
    cv2.putText(image, f'// {get_angle(relative_keypoints)}', point1, cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
    # 人差し指の先端
    point2 = (int((keypoints[8][0])), int((keypoints[8][1])))
    cv2.putText(image, f'[{float(relative_keypoints[8][0])}, {float(relative_keypoints[8][1])}, {float(relative_keypoints[8][2])}]', point2, cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 255), 3)


# 射線を描画
def put_aim_line(image, keypoints):
    point1 = (int((keypoints[5][0])), int((keypoints[5][1])))
    aim_point = get_aim_point(keypoints, 3)
    image = cv2.line(image, point1, aim_point, (0, 255, 0), 3)


# 照準位置を取得する(銃身の何倍かを射撃距離とする)
def get_aim_point(keypoints, range_multiplier):
    # 人差し指の付け根
    point1 = (int((keypoints[5][0])), int((keypoints[5][1])))
    # 人差し指の先端
    point2 = (int((keypoints[8][0])), int((keypoints[8][1])))

    aim_point = ((point2[0] - point1[0]) * range_multiplier + point1[0], (point2[1] - point1[1]) * range_multiplier + point1[1])

    return aim_point
