import cv2
import detect

FACE_CASCADE_NAME = "/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml";
HAND_CASCADE_NAME = "hand_front.xml"
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

    face_cascade = detect.CascadeDetector(FACE_CASCADE_NAME)
    hand_cascade = detect.CascadeDetector(HAND_CASCADE_NAME)
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

        # Remove faces from the scene
        faces = face_cascade.find(frame1, minNeighbors=2, minSize=(30,30))
        no_faces = face_cascade.remove(frame1, faces)

        # Detect hands in the scene with no faces
        hands = hand_cascade.find(no_faces, scaleFactor=3, minNeighbors=15,
                                  minSize=(25,35))
        frame1 = no_faces
        largest = hand_cascade.largest(frame1, hands)
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