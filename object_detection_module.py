# object_detection_module.py

import cv2
import os
import time
import numpy as np

from . import config
from .utils import log_event

# Initialize YOLO network
net = None
layer_names = None
output_layers = None

def load_yolo_model():
    """
    Loads the YOLO model weights and config from the specified paths.
    """
    global net, layer_names, output_layers

    print(f"[{time.strftime('%H:%M:%S')}] Loading YOLO model from '{config.YOLO_WEIGHTS}' and '{config.YOLO_CONFIG}'...")
    if not os.path.exists(config.YOLO_WEIGHTS) or not os.path.exists(config.YOLO_CONFIG):
        print(f"[{time.strftime('%H:%M:%S')}] Error: YOLO model files not found in '{config.MODEL_DATA_DIR}'. Object detection will not work.")
        net = None
        return

    try:
        net = cv2.dnn.readNet(config.YOLO_WEIGHTS, config.YOLO_CONFIG)

        # Get the names of all layers in the network
        layer_names = net.getLayerNames()
        # Get the names of the output layers (these are the layers that produce the detection results)
        # For YOLO, these are the unconnected output layers
        output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

        print(f"[{time.strftime('%H:%M:%S')}] YOLO model loaded successfully.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error loading YOLO model: {e}")
        net = None

def detect_objects_in_frame(frame):
    """
    Detects objects in a single frame using the loaded YOLO model.
    Returns a list of (class_name, confidence, bbox) tuples.
    """
    detected_objects = []

    if net is None:
        # Model not loaded, log a warning if it hasn't been logged recently
        if not hasattr(detect_objects_in_frame, 'warned_about_model_not_loaded'):
            print(f"[{time.strftime('%H:%M:%S')}] Warning: YOLO model not loaded. Skipping object detection.")
            detect_objects_in_frame.warned_about_model_not_loaded = True
        return detected_objects

    height, width, channels = frame.shape

    # Create a blob from the frame (scale, size, mean subtraction, swap RB)
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)

    # Forward pass through the network
    outs = net.forward(output_layers)

    # Post-process the detections
    class_ids = []
    confidences = []
    boxes = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > config.YOLO_CONFIDENCE_THRESHOLD:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Apply Non-Maximum Suppression (NMS) to remove overlapping bounding boxes
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, config.YOLO_CONFIDENCE_THRESHOLD, config.YOLO_NMS_THRESHOLD)

    if len(indexes) > 0: # Check if indexes is not empty (can be empty array)
        for i in indexes.flatten(): # Flatten the 2D array of indexes
            box = boxes[i]
            x, y, w, h = box[0], box[1], box[2], box[3]
            label = str(config.YOLO_CLASSES[class_ids[i]])
            confidence = str(round(confidences[i], 2))

            detected_objects.append((label, confidence, (x, y, w, h)))

    return detected_objects