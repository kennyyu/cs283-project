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
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

    def center(self):
        return (int(self.x + self.width / 2), int(self.y + self.height / 2))

    def mask(self, frame):
        """ Returns a mask for frame, using the bounding box. """
        mask = np.zeros(shape=(frame.shape[0], frame.shape[1]),
                        dtype=np.dtype("uint8"))
        (u, v) = np.ix_(range(self.y, min(self.y + self.height, frame.shape[0])),
                        range(self.x, min(self.x + self.width, frame.shape[1])))
        indices = (u.astype(int), v.astype(int))
        mask[indices] += 1
        return mask

    def filter(self, frame):
        mask = np.zeros(shape=(frame.shape[0], frame.shape[1]),
                        dtype=np.dtype("uint8"))
        (u, v) = np.ix_(range(max(0, self.y),
                              min(self.y + self.height, frame.shape[0])),
                        range(max(0, self.x),
                              min(self.x + self.width, frame.shape[1])))
        indices = (u.astype(int), v.astype(int))
        result = np.zeros(frame.shape, dtype=frame.dtype)
        result[indices] = frame[indices]
        return result

    def draw(self, frame, color):
        cv2.rectangle(frame, (self.x, self.y),
                      (self.x + self.width, self.y + self.height), color)

    def __str__(self):
        return "(x=%s, y=%s, w=%s, h=%s)" % (str(self.x), str(self.y),
                                             str(self.width), str(self.height))

class CascadeDetector(object):
    """
    Wrapper class for a CascadeClassifier object. Provides utility methods
    to find the largest object and to mask objects out of frames.
    """

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
        objects = self.cascade.detectMultiScale(gray, scaleFactor=scaleFactor,
                                                minNeighbors=minNeighbors,
                                                flags=flags,
                                                minSize=minSize, maxSize=maxSize)
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

        # Overall direction of the scene
        direction = (0, 0)

        if features_prev is None:
            return (direction, frame_prev)
        for f in features_prev:
            cv2.circle(frame_prev, (f[0][0], f[0][1]), 2, color_prev)

        # Use Lucas-Kanade to find points in second frame
        features_next, status, err = cv2.calcOpticalFlowPyrLK(gray_prev, gray_next,
                                                                features_prev)

        # Compute overall direction of the scene
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

class BGSubtractor(object):
    """
    Removes background from a sequence of frames by maintaining a history
    of frames seen so far.
    """

    def __init__(self, nframes):
        """
        Constructor. nframes is the number of frames to keep in the history.
        """
        self.nframes = nframes
        self.frames = []

    def bgremove(self, frame, threshold=20, ksize=(15,15)):
        """
        Removes the background of the frame, using thresholding the difference with
        the provided the threshold. If fewer than nframes have been seen, the frame
        will be returned unchanged.
        """
        # If we don't have enough frames in our history, return the frame
        if len(self.frames) < self.nframes:
            self.frames.append(frame)
            return frame

        # Remove the oldest frame our history and append the new frame
        original = self.frames[0]
        self.frames = self.frames[1:]
        self.frames.append(frame)

        # Subtract the current frame and the oldest frame
        difference = cv2.absdiff(frame, original)
        _, difference = cv2.threshold(difference, threshold, 255, cv2.THRESH_BINARY)
        difference = cv2.GaussianBlur(difference, ksize, 1)
        gray = bgr2gray(difference)
        indices = gray.nonzero()

        # Set entries to zero whose difference did not pass the threshold
        mask = np.zeros(frame.shape, dtype=frame.dtype)
        mask[indices] = frame[indices]
        return mask

class Kalman(object):
    """
    Implementation of a Kalman Filter.
    See: http://www.cs.unc.edu/~tracker/media/pdf/SIGGRAPH2001_CoursePack_08.pdf
    OpenCV 2.4.3. is lacking python bindings for this.
    """

    def __init__(self, n, m, l, p_sigma=.1, q_sigma=1e-4, r_sigma=1e-1):
        """
        Params:
            n: dimension of our state (dynamic)
            m: dimension of our measurements
            l: dimension of our control
            p_sigma: entry in our diagonal matrix P (error noise STD)
            q_sigma: entry in our diagonal matrix Q (process noise STD)
            r_sigma: entry in our diagonal matrix R (measurement noise STD)
        """
        self.n = n
        self.m = m
        self.l = l
        self.p_sigma = p_sigma
        self.q_sigma = q_sigma
        self.r_sigma = r_sigma

    def init(self, A, x,
             B=np.zeros((0,0)),
             H=np.zeros((0,0)),
             P=np.zeros((0,0)),
             Q=np.zeros((0,0)),
             R=np.zeros((0,0))):
        """
        Params:
            A: transition matrix (n x n)
            x: initial state (n x 1)
            B: control matrix (n x l)
            H: measurement matrix (m x n)
            P: error noise covariance matrix (n x n)
            Q: process noise covariance matrix (n x n)
            R: measurement noise covariance matrix (m x m)
        """
        self.A = A
        self.x = x
        self.B = B if B.shape == (self.n, self.l) else np.zeros((self.n, self.l))
        self.H = H if H.shape == (self.m, self.n) else np.zeros((self.m, self.n))
        self.P = P if P.shape == (self.n, self.n) else np.identity(self.n) * self.p_sigma
        self.Q = Q if Q.shape == (self.n, self.n) else np.identity(self.n) * self.q_sigma
        self.R = R if R.shape == (self.m, self.m) else np.identity(self.m) * self.r_sigma

    def predict(self, u=np.zeros((0,0))):
        """ Returns prior estimation of z. """
        
        u = u if u.shape == (self.l, 1) else np.zeros((self.l, 1))
        self.x = np.dot(self.A, self.x) + np.dot(self.B, u)
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q
        """
        self.x = np.dot(self.A, self.x)
        """
        return self.generate()

    def correct(self, z):
        """ Returns posterior estimation of z. """
        
        K = np.dot(np.dot(self.P, self.H.T),
                   np.dot(np.dot(self.H, self.P), self.H.T) + self.R)
        self.x = self.x + np.dot(K, z - np.dot(self.H, self.x))
        self.P = np.dot(np.identity(self.n) - np.dot(K, self.H), self.P)
        """
        self.x = np.dot(self.H, z)
        """
        return self.generate()

    def generate(self):
        """ Generates an estimation of z. """
        
        v = np.random.normal(0, np.linalg.norm(self.R), self.m)
        return np.dot(self.H, self.x) + v.T
        """
        return self.x
        """

