import cv2
import os
from datetime import datetime
from detect import VMath
from pipeline import Pipeline, FRAME_WIDTH, FRAME_HEIGHT
from record import NUM_FRAMES

def main(**kwargs):
    # Create pipeline from command line arguments
    pipeline = Pipeline.create(**kwargs)

    directory = "data/" + str(pipeline.__class__)
    if not os.path.exists(directory):
        os.makedirs(directory)

    prev = None
    current = None

    overall = (0, 0)
    hand_size = (0, 0)
    time_start = datetime.now()
    time_now = datetime.now()
    
    for i in range(0, NUM_FRAMES):
        prev = current
        current = cv2.imread("data/analysis/img%04d.jpg" % i)
        if prev is None:
            continue

        # Detect hand and direction of the scene
        largest, direction, frame_out = pipeline.detect(prev, current)
        cv2.imwrite(directory + "/img%04d.jpg" % i, frame_out)

        # Compute the running counts
        time_now = datetime.now()
        time_diff = time_now - time_start
        print("frames/sec: " + str(1e6 * (1. * i) / (time_diff.seconds * 1e6 + time_diff.microseconds)))
        overall = VMath.add(overall, direction)
        hand_size = VMath.add(hand_size, (largest.width, largest.height))

    print "FINAL:"
    time_diff = time_now - time_start
    print("frames/sec: " + str(1e6 * (1. * i) / (time_diff.seconds * 1e6 + time_diff.microseconds)))
    print("average direction (x, y): " + str(VMath.scale(overall, 1.0 / (NUM_FRAMES - 1))))
    print("average hand size (width, height): " + str(VMath.scale(hand_size, 1.0 / (NUM_FRAMES - 1))))


if __name__ == "__main__":
    args = Pipeline.parser.parse_args()
    main(**vars(args))