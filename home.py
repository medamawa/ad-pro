import cv2
import time

import utils.image_utils as image_utils
import utils.home_utils as home_utils

# ホーム画面
def home(window_name, window_size, title_image, background_color):
    # home画面の表示開始時刻を取得
    start_time = time.time()
    background_base = home_utils.make_background(background_color)

    while True:
        # 現在時刻を取得
        now = time.time()

        # 背景画像の生成
        background_image = home_utils.animate_background(background_base, background_color, window_size, (now - start_time))

        press_any_key_image = cv2.imread("src/press_any_key_to_start.png", cv2.IMREAD_UNCHANGED)
        press_any_key_image = image_utils.resize(press_any_key_image, 0.8)

        image_utils.put_image(background_image, title_image, (int(window_size[0]/2), int(window_size[1]/2) - 100))
        image_utils.put_image(background_image, press_any_key_image, (int(window_size[0]/2), int(window_size[1]/2) + 150))
    
        cv2.imshow(window_name, background_image)

        # Enterが押されたら画面を切り替える
        if cv2.waitKey(1) == 13:
            break
