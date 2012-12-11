Pipeline for Hand Gesture Detection
===================================

The goal of this project is to create a simple hand gesture detection system, using relatively few images to train our hand classifier. Given a poorly trained Haar Cascade Classifier (250 positive samples and 100 negative samples) to recognize hands, this project assembles a pipeline to improve the quality of the recognition. These steps include:

1. Face detection and removal of faces.
2. Background subtraction.
3. Use a simplified Kalman-Filter-esque technique to estimate the bounding box of the hand. This assumes that a hand moves in a smooth manner.
4. Use our hand classifier to detect the largest hand within the bounding box.
5. Compute the optical flow of points within the bounding box using Lucas-Kanade.
6. Use the optical flow and the measured position of the hand to correct our Kalman-Filter estimate.

Dependencies
============

* OpenCV 2.4.3
* Tornado (Python) 2.4.1
* Python 2.7
* Websockets
* Chrome

How to Run the Code
===================

## Running the Pipeline

You must have OpenCV 2.4.1+ installed and Python 2.7. To run the detection pipeline without the maps application, run:

    python pipeline.py

To choose a different pipeline, choose one of the following, e.g.:

    python pipeline.py --pipeline=nofacekalman

Below are the possible options:

1. full - all the stages
2. simple - simple hand detection with no pipeline
3. face - detect faces
4. noface - remove faces
5. nofacekalman - remove faces, apply a kalman filter
6. screenshot - see all the individual stages of the pipeline

To see more flags, use the `-h` flag:

    python pipeline.py -h

## Running the Maps Application

To run the server, you must install Tornado (Python) 2.4.1. To start the server, specify the port (default is 8888):

    python server.py --port=8888

`server.py` accepts the same command line arguments as `pipeline.py`. To open the client on the server, edit `static/settings.js` to match the port specified on the server. `static/settings.js` should look like this:

    MotionApp = {
        HOST: "localhost",
        PORT: 8888,
        WIDTH: 320,
        HEIGHT: 240,
        SCALE_FACTOR: 0.5,
    };

Then visit `localhost:8888` in Chrome (you must be using the latest version of Chrome and have Websockets enabled, see `chrome://flags`). To scroll around, face the palm of your hand, fingers together, towards the camera, and move your hand around!
