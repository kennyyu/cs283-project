import cv2
import math
import numpy as np

def bgr2gray(frame):
    """ Convert a frame to grayscale. """
    return cv2.equalizeHist(cv2.cvtColor(frame, cv2.cv.CV_BGR2GRAY))

class VMath(object):
    """ Static wrapper class for functions dealing with vector arithmetic. """

    @staticmethod
    def add((u, v), (x, y)):
        return (u + x, v + y)

    @staticmethod
    def negate((u, v)):
        return (-u, -v)

    @staticmethod
    def subtract(a, b):
        return add(a, negate(b))

    @staticmethod
    def scale((u, v), k):
        return (k * u, k * v)

    @staticmethod
    def int_tuple((u,v)):
        return (int(u), int(v))

    @staticmethod
    def norm(u, v):
        return sqrt(u * u + v * v)

    @staticmethod
    def dist(a, b):
        return norm(subtract(a, b))

class Color(object):
    """ Static wrapper class for color constants. """
    RED = cv2.cv.Scalar(0, 0, 255)
    GREEN = cv2.cv.Scalar(0, 255, 0)
    BLUE = cv2.cv.Scalar(255, 0, 0)
    WHITE = cv2.cv.Scalar(255, 255, 255)
    YELLOW = cv2.cv.Scalar(0, 255, 255)

class Rect(object):
    """ Utility class for dealing with rectangles. """

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def center(self):
        return (int(x + width / 2), int(y + height / 2))

class CascadeDetector(object):

    def __init__(self, cascade_name):
        """
        Constructor. Throws exception if opencv cannot open the cascade with
        the provided name.
        """
        cascade = cv2.CascadeClassifier(cascade_name)
        if cascade.empty():
            raise Exception("couldn't load cascade: " + cascade_name)
        self.cascade = cascade

    def find(self,
             frame,
             scaleFactor=1.1,
             minNeighbors=3,
             flags=cv2.cv.CV_HAAR_DO_CANNY_PRUNING | cv2.cv.CV_HAAR_DO_CANNY_PRUNING,
             minSize=None,
             maxSize=None):
        """
        Finds all the objects in the frame and returns a list of rectangle
        objects (x, y, width, height).
        """
        gray = bgr2gray(frame)
        objects = self.cascade.detectMultiScale(gray, scaleFactor, minNeighbors,
                                                flags, minSize, maxSize)
        if objects is None or len(objects) == 0:
            objects = []
        return objects

    def largest(self, frame, objects, draw=True,
                color=Color.YELLOW, bestColor=Color.GREEN):
        """
        Returns the largest object in the list of objects, and optionally draws
        bounding boxes around the other detected objects in the frame.
        """
        best = Rect(0, 0, 0, 0)
        for rect in objects:
            [x, y, width, height] = rect[:4]
            if draw:
                cv2.rectangle(frame, (x, y), (x + width, y + height), color)
            if width * height > best.width * best.height:
                best = Rect(x, y, width, height)
        cv2.rectangle(frame, (rect.x, rect.y),
                      (rect.x + rect.width, rect.y + rect.height), bestColor)
        return best

    def remove(self, frame, objects):
        """
        Returns a copy of frame where the pixels within bounding boxes of
        the detected objects are zeroed out.
        """
        result = frame.copy()
        for rect in objects:
            [x, y, width, height] = rect[:4]
            (u, v) = np.ix_(range(int(y), int(y + width)),
                            range(int(x), int(x + height)))
            submatrix = (u.astype(int), v.astype(int))
            result[submatrix] = 0
        return result
