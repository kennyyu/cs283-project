import argparse
import cv2
import detect
import numpy as np

FACE_CASCADE_NAME = "cascades/haarcascade_frontalface_alt.xml";
HAND_CASCADE_NAME = "cascades/hand_front.xml"
WINDOW_NAME = "Pipeline"
FRAME_WIDTH = 320
FRAME_HEIGHT = 240

QUIT_KEY = 'c'

class Pipeline(object):
    """ Abstract Class for pipelines. """

    """ Command line arguments for our pipelines """
    parser = argparse.ArgumentParser(description="Optical Flow on Hand Detection")
    parser.add_argument("-pl", "--pipeline", type=str, default="full",
                        choices=["full", "simple", "face", "noface", "nofacekalman", "screenshot"],
                        dest="pipeline_type", help="type of pipeline to run")
    parser.add_argument("--face_cascade_name", type=str, dest="face_cascade_name",
                        help="face cascade file name")
    parser.add_argument("--hand_cascade_name", type=str, dest="hand_cascade_name",
                        help="hand cascade file name")
    parser.add_argument("--haarScaleFactor", type=float, dest="haarScaleFactor",
                        help="haar scale factor for hand detection")
    parser.add_argument("--haarMinNeighbors", type=int, dest="haarMinNeighbors",
                        help="haar min neighbors for hand detection")
    parser.add_argument("--minDistThreshold", type=int,  dest="minDistThreshold",
                        help="min distance threshold for lucas-kanade")
    parser.add_argument("--maxDistThreshold", type=int, dest="maxDistThreshold",
                        help="max distance threshold for lucas-kanade")
    parser.add_argument("--window_width", type=int,  dest="window_width",
                        help="width of search window for simple kalman")
    parser.add_argument("--window_height", type=int, dest="window_height",
                        help="height of search window for simple kalman")
    parser.add_argument("--nframes", type=int, dest="nframes",
                        help="number of frames to preserve for bg subtraction")
    parser.add_argument("--threshold", type=int, dest="threshold",
                        help="threshold for bg subtraction")
    parser.add_argument("--directionScale", type=float, dest="directionScale",
                        help="scale factor for overall direction, used in kalman")

    @staticmethod
    def create(pipeline_type, **kwargs):
        # Filter out kwargs
        newkwargs = {}
        for key in kwargs:
            if kwargs[key] is not None:
                newkwargs[key] = kwargs[key]

        if pipeline_type == "full":
            return FullPipeline(**newkwargs)
        elif pipeline_type == "simple":
            return SimplePipeline(**newkwargs)
        elif pipeline_type == "face":
            return FacePipeline(**newkwargs)
        elif pipeline_type == "noface":
            return NoFacePipeline(**newkwargs)
        elif pipeline_type == "nofacekalman":
            return NoFaceKalmanPipeline(**newkwargs)
        elif pipeline_type == "screenshot":
            return FullScreenshotPipeline(**newkwargs)
        else:
            raise Exception("unsupported option: " + pipeline_type)

    def detect(self, frame1, frame2):
        """
        All implementing classes must implement this method. Returns frame1,
        annotated with the detected hand and optical flow, and the overall
        direction of the scene.
        """
        raise Exception("Must subclass implement")

class FullPipeline(Pipeline):
    """
    Includes the full pipeline. The stages are:
        1. Detect faces and remove them from the image.
        2. Subtract away the background.
        3. Use a simplified version of a Kalman Filter to estimate the
            bounding box of the hand. This assumes smooth motion of the
            hand.
        4. Find the largest hand in the bounding box.
        5. Find the optical flow in the bounding box of the hand.
        6. Correct our estimate of our Kalman Filter, using the measured
            location and overall velocity of the hand.
    """

    def __init__(self, face_cascade_name=FACE_CASCADE_NAME,
                 hand_cascade_name=HAND_CASCADE_NAME,
                 haarScaleFactor=1.1, haarMinNeighbors=60,
                 minDistThreshold=5, maxDistThreshold=50,
                 window_width=100, window_height=180,
                 threshold=20, nframes=20, directionScale=0.02):
        self.face_cascade = detect.CascadeDetector(face_cascade_name)
        self.hand_cascade = detect.CascadeDetector(hand_cascade_name)
        self.optical = detect.LKOpticalFlow(min_threshold=minDistThreshold,
                                            max_threshold=maxDistThreshold)
        self.subtractor = detect.BGSubtractor(nframes, threshold=threshold)
        self.kalman = detect.SimpleKalman(FRAME_WIDTH, FRAME_HEIGHT,
                                          window_width, window_height, scale=directionScale)
        self.haarScaleFactor = haarScaleFactor
        self.haarMinNeighbors = haarMinNeighbors

    def detect(self, frame1, frame2):
        # Remove faces from the scene
        faces = self.face_cascade.find(frame1, minNeighbors=2, minSize=(30,30))
        no_faces = self.face_cascade.remove(frame1, faces)

        # Remove background
        foreground = self.subtractor.bgremove(no_faces)

        # Look at the window provided by Kalman prediction
        search_filtered = self.kalman.predict().filter(foreground)

        # Detect hands in the scene with no faces
        hands = self.hand_cascade.find(search_filtered,
                                       scaleFactor=self.haarScaleFactor,
                                       minNeighbors=self.haarMinNeighbors,
                                       minSize=(25,35))
        largest = self.hand_cascade.largest(frame1, hands, draw=True)
        mask = largest.mask(frame1)

        # Detect motion in the scene
        direction, frame_out = self.optical.direction(frame1, frame2, mask=mask)

        # Update Kalman
        correction = self.kalman.correct(largest, direction)
        correction.draw(frame_out, detect.Color.BLUE)
        return direction, frame_out

class NoFaceKalmanPipeline(Pipeline):

    def __init__(self, face_cascade_name=FACE_CASCADE_NAME,
                 hand_cascade_name=HAND_CASCADE_NAME,
                 haarScaleFactor=1.1, haarMinNeighbors=60,
                 minDistThreshold=5, maxDistThreshold=50,
                 window_width=100, window_height=180,
                 directionScale=0.02):
        self.face_cascade = detect.CascadeDetector(face_cascade_name)
        self.hand_cascade = detect.CascadeDetector(hand_cascade_name)
        self.optical = detect.LKOpticalFlow(min_threshold=minDistThreshold,
                                            max_threshold=maxDistThreshold)
        self.kalman = detect.SimpleKalman(FRAME_WIDTH, FRAME_HEIGHT,
                                          window_width, window_height, scale=directionScale)
        self.haarScaleFactor = haarScaleFactor
        self.haarMinNeighbors = haarMinNeighbors

    def detect(self, frame1, frame2):
        # Remove faces from the scene
        faces = self.face_cascade.find(frame1, minNeighbors=2, minSize=(30,30))
        no_faces = self.face_cascade.remove(frame1, faces)

        # Look at the window provided by Kalman prediction
        search_filtered = self.kalman.predict().filter(no_faces)

        # Detect hands in the scene with no faces
        hands = self.hand_cascade.find(search_filtered,
                                       scaleFactor=self.haarScaleFactor,
                                       minNeighbors=self.haarMinNeighbors,
                                       minSize=(25,35))
        largest = self.hand_cascade.largest(frame1, hands, draw=True)
        mask = largest.mask(frame1)

        # Detect motion in the scene
        direction, frame_out = self.optical.direction(frame1, frame2, mask=mask)

        # Update Kalman
        correction = self.kalman.correct(largest, direction)
        correction.draw(frame_out, detect.Color.BLUE)
        return direction, frame_out

class NoFacePipeline(Pipeline):
    """
    Hand detection by only removing faces.
    """
    def __init__(self, face_cascade_name=FACE_CASCADE_NAME,
                 hand_cascade_name=HAND_CASCADE_NAME,
                 haarScaleFactor=1.1, haarMinNeighbors=60,
                 minDistThreshold=5, maxDistThreshold=50):
        self.face_cascade = detect.CascadeDetector(face_cascade_name)
        self.hand_cascade = detect.CascadeDetector(hand_cascade_name)
        self.optical = detect.LKOpticalFlow(min_threshold=minDistThreshold,
                                            max_threshold=maxDistThreshold)
        self.haarScaleFactor = haarScaleFactor
        self.haarMinNeighbors = haarMinNeighbors

    def detect(self, frame1, frame2):
        # Remove faces from the scene
        faces = self.face_cascade.find(frame1, minNeighbors=2, minSize=(30,30))
        no_faces = self.face_cascade.remove(frame1, faces)

        # Detect hands in the scene with no faces
        hands = self.hand_cascade.find(no_faces,
                                       scaleFactor=self.haarScaleFactor,
                                       minNeighbors=self.haarMinNeighbors,
                                       minSize=(25,35))
        largest = self.hand_cascade.largest(frame1, hands, draw=True)
        mask = largest.mask(frame1)

        # Detect motion in the scene
        return self.optical.direction(frame1, frame2, mask=mask)

class SimplePipeline(Pipeline):
    """
    Simple pipeline that detects hands without preprocessing.
    """

    def __init__(self, hand_cascade_name=HAND_CASCADE_NAME,
                 minDistThreshold=5, maxDistThreshold=50,
                 haarScaleFactor=1.1, haarMinNeighbors=60):
        self.hand_cascade = detect.CascadeDetector(hand_cascade_name)
        self.haarScaleFactor = haarScaleFactor
        self.haarMinNeighbors = haarMinNeighbors
        self.optical = detect.LKOpticalFlow(min_threshold=minDistThreshold,
                                            max_threshold=maxDistThreshold)

    def detect(self, frame1, frame2):
        # Detect hands in the scene with no faces
        hands = self.hand_cascade.find(frame1,
                                       scaleFactor=self.haarScaleFactor,
                                       minNeighbors=self.haarMinNeighbors,
                                       minSize=(25,35))
        largest = self.hand_cascade.largest(frame1, hands, draw=True)
        mask = largest.mask(frame1)

        # Detect motion in the scene
        return self.optical.direction(frame1, frame2, mask=mask)

class FacePipeline(Pipeline):
    """
    Simple pipeline for face detection.
    """

    def __init__(self, face_cascade_name=FACE_CASCADE_NAME,
                 minDistThreshold=5, maxDistThreshold=50):
        self.face_cascade = detect.CascadeDetector(face_cascade_name)
        self.optical = detect.LKOpticalFlow(min_threshold=minDistThreshold,
                                            max_threshold=maxDistThreshold)

    def detect(self, frame1, frame2):
        faces = self.face_cascade.find(frame1, scaleFactor=1.1, minNeighbors=2,
                                       minSize=(30,30))
        largest = self.face_cascade.largest(frame1, faces, draw=True)
        mask = largest.mask(frame1)
        return self.optical.direction(frame1, frame2, mask=mask)

class FullScreenshotPipeline(Pipeline):
    """
    Includes the full pipeline and creates different windows to see intermediate results.
    """

    def __init__(self, face_cascade_name=FACE_CASCADE_NAME,
                 hand_cascade_name=HAND_CASCADE_NAME,
                 haarScaleFactor=1.1, haarMinNeighbors=60,
                 minDistThreshold=5, maxDistThreshold=50,
                 window_width=100, window_height=180,
                 threshold=20, nframes=20, directionScale=0.02):
        self.face_cascade = detect.CascadeDetector(face_cascade_name)
        self.hand_cascade = detect.CascadeDetector(hand_cascade_name)
        self.optical = detect.LKOpticalFlow(min_threshold=minDistThreshold,
                                            max_threshold=maxDistThreshold)
        self.subtractor = detect.BGSubtractor(nframes, threshold=threshold)
        self.kalman = detect.SimpleKalman(FRAME_WIDTH, FRAME_HEIGHT,
                                          window_width, window_height, scale=directionScale)
        self.haarScaleFactor = haarScaleFactor
        self.haarMinNeighbors = haarMinNeighbors

    def detect(self, frame1, frame2):
        # Show original detection
        frame1_copy = frame1.copy()
        hands = self.hand_cascade.find(frame1_copy,
                                       scaleFactor=self.haarScaleFactor,
                                       minNeighbors=self.haarMinNeighbors,
                                       minSize=(25,35))
        self.hand_cascade.largest(frame1_copy, hands, draw=True)
        cv2.imshow("Original Detection", frame1_copy)

        # Remove faces from the scene
        faces = self.face_cascade.find(frame1, minNeighbors=2, minSize=(30,30))
        no_faces = self.face_cascade.remove(frame1, faces)
        hands = self.hand_cascade.find(no_faces,
                                       scaleFactor=self.haarScaleFactor,
                                       minNeighbors=self.haarMinNeighbors,
                                       minSize=(25,35))
        no_faces_copy = no_faces.copy()
        self.hand_cascade.largest(no_faces_copy, hands, draw=True)
        cv2.imshow("Removed Faces", no_faces_copy)

        # Remove background
        foreground = self.subtractor.bgremove(no_faces)
        hands = self.hand_cascade.find(foreground,
                                       scaleFactor=self.haarScaleFactor,
                                       minNeighbors=self.haarMinNeighbors,
                                       minSize=(25,35))
        foreground_copy = foreground.copy()
        self.hand_cascade.largest(foreground_copy, hands, draw=True)
        cv2.imshow("Removed Background", foreground_copy)

        # Look at the window provided by Kalman prediction
        search_filtered = self.kalman.predict().filter(foreground)
        hands = self.hand_cascade.find(search_filtered,
                                       scaleFactor=self.haarScaleFactor,
                                       minNeighbors=self.haarMinNeighbors,
                                       minSize=(25,35))
        search_filtered_copy = search_filtered.copy()
        self.hand_cascade.largest(search_filtered_copy, hands, draw=True)
        cv2.imshow("Kalman Filter", search_filtered_copy)

        # Detect hands in the scene with no faces
        hands = self.hand_cascade.find(search_filtered,
                                       scaleFactor=self.haarScaleFactor,
                                       minNeighbors=self.haarMinNeighbors,
                                       minSize=(25,35))
        largest = self.hand_cascade.largest(frame1, hands, draw=True)
        mask = largest.mask(frame1)

        # Detect motion in the scene
        direction, frame_out = self.optical.direction(frame1, frame2, mask=mask)

        # Update Kalman
        correction = self.kalman.correct(largest, direction)
        correction.draw(frame_out, detect.Color.BLUE)
        return direction, frame_out

def main(**kwargs):
    # Read video stream from webcam
    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        print "couldn't load webcam"
        return
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    # Create pipeline from command line arguments
    pipeline = Pipeline.create(**kwargs)

    while True:
        retval1, frame1 = capture.read()
        retval2, frame2 = capture.read()
        if not retval1 or not retval2:
            print "could not grab frames"
            return

        # Mirror the frames to mimic webcam motion
        frame1 = cv2.flip(frame1, 1)
        frame2 = cv2.flip(frame2, 1)

        # Detect hand and direction of the scene
        direction, frame_out = pipeline.detect(frame1, frame2)
        print(direction)
        cv2.imshow(WINDOW_NAME, frame_out)

        # Handlers for key presses
        c = cv2.waitKey(10)
        if chr(c & 255) is QUIT_KEY:
            break

if __name__ == "__main__":
    args = Pipeline.parser.parse_args()
    main(**vars(args))
