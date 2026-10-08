import cv2
import numpy as np
import random
from typing import Tuple, Optional

class SyntheticIndustrialGenerator:
    """Generates synthetic metal surface images with parameterizable defects and noise."""
    
    def __init__(self, width: int = 512, height: int = 512, seed: Optional[int] = None):
        self.width = width
        self.height = height
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)

    def generate_base_metal(self) -> np.ndarray:
        """Generates realistic brushed metal surface texture with horizontal grain."""
        base_intensity = np.random.randint(160, 200)
        img = np.full((self.height, self.width), base_intensity, dtype=np.uint8)

        # Brushed grain lines horizontally
        for _ in range(self.height * 2):
            y = np.random.randint(0, self.height)
            thickness = np.random.randint(1, 2)
            shade = np.random.randint(-25, 25)
            line_val = np.clip(base_intensity + shade, 0, 255)
            cv2.line(img, (0, y), (self.width, y), int(line_val), thickness)

        # Add Gaussian noise
        noise = np.random.normal(0, 7, (self.height, self.width)).astype(np.float32)
        metal = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        return cv2.cvtColor(metal, cv2.COLOR_GRAY2BGR)

    def inject_scratch(self, img: np.ndarray) -> np.ndarray:
        """Injects linear or curvilinear surface scratch."""
        out = img.copy()
        pt1 = (np.random.randint(50, self.width - 50), np.random.randint(50, self.height - 50))
        angle = np.random.uniform(0, 2 * np.pi)
        length = np.random.randint(80, 220)
        pt2 = (
            int(np.clip(pt1[0] + length * np.cos(angle), 10, self.width - 10)),
            int(np.clip(pt1[1] + length * np.sin(angle), 10, self.height - 10))
        )
        thickness = np.random.randint(1, 3)
        color = (np.random.randint(40, 90), np.random.randint(40, 90), np.random.randint(40, 90))
        cv2.line(out, pt1, pt2, color, thickness, cv2.LINE_AA)
        return out

    def inject_crack(self, img: np.ndarray) -> np.ndarray:
        """Injects branching jagged crack."""
        out = img.copy()
        curr_pt = (np.random.randint(100, self.width - 100), np.random.randint(100, self.height - 100))
        segments = np.random.randint(6, 14)
        for _ in range(segments):
            next_pt = (
                int(np.clip(curr_pt[0] + np.random.randint(-30, 30), 10, self.width - 10)),
                int(np.clip(curr_pt[1] + np.random.randint(15, 45), 10, self.height - 10))
            )
            cv2.line(out, curr_pt, next_pt, (20, 20, 20), np.random.randint(2, 4), cv2.LINE_AA)
            if np.random.random() < 0.4:
                branch_pt = (
                    int(np.clip(curr_pt[0] + np.random.randint(-40, 40), 10, self.width - 10)),
                    int(np.clip(curr_pt[1] + np.random.randint(10, 30), 10, self.height - 10))
                )
                cv2.line(out, curr_pt, branch_pt, (25, 25, 25), 1, cv2.LINE_AA)
            curr_pt = next_pt
        return out

    def inject_corrosion(self, img: np.ndarray) -> np.ndarray:
        """Injects oxidation patches with pitting."""
        out = img.copy()
        cx = np.random.randint(120, self.width - 120)
        cy = np.random.randint(120, self.height - 120)
        num_spots = np.random.randint(25, 60)
        for _ in range(num_spots):
            rx = cx + int(np.random.normal(0, 35))
            ry = cy + int(np.random.normal(0, 35))
            rx = np.clip(rx, 10, self.width - 10)
            ry = np.clip(ry, 10, self.height - 10)
            radius = np.random.randint(3, 10)
            # Rust orange/brown tone
            color = (np.random.randint(20, 50), np.random.randint(70, 110), np.random.randint(130, 180))
            cv2.circle(out, (rx, ry), radius, color, -1)
        return out

    def inject_dimensional(self, img: np.ndarray) -> np.ndarray:
        """Injects corner notch or edge deformation scaled dynamically to resolution."""
        out = img.copy()
        flaw_type = random.choice(["corner_chip", "edge_notch"])
        scale = min(self.width, self.height) / 512.0
        flaw_size = int(random.uniform(55, 95) * scale)

        if flaw_type == "corner_chip":
            corner = random.choice(["top_left", "top_right", "bottom_left", "bottom_right"])
            if corner == "top_left":
                pts = np.array([[0, 0], [flaw_size, 0], [0, flaw_size]], np.int32)
            elif corner == "top_right":
                pts = np.array([[self.width, 0], [self.width - flaw_size, 0], [self.width, flaw_size]], np.int32)
            elif corner == "bottom_left":
                pts = np.array([[0, self.height], [flaw_size, self.height], [0, self.height - flaw_size]], np.int32)
            else:
                pts = np.array([[self.width, self.height], [self.width - flaw_size, self.height], [self.width, self.height - flaw_size]], np.int32)
            cv2.fillPoly(out, [pts], (15, 15, 15))
        else:
            edge = random.choice(["top", "bottom", "left", "right"])
            nw = int(flaw_size * 1.5)
            nh = int(flaw_size * 0.8)
            if edge == "top":
                cx = random.randint(nw, max(nw + 1, self.width - nw))
                pts = np.array([[cx - nw // 2, 0], [cx + nw // 2, 0], [cx, nh]], np.int32)
            elif edge == "bottom":
                cx = random.randint(nw, max(nw + 1, self.width - nw))
                pts = np.array([[cx - nw // 2, self.height], [cx + nw // 2, self.height], [cx, self.height - nh]], np.int32)
            elif edge == "left":
                cy = random.randint(nh, max(nh + 1, self.height - nh))
                pts = np.array([[0, cy - nh // 2], [0, cy + nh // 2], [nw, cy]], np.int32)
            else:
                cy = random.randint(nh, max(nh + 1, self.height - nh))
                pts = np.array([[self.width, cy - nh // 2], [self.width, cy + nh // 2], [self.width - nw, cy]], np.int32)
            cv2.fillPoly(out, [pts], (15, 15, 15))
        return out

    def generate(self, defect_type: str = "normal") -> Tuple[np.ndarray, str]:
        """Generates metal surface with requested defect."""
        base = self.generate_base_metal()
        if defect_type == "normal":
            return base, "normal"
        elif defect_type == "scratch":
            return self.inject_scratch(base), "scratch"
        elif defect_type == "crack":
            return self.inject_crack(base), "crack"
        elif defect_type == "corrosion":
            return self.inject_corrosion(base), "corrosion"
        elif defect_type == "dimensional":
            return self.inject_dimensional(base), "dimensional"
        else:
            return base, "normal"

    # Degradation Injection for Self-Healing Testing
    def inject_blur(self, img: np.ndarray, ksize: int = 21) -> np.ndarray:
        """Injects heavy defocus blur (simulates out-of-focus camera)."""
        return cv2.GaussianBlur(img, (ksize, ksize), 0)

    def inject_underexposure(self, img: np.ndarray, factor: float = 0.15) -> np.ndarray:
        """Injects severe underexposure (simulates failed factory strobe)."""
        return np.clip(img.astype(np.float32) * factor, 0, 255).astype(np.uint8)

    def inject_overexposure(self, img: np.ndarray, offset: int = 140) -> np.ndarray:
        """Injects severe overexposure/glare (simulates blinding specular reflection)."""
        return np.clip(img.astype(np.int32) + offset, 0, 255).astype(np.uint8)


class VirtualCamera:
    """Simulates a live industrial camera feed cycling through standard & defective frames."""
    
    def __init__(self, sequence: Optional[list] = None):
        self.generator = SyntheticIndustrialGenerator()
        self.sequence = sequence or ["normal", "scratch", "crack", "corrosion", "dimensional"]
        self.frame_idx = 0

    def read(self) -> Tuple[bool, np.ndarray, str]:
        defect = self.sequence[self.frame_idx % len(self.sequence)]
        frame, label = self.generator.generate(defect)
        self.frame_idx += 1
        return True, frame, label
