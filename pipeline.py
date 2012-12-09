import cv2
import detect

CASCADE_NAME = "/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml";
WINDOW_NAME = "Pipeline"
FRAME_WIDTH = 320
FRAME_HEIGHT = 240

QUIT_KEY = 'c'

def main():
    # Read video stream from webcam
    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        print "couldn't load webcam"
        return
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    cascade = detect.CascadeDetector(CASCADE_NAME)
    optical = detect.LKOpticalFlow()

    while True:
        retval1, frame1 = capture.read()
        retval2, frame2 = capture.read()
        if not retval1 or not retval2:
            print "could not grab frames"
            return

        # Mirror the frames to mimic webcam motion
        frame1 = cv2.flip(frame1, 1)
        frame2 = cv2.flip(frame2, 1)

        # Detect objects in the scene
        objects = cascade.find(frame1, minNeighbors=2, minSize=(30,30))
        largest = cascade.largest(frame1, objects)
        result = cascade.remove(frame1, objects)
        mask = largest.mask(frame1)

        # Detect motion in the scene
        direction, frame_out = optical.direction(frame1, frame2, mask=mask)
        cv2.imshow(WINDOW_NAME, frame_out)

        # Handlers for key presses
        c = cv2.waitKey(10)
        if chr(c & 255) is QUIT_KEY:
            break

if __name__ == "__main__":
    main()