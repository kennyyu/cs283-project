import cv2
import math
import numpy as np

# Global constants
FACE_CASCADE_NAME = "/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml";
FACE_CASCADE = cv2.CascadeClassifier(FACE_CASCADE_NAME)

WINDOW_NAME = "Face Optical Flow"
FRAME_WIDTH = 320
FRAME_HEIGHT = 240

MAX_CORNERS = 100 # maximum number of corners per box
MIN_THRESHOLD = 10 # remove distances that are too small
MAX_THRESHOLD = 50 # remove distances that are too big

# Colors
RED = cv2.cv.Scalar(0, 0, 255)
GREEN = cv2.cv.Scalar(0, 255, 0)
BLUE = cv2.cv.Scalar(255, 0, 0)
WHITE = cv2.cv.Scalar(255, 255, 255)

# Some useful functions for dealing with vectors
def add((u, v), (x, y)):
    return (u + x, v + y)

def negate((u, v)):
    return (-u, -v)

def subtract(a, b):
    return add(a, negate(b))

def scale((u, v), k):
    return (k * u, k * v)

def float_to_int((u,v)):
    return (int(u), int(v))

def dist((u,v), (a,b)):
    return math.sqrt((u - a) * (u - a) + (b - v) * (b - v))

def detect_and_display(frame1, frame2):
    # Convert to grayscale
    frame_gray1 = cv2.cvtColor(frame1, cv2.cv.CV_BGR2GRAY)
    frame_gray1 = cv2.equalizeHist(frame_gray1)
    frame_gray2 = cv2.cvtColor(frame2, cv2.cv.CV_BGR2GRAY)
    frame_gray2 = cv2.equalizeHist(frame_gray2)

    # Find all the faces in the frame
    faces = FACE_CASCADE.detectMultiScale(frame_gray1, 1.1, 2,
                                          0 | cv2.cv.CV_HAAR_SCALE_IMAGE,
                                          (30,30))

    # If there are no faces, then quit
    if faces == None or len(faces) == 0:
        print (0,0)
        return frame1

    # Only keep the largest face
    fmax = [0, 0, 0, 0]
    for f in faces:
        if f[2] * f[3] > fmax[2] * fmax[3]:
            fmax = f
    x1 = int(fmax[0])
    y1 = int(fmax[1])
    width = int(fmax[2])
    height = int(fmax[3])
    cv2.rectangle(frame1, (x1, y1), (x1 + width, y1 + height), GREEN)

    # Create a mask using the bounding box of the face
    frame_roi = None
    if width > 0 and height > 0:
        frame_roi = np.zeros(shape=frame_gray1.shape, dtype=np.dtype("uint8"))
        submatrix = np.ix_(range(y1, min(y1 + width, FRAME_WIDTH)),
                           range(x1, min(x1 + height, FRAME_HEIGHT)))
        frame_roi[submatrix] += 1

    # Find features of first frame
    features1 = cv2.goodFeaturesToTrack(frame_gray1, MAX_CORNERS,
                                        qualityLevel=0.01,
                                        minDistance=0.01,
                                        mask=frame_roi)
    for v in features1:
        cv2.circle(frame1, (v[0][0], v[0][1]), 2, RED)

    # Use Lucas-Kanade to find points in second frame
    features2, status, err = cv2.calcOpticalFlowPyrLK(frame_gray1, frame_gray2,
                                                      features1)

    # Calculate the total aggregate direction of the scene
    overall = (0, 0)
    n = len(features1)
    for i in range(0, n):
        if status[i] == 1:
            oldpt = (features1[i][0][0], features1[i][0][1])
            newpt = (features2[i][0][0], features2[i][0][1])
            if MIN_THRESHOLD < dist(oldpt, newpt) < MAX_THRESHOLD:
                cv2.circle(frame1, newpt, 2, GREEN)
                cv2.line(frame1, oldpt, newpt, GREEN)
                overall = add(overall, subtract(newpt, oldpt))

    # Draw the overall motion
    center = (int(FRAME_WIDTH / 2), int(FRAME_HEIGHT / 2))
    overall = scale(overall, 0.2)
    cv2.line(frame1, center, float_to_int(add(center, overall)), WHITE, 3)
    print overall
    return frame1

def main():
    # Ensure cascade was loaded
    if (FACE_CASCADE.empty()):
        print "couldn't load cascade"
        return

    # Read the video stream
    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        print "couldn't load video"
        return
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    while True:
        retval1, frame1 = capture.read()
        retval2, frame2 = capture.read()
        if not retval1 or not retval2:
            print "could not grab frames"
            return

        # Mirror the frames to mimic webcam motion
        frame1 = cv2.flip(frame1, 1)
        frame2 = cv2.flip(frame2, 1)
        detect_and_display(frame1, frame2)
        cv2.imshow(WINDOW_NAME, frame1)

        c = cv2.waitKey(10)
        if chr(c & 255) is 'c':
            break

if __name__ == "__main__":
    main();