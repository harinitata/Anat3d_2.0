"""Optional OpenCV debug window (disable with --no-preview, e.g. inside Docker)."""
from .controller import FrameResult


class Preview:
    def show(self, result: FrameResult) -> bool:
        """Draw the frame. Returns False when ESC is pressed."""
        import cv2
        if result.frame is None:
            return True
        image = cv2.flip(result.frame, 1)
        color = (0, 255, 0) if result.hand_detected else (0, 0, 255)
        label = result.gesture.value if result.gesture else "NEUTRAL"
        cv2.putText(image, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.putText(image, "HAND DETECTED" if result.hand_detected else "NO HAND",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.imshow("ANAT3D - Controller", image)
        return (cv2.waitKey(1) & 0xFF) != 27

    def close(self) -> None:
        import cv2
        cv2.destroyAllWindows()
