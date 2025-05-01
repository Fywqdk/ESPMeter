print(f'Importing')
from datetime import datetime
import time
import easyocr
import cv2
import numpy as np
import smbclient

print(f'Setting parameters')

# Local data folder
local_folder = '/home/espmeter/data/'
local_file_name = 'espmeter_raw.jpg'

# Define start and endpoint for rectangle covering the value to extract
start_point = (275, 215)
end_point = (600, 310)

# Define contrast and brightness parameters
alpha = 1.0             				# Contrast
beta = 21               				# Brightness
kernel = np.ones((3, 3), np.uint8) 		# kernel

# Threshold for accepting OCR results (int 0-100):
THRESH = 85

print(f'loading OCR')
reader = easyocr.Reader(['en'], gpu=False, quantize=False, verbose=False)

print(f'loading image')
image = cv2.imread(local_folder + local_file_name)



roi = image[start_point[1]:end_point[1], start_point[0]:end_point[0]]

adjusted = cv2.convertScaleAbs(roi, alpha=alpha, beta=beta)

cv2.imwrite(local_folder + f"test/test.jpg", adjusted)

result = reader.recognize(adjusted, allowlist='0123456789')

int_res = int(result[0][1])
conf = round(result[0][2]*100, 2)

print(f'{int_res} - {conf}')


