import cv2
import detect
import numpy as np

FACE_CASCADE_NAME = "/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml";
HAND_CASCADE_NAME = "hand_front.xml"
WINDOW_NAME = "Pipeline"
FRAME_WIDTH = 320
FRAME_HEIGHT = 240

QUIT_KEY = 'c'

class Pipeline(object):
    """ Abstract Class for pipelines. """

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

    def __init__(self, face_cascade_name, hand_cascade_name,
                 haarScaleFactor=1.1, haarMinNeighbors=60,
                 window_width=100, window_height=180,
                 nframes=20, directionScale=0.1):
        self.face_cascade = detect.CascadeDetector(face_cascade_name)
        self.hand_cascade = detect.CascadeDetector(hand_cascade_name)
        self.optical = detect.LKOpticalFlow()
        self.subtractor = detect.BGSubtractor(nframes)
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
        largest = self.hand_cascade.largest(frame1, hands, draw=False)
        mask = largest.mask(frame1)

        # Detect motion in the scene
        direction, frame_out = self.optical.direction(frame1, frame2, mask=mask)

        # Update Kalman
        correction = self.kalman.correct(largest, direction)
        correction.draw(frame_out, detect.Color.BLUE)
        return direction, frame_out

def main():
    # Read video stream from webcam
    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        print "couldn't load webcam"
        return
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    pipeline = FullPipeline(FACE_CASCADE_NAME, HAND_CASCADE_NAME,
                            haarScaleFactor=1.1, haarMinNeighbors=60,
                            window_width=100, window_height=180,
                            nframes=20, directionScale=0.1)

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
    main()