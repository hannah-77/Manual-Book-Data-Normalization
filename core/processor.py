import cv2
import numpy as np

def clean_medical_element(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return

    # Konversi ke HSV untuk deteksi warna merah yang akurat
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Range warna Merah
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 50, 50])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    # Dilation untuk memastikan pinggiran stempel juga terhapus
    kernel = np.ones((3,3), np.uint8)
    red_mask = cv2.dilate(red_mask, kernel, iterations=1)

    # Ubah area merah menjadi putih
    img[red_mask > 0] = [255, 255, 255]
    cv2.imwrite(img_path, img)