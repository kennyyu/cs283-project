Pipeline for Hand Gesture Recognition
=====================================

The goal of this project is to create a simple hand gesture recognition system, using relatively few images to train our hand classifier. Given a poorly trained Haar Cascade Classifier (250 positive samples and 100 negative samples) to recognize hands, this project assembles a pipeline to improve the quality of the recognition. These steps include:

1. Face detection and removal of faces.
2. Background subtraction.
3. Use a simplified Kalman-Filter-esque technique to estimate the bounding box of the hand. This assumes that a hand moves in a smooth manner.
4. Find our hand classifier to detect the largest hand within the bounding box.
5. Compute the optical flow of points within the bounding box using Lucas-Kanade.
6. Use the optical flow and the measured position of the hand to correct our Kalman-Filter estimate.

Dependencies
============

* OpenCV 2.4.3
* Tornado (Python) 2.4.1
* Python 2.7