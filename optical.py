import cv2
import math
import numpy as np

# Global constants
CASCADE_NAME = "/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml";
CASCADE = cv2.CascadeClassifier(CASCADE_NAME)

WINDOW_NAME = "Optical Flow"
FRAME_WIDTH = 320
FRAME_HEIGHT = 240

MAX_CORNERS = 100 # maximum number of corners per box
MIN_THRESHOLD = 3 # remove distances that are too small
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
    """
    Finds the object in the scene and use Lucas-Kanade to detect the optical
    flow in the bounding frame of the scene. Returns a tuple (direction, frame)
    where direction is a string encoding the direction of the scene, and frame
    containing the annotated frame.
    """
    # Convert to grayscale
    frame_gray1 = cv2.equalizeHist(cv2.cvtColor(frame1, cv2.cv.CV_BGR2GRAY))
    frame_gray2 = cv2.equalizeHist(cv2.cvtColor(frame2, cv2.cv.CV_BGR2GRAY))

    # Find the frame region of interest for the largest object
    overall = (0, 0)
    frame_roi = get_frame_roi(frame_gray1, frame1)
    if frame_roi is not None:
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
        overall = overall_direction(frame1, features1, features2, status)

    # Draw the overall motion
    center = (int(FRAME_WIDTH / 2), int(FRAME_HEIGHT / 2))
    cv2.line(frame1, center, float_to_int(add(center, overall)), WHITE, 3)
    print overall
    return direction_string(overall), frame1

def get_frame_roi(frame_gray, frame):
    """
    Detect all the objects in the scene and returns a frame region of interest
    for the largest object, or None if there are no objects.
    """
    # Find all the objects in the frame
    objects = CASCADE.detectMultiScale(frame_gray, 1.1, 2,
                                       0 | cv2.cv.CV_HAAR_SCALE_IMAGE,
                                       (30,30))

    # If there are no objects, then return None
    if objects == None or len(objects) == 0:
        return None

    # Only keep the largest face
    objmax = [0, 0, 0, 0]
    for obj in objects:
        if obj[2] * obj[3] > objmax[2] * objmax[3]:
            objmax = obj
    x = int(objmax[0])
    y = int(objmax[1])
    width = int(objmax[2])
    height = int(objmax[3])
    cv2.rectangle(frame, (x, y), (x + width, y + height), GREEN)

    # Create a mask using the bounding box of the face
    frame_roi = None
    if width > 0 and height > 0:
        frame_roi = np.zeros(shape=frame_gray.shape, dtype=np.dtype("uint8"))
        (u, v) = np.ix_(range(y, min(y + width, FRAME_WIDTH)),
                        range(x, min(x + height, FRAME_HEIGHT)))
        submatrix = (u.astype(int), v.astype(int))
        frame_roi[submatrix] += 1
    return frame_roi

def overall_direction(frame, features1, features2, status):
    """
    Compute the overall direction vector of the scene by computing the
    sum of the distances of corresponding points between features1 and
    features2.
    """
    overall = (0, 0)
    n = len(features1)
    for i in range(0, n):
        if status[i] == 1:
            oldpt = (features1[i][0][0], features1[i][0][1])
            newpt = (features2[i][0][0], features2[i][0][1])
            if MIN_THRESHOLD < dist(oldpt, newpt) < MAX_THRESHOLD:
                cv2.circle(frame, newpt, 2, GREEN)
                cv2.line(frame, oldpt, newpt, GREEN)
                overall = add(overall, subtract(newpt, oldpt))
    return overall

def direction_string((x,y)):
    """
    Normalizes (x,y) and returns a string of the form:
        x = 0.12
        y = -0.13
        output: "+0.12-0.13"
    """
    a = x / FRAME_WIDTH;
    b = y / FRAME_HEIGHT;
    return "%+0.2f%+0.2f" % (a,b)

def main():
    # Ensure cascade was loaded
    if CASCADE.empty():
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

        # Quit if 'c' is pressed
        c = cv2.waitKey(10)
        if chr(c & 255) is 'c':
            break

if __name__ == "__main__":
    main();