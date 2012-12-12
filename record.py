import cv2
import pipeline

# Number of frames to record
NUM_FRAMES = 50

def main():
    # Read video stream from webcam
    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        print "couldn't load webcam"
        return
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, pipeline.FRAME_WIDTH)
    capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, pipeline.FRAME_HEIGHT)

    prev = None
    current = None

    for i in range(-1, NUM_FRAMES):
        prev = current
        retval1, current = capture.read()
        if not retval1:
            print "could not grab frame"
            return
        if prev is None:
            continue

        # Mirror the frames to mimic webcam motion
        prev = cv2.flip(prev, 1)

        # Write frame to disk
        cv2.imwrite("data/analysis/img%04d.jpg" % i, prev)

if __name__ == "__main__":
    main()