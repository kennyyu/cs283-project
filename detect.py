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
        return VMath.add(a, VMath.negate(b))

    @staticmethod
    def scale((u, v), k):
        return (k * u, k * v)

    @staticmethod
    def int_tuple((u, v)):
        return (int(u), int(v))

    @staticmethod
    def norm((u, v)):
        return math.sqrt(u * u + v * v)

    @staticmethod
    def dist(a, b):
        return VMath.norm(VMath.subtract(a, b))

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

    def mask(self, frame):
        """ Returns a mask for frame, using the bounding box. """
        mask = np.zeros(shape=(frame.shape[0], frame.shape[1]),
                        dtype=np.dtype("uint8"))
        (u, v) = np.ix_(range(self.y, self.y + self.width),
                        range(self.x, self.x + self.height))
        indices = (u.astype(int), v.astype(int))
        mask[indices] += 1
        return mask

    def __str__(self):
        return "(x=%s, y=%s, w=%s, h=%s)" % (str(self.x), str(self.y),
                                             str(self.width), str(self.height))

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
             flags=cv2.cv.CV_HAAR_SCALE_IMAGE | cv2.cv.CV_HAAR_DO_CANNY_PRUNING,
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
        cv2.rectangle(frame, (best.x, best.y),
                      (best.x + best.width, best.y + best.height), bestColor)
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

class LKOpticalFlow(object):
    """
    Static wrapper class for calculating the direction of a scene using
    Lucas-Kanade.
    """

    def __init__(self):
        pass

    def direction(self, frame_prev, frame_next, maxCorners=100,
                  qualityLevel=0.01, minDistance=0.01, mask=None,
                  min_threshold=3, max_threshold=50,
                  color_prev=Color.RED, color_next=Color.GREEN):
        """
        Uses Lucas-Kanade to find corresponding points in the second frame
        using features from the first frame. Returns the overall direction of
        the scene and the annotated frame.
        """
        gray_prev = bgr2gray(frame_prev)
        gray_next = bgr2gray(frame_next)

        # Find features in the first frame
        features_prev = cv2.goodFeaturesToTrack(gray_prev, maxCorners,
                                                qualityLevel, minDistance,
                                                mask=mask)
        if features_prev is not None:
            for f in features_prev:
                cv2.circle(frame_prev, (f[0][0], f[0][1]), 2, color_prev)

            # Use Lucas-Kanade to find points in second frame
            features_next, status, err = cv2.calcOpticalFlowPyrLK(gray_prev,
                                                                  gray_next,
                                                                  features_prev)

        # Compute overall direction of the scene
        direction = (0, 0)
        for i in range(0, len(features_prev)):
            # Ff the feature was found in the second frame
            if status[i] == 1:
                oldpt = (features_prev[i][0][0], features_prev[i][0][1])
                newpt = (features_next[i][0][0], features_next[i][0][1])

                # Threshold distances to avoid small and big movements
                if min_threshold < VMath.dist(oldpt, newpt) < max_threshold:
                    cv2.circle(frame_prev, newpt, 2, color_next)
                    cv2.line(frame_prev, oldpt, newpt, color_next)
                    direction = VMath.add(direction, VMath.subtract(newpt, oldpt))

        # Draw the overall motion
        shape = frame_prev.shape
        center = (shape[1] / 2, shape[0] / 2)
        cv2.line(frame_prev, center, VMath.int_tuple(VMath.add(center, direction)),
                 Color.WHITE, 3)
        return (direction, frame_prev)

