"""
Capture your own labeled training images from the webcam.

Usage:
    python 08_capture_images.py <label>

Example:
    python 08_capture_images.py mug
    python 08_capture_images.py hand

Run this once per class you want the classifier to learn (at least 2
classes -- classification needs something to distinguish FROM). Aim for
~30-50 images per class, varying angle/lighting/distance a bit so the
model doesn't just memorize one exact pose.

Controls once the window is open:
    c = capture the current frame and save it under this label
    q = quit
"""
import os
import sys
import cv2

if len(sys.argv) < 2:
    print("Usage: python 08_capture_images.py <label>")
    sys.exit(1)

label = sys.argv[1]
save_dir = os.path.join(os.path.dirname(__file__), "image_data", label)
os.makedirs(save_dir, exist_ok=True)

existing = len(os.listdir(save_dir))   # so re-running doesn't overwrite previous captures
count = existing

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("No camera found.")

print(f"capturing images for label: '{label}'")
print(f"saving to: {save_dir}")
print(f"already have {existing} images for this label")
print("press 'c' to capture, 'q' to quit\n")

while True:
    ok, frame = cap.read()
    if not ok:
        break

    display = frame.copy()
    cv2.putText(display, f"label: {label}  captured: {count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(display, "c=capture  q=quit", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.imshow("capture", display)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("c"):
        path = os.path.join(save_dir, f"{count:04d}.png")
        cv2.imwrite(path, frame)
        count += 1
        print(f"saved {path}")
    elif key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print(f"\ndone. {count} total images for label '{label}'.")
