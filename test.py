# test.py

import os
import tensorflow as tf
import numpy as np
import cv2

# module-level variables ##############################################################################################
RETRAINED_LABELS_TXT_FILE_LOC = os.getcwd() + "/" + "retrained_labels.txt"
RETRAINED_GRAPH_PB_FILE_LOC = os.getcwd() + "/" + "retrained_graph.pb"

TEST_IMAGES_DIR = os.getcwd() + "/test_images"

SCALAR_RED = (0.0, 0.0, 255.0)
SCALAR_BLUE = (255.0, 0.0, 0.0)

#######################################################################################################################
def main():
    print("starting program . . .")

    if not checkIfNecessaryPathsAndFilesExist():
        return
    # end if

    # get a list of classifications from the labels file
    classifications = []
    # for each line in the label file . . .
    for currentLine in tf.gfile.GFile(RETRAINED_LABELS_TXT_FILE_LOC):
        # remove the carriage return
        classification = currentLine.rstrip()
        # and append to the list
        classifications.append(classification)
    # end for

    # show the classifications to prove out that we were able to read the label file successfully
    print("classifications = " + str(classifications))

    # load the graph from file
    with tf.gfile.FastGFile(RETRAINED_GRAPH_PB_FILE_LOC, 'rb') as retrainedGraphFile:
        # instantiate a GraphDef object
        graphDef = tf.GraphDef()
        # read in retrained graph into the GraphDef object
        graphDef.ParseFromString(retrainedGraphFile.read())
        # import the graph into the current default Graph, note that we don't need to be concerned with the return value
        _ = tf.import_graph_def(graphDef, name='')
    # end with

    # if the test image directory listed above is not valid, show an error message and bail
    if not os.path.isdir(TEST_IMAGES_DIR):
        print("the test image directory does not seem to be a valid directory, check file / directory paths")
        return
    # end if
    
    # camera code by karan
    cv2.namedWindow('preview',cv2.WINDOW_NORMAL)

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
            img_name = "CapturedImg.png"
            cv2.imwrite(img_name, frame)
            print(" written!".format(img_name))
            break
        else:
            cv2.rectangle(img=frame, pt1=(100, 100), pt2=(400, 400), color=(255, 0, 0), thickness=5, lineType=8, shift=0)

    vc.release()
    cv2.destroyAllWindows()
    
    crop_img = frame[100:400, 100:400]
    #cv2.imshow("cropped", crop_img)
    crop_img1 = masking(crop_img)
    hsv = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)
    lower = np.array([0, 48, 80], dtype = "uint8")
    upper = np.array([20, 255, 255], dtype = "uint8")
    # Threshold the HSV image to get only blue colors
    mask = cv2.inRange(hsv, lower, upper)
    # Bitwise-AND mask and original image
    result = cv2.bitwise_and(crop_img,crop_img, mask= mask)
    cv2.imshow("cropped", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    with tf.Session() as sess:
        # for each file in the test images directory . . .
        #for fileName in os.listdir(TEST_IMAGES_DIR):
            # if the file does not end in .jpg or .jpeg (case-insensitive), continue with the next iteration of the for loop
           # if not (fileName.lower().endswith(".png")):
              #  continue
            # end if

            # show the file name on std out
           # print(fileName)

            # get the file name and full path of the current image file
            #imageFileWithPath = os.path.join(TEST_IMAGES_DIR, fileName)
            # attempt to open the image with OpenCV
            #openCVImage = cv2.imread(imageFileWithPath)

            # if we were not able to successfully open the image, continue with the next iteration of the for loop
            #if openCVImage is None:
               # print("unable to open " + fileName + " as an OpenCV image")
               # continue
            # end if

            # get the final tensor from the graph
            finalTensor = sess.graph.get_tensor_by_name('final_result:0')

            # convert the OpenCV image (numpy array) to a TensorFlow image
            tfImage = np.array(result)[:, :, 0:3]
        
            
            # run the network to get the predictions
            
            predictions = sess.run(finalTensor, {'DecodeJpeg:0': tfImage})
            print(predictions)

            # sort predictions from most confidence to least confidence
            sortedPredictions = predictions[0].argsort()[-len(predictions[0]):][::-1]
           

            print("---------------------------------------")

            # keep track of if we're going through the next for loop for the first time so we can show more info about
            # the first prediction, which is the most likely prediction (they were sorted descending above)
            onMostLikelyPrediction = True
            # for each prediction . . .
            for prediction in sortedPredictions:
                strClassification = classifications[prediction]

                # if the classification (obtained from the directory name) ends with the letter "s", remove the "s" to change from plural to singular
                if strClassification.endswith("s"):
                    strClassification = strClassification[:-1]
                # end if

                # get confidence, then get confidence rounded to 2 places after the decimal
                confidence = predictions[0][prediction]

                # if we're on the first (most likely) prediction, state what the object appears to be and show a % confidence to two decimal places
                if onMostLikelyPrediction:
                    # get the score as a %
                    scoreAsAPercent = confidence * 100.0
                    # show the result to std out
                    print("the object appears to be a " + strClassification + ", " + "{0:.2f}".format(scoreAsAPercent) + "% confidence")
                    # write the result on the image
                    writeResultOnImage(crop_img, strClassification + ", " + "{0:.2f}".format(scoreAsAPercent) + "% confidence")
                    # finally we can show the OpenCV image
                    cv2.imshow("Captured_image", crop_img)
                    # mark that we've show the most likely prediction at this point so the additional information in
                    # this if statement does not show again for this image
                    onMostLikelyPrediction = False
                # end if

                # for any prediction, show the confidence as a ratio to five decimal places
                print(strClassification + " (" +  "{0:.5f}".format(confidence) + ")")
            # end for

            # pause until a key is pressed so the user can see the current image (shown above) and the prediction info
            cv2.waitKey()
            # after a key is pressed, close the current window to prep for the next time around
            cv2.destroyAllWindows()
        # end for
    # end with

    # write the graph to file so we can view with TensorBoard
    tfFileWriter = tf.summary.FileWriter(os.getcwd())
    tfFileWriter.add_graph(sess.graph)
    tfFileWriter.close()

# end main
    
#############################################################################################################
def masking(image):
   
    # create a simple mask image similar 
    # to the loaded image, with the  
    # shape and return type 
    mask = np.zeros(image.shape[:2], np.uint8) 

    # specify the background and foreground model 
    # using numpy the array is constructed of 1 row 
    # and 65 columns, and all array elements are 0 
    # Data type for the array is np.float64 (default) 
    backgroundModel = np.zeros((1, 65), np.float64) 
    foregroundModel = np.zeros((1, 65), np.float64) 

    # define the Region of Interest (ROI) 
    # as the coordinates of the rectangle 
    # where the values are entered as 
    # (startingPoint_x, startingPoint_y, width, height) 
    # these coordinates are according to the input image 
    # it may vary for different images 
    rectangle = (20, 20, 200, 350) 

    # apply the grabcut algorithm with appropriate 
    # values as parameters, number of iterations = 3  
    # cv2.GC_INIT_WITH_RECT is used because 
    # of the rectangle mode is used  
    cv2.grabCut(image, mask, rectangle,   
                backgroundModel, foregroundModel, 
                3, cv2.GC_INIT_WITH_RECT) 

    # In the new mask image, pixels will  
    # be marked with four flags  
    # four flags denote the background / foreground  
    # mask is changed, all the 0 and 2 pixels  
    # are converted to the background 
    # mask is changed, all the 1 and 3 pixels 
    # are now the part of the foreground 
    # the return type is also mentioned, 
    # this gives us the final mask 
    mask2 = np.where((mask == 2)|(mask == 0), 0, 1).astype('uint8') 

    # The final mask is multiplied with  
    # the input image to give the segmented image. 
    image = image * mask2[:, :, np.newaxis] 

    # output segmented image with colorbar 
    # plt.imshow(image) 
    # plt.colorbar() 
    # plt.show() 
    return image

#######################################################################################################################
def checkIfNecessaryPathsAndFilesExist():
    if not os.path.exists(TEST_IMAGES_DIR):
        print('')
        print('ERROR: TEST_IMAGES_DIR "' + TEST_IMAGES_DIR + '" does not seem to exist')
        print('Did you set up the test images?')
        print('')
        return False
    # end if

    if not os.path.exists(RETRAINED_LABELS_TXT_FILE_LOC):
        print('ERROR: RETRAINED_LABELS_TXT_FILE_LOC "' + RETRAINED_LABELS_TXT_FILE_LOC + '" does not seem to exist')
        return False
    # end if

    if not os.path.exists(RETRAINED_GRAPH_PB_FILE_LOC):
        print('ERROR: RETRAINED_GRAPH_PB_FILE_LOC "' + RETRAINED_GRAPH_PB_FILE_LOC + '" does not seem to exist')
        return False
    # end if

    return True
# end function

#######################################################################################################################
def writeResultOnImage(openCVImage, resultText):
    # ToDo: this function may take some further fine-tuning to show the text well given any possible image size

    imageHeight, imageWidth, sceneNumChannels = openCVImage.shape

    # choose a font
    fontFace = cv2.FONT_HERSHEY_TRIPLEX

    # chose the font size and thickness as a fraction of the image size
    fontScale = 1.0
    fontThickness = 2

    # make sure font thickness is an integer, if not, the OpenCV functions that use this may crash
    fontThickness = int(fontThickness)

    upperLeftTextOriginX = int(imageWidth * 0.05)
    upperLeftTextOriginY = int(imageHeight * 0.05)

    textSize, baseline = cv2.getTextSize(resultText, fontFace, fontScale, fontThickness)
    textSizeWidth, textSizeHeight = textSize

    # calculate the lower left origin of the text area based on the text area center, width, and height
    lowerLeftTextOriginX = upperLeftTextOriginX
    lowerLeftTextOriginY = upperLeftTextOriginY + textSizeHeight

    # write the text on the image
    cv2.putText(openCVImage, resultText, (lowerLeftTextOriginX, lowerLeftTextOriginY), fontFace, fontScale, SCALAR_BLUE, fontThickness)
# end function

#######################################################################################################################
if __name__ == "__main__":
    main()
