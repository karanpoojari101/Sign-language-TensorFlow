import cv2
import numpy as np
import time
import getpass
import os
i=165

getUser = getpass.getuser()
save = 'C:/Users/' + getUser + "/Desktop/images/C"

vc = cv2.VideoCapture(0)

if vc.isOpened(): # try to get the first frame
    rval, frame = vc.read()
else:
    rval = False

while rval:
    cv2.imshow("preview", frame)
    rval, frame = vc.read()
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break
    elif key%256 == 32:
        # SPACE pressed
        img_name = "opencv_frame_{}.png"
        cv2.imwrite(img_name, frame)
        print("{} written!".format(img_name))
        name= "C"+str(i)
        crop_img = frame[100:400, 100:400]
        crop_img1 = masking(crop_img)
        hsv = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)
        lower = np.array([0, 48, 80], dtype = "uint8")
        upper = np.array([20, 255, 255], dtype = "uint8")
        # Threshold the HSV image to get only blue colors
        mask = cv2.inRange(hsv, lower, upper)
        # Bitwise-AND mask and original image
        result = cv2.bitwise_and(crop_img,crop_img, mask= mask)
        cv2.imwrite(os.path.join(save, name+".png"), result)
        i=i+1
    else:
        cv2.rectangle(img=frame, pt1=(100, 100), pt2=(400, 400), color=(255, 0, 0), thickness=5, lineType=8, shift=0)

vc.release()
cv2.destroyAllWindows() 