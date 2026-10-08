import numpy as np
from typing import Dict, Any, List

class TestAuditorAgent:
    """
    Test & Audit Agent: Evaluates detection precision, computes Intersection-over-Union (IoU)
    against ground truth metadata, and logs system benchmark metrics.
    """

    @staticmethod
    def calculate_iou(boxA: List[int], boxB: List[int]) -> float:
        """Computes Intersection over Union (IoU) between two bounding boxes [x, y, w, h]."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = boxA[2] * boxA[3]
        boxBArea = boxB[2] * boxB[3]

        denom = float(boxAArea + boxBArea - interArea)
        if denom == 0:
            return 0.0
        return round(interArea / denom, 3)

    def generate_audit_report(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes the final audit report from graph state.
        """
        detections = state.get("detections", [])
        quality = state.get("quality_report", {})
        meta = state.get("metadata", {})
        iterations = state.get("iteration_count", 1)
        enhancements = state.get("enhancement_history", [])

        detected_bbox = detections[0]["bbox"] if detections else None
        gt_bbox = meta.get("ground_truth_bbox", None)

        iou_score = 0.0
        if detected_bbox and gt_bbox:
            iou_score = self.calculate_iou(detected_bbox, gt_bbox)

        # Audit verdict classification
        if detections and (quality.get("quality_score", 0) >= 60.0 or iou_score > 0.4):
            if iterations == 1:
                verdict = "PASSED_FIRST_TRY"
            else:
                verdict = "PASSED_AFTER_SELF_HEALING"
        else:
            verdict = "FAILED_QUALITY_GATE"

        report = {
            "verdict": verdict,
            "face_detected": len(detections) > 0,
            "detection_count": len(detections),
            "primary_bbox": detected_bbox,
            "iou_vs_ground_truth": iou_score,
            "final_quality_score": quality.get("quality_score", 0.0),
            "final_status": quality.get("status", "UNKNOWN"),
            "self_healing_iterations": iterations - 1,
            "applied_enhancements": enhancements,
            "degradation_handled": meta.get("degradation", "none")
        }

        return report
