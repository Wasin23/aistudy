"""
Sanity check: can we grab live frames from a webcam at all?
This is the "hello world" of perception -- before any model touches
the images, we need frames flowing reliably.

Press 'q' in the window to quit.
"""
import cv2

cap = cv2.VideoCapture(0)  # 0 = default camera

if not cap.isOpened():
    raise RuntimeError("No camera found at index 0 -- try 1, or check permissions.")

print("Camera opened. Press 'q' to quit.")

while True:
    ok, frame = cap.read()
    if not ok:
        print("Failed to read frame.")
        break

    cv2.imshow("webcam", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
