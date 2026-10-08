import os
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger

GRIEVANCE_CATEGORIES = [
    "academic",
    "infrastructure",
    "hostel",
    "transport",
    "internet",
    "laboratory",
    "administration",
    "library",
    "security",
    "other",
]

GRIEVANCE_PRIORITIES = ["low", "medium", "high", "critical"]

CATEGORY_KEYWORDS = {
    "hostel": ["hostel", "room", "mess", "food", "warden", "hot water", "bed", "bathroom", "cleaning"],
    "transport": ["bus", "driver", "route", "late", "timing", "pass", "seat", "transport", "pickup"],
    "internet": ["wifi", "internet", "network", "lan", "connection", "firewall", "portal", "router"],
    "laboratory": ["lab", "equipment", "computer", "machine", "oscilloscope", "chemical", "component", "hardware", "software"],
    "infrastructure": ["fan", "light", "projector", "ac", "desk", "bench", "water cooler", "restroom", "building", "lift"],
    "academic": ["marks", "faculty", "teaching", "syllabus", "attendance", "lecture", "assignment", "evaluation"],
    "library": ["book", "journal", "library card", "fine", "digital library", "librarian", "return"],
    "security": ["ragging", "harassment", "lost", "theft", "id check", "guard", "safety", "threat"],
    "administration": ["fee receipt", "certificate", "office", "counter", "clerk", "staff", "delay", "scholarship"],
}

CATEGORY_TO_DEPARTMENT = {
    "hostel": "Hostel Affairs",
    "transport": "Transport Division",
    "internet": "IT Infrastructure & Networks",
    "laboratory": "Lab Incharge / Academic Labs",
    "infrastructure": "Campus Maintenance",
    "academic": "Academic Dean / HOD",
    "library": "Central Library",
    "security": "Campus Vigilance & Security",
    "administration": "Administrative Office",
    "other": "Dean of Student Affairs",
}

CRITICAL_KEYWORDS = ["ragging", "harassment", "assault", "fire", "electrical shock", "injury", "threat", "emergency"]
HIGH_KEYWORDS = ["water shortage", "food poisoning", "exam tomorrow", "bus breakdown", "server down", "wifi down during test"]
LOW_KEYWORDS = ["suggestion", "book request", "timing request", "slight noise", "cosmetic"]


class GrievanceClassifier:
    """
    Hugging Face Transformers-based Grievance Classification Engine.
    Predicts category, priority, responsible department, and confidence.
    Enforces human-in-the-loop confirmation if confidence falls below threshold.
    """

    def __init__(self):
        self.model_name = settings.HF_GRIEVANCE_MODEL
        self.threshold = settings.CLASSIFIER_CONFIDENCE_THRESHOLD
        self._custom_model_dir = "./models/grievance_model"
        self._is_loaded = False
        self.pipeline = None

    def load_model(self) -> bool:
        """Load fine-tuned transformer model if present on disk."""
        try:
            from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

            if os.path.exists(self._custom_model_dir):
                tokenizer = AutoTokenizer.from_pretrained(self._custom_model_dir)
                model = AutoModelForSequenceClassification.from_pretrained(self._custom_model_dir)
                self.pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer, return_all_scores=True)
                self._is_loaded = True
                logger.info("Custom fine-tuned grievance classifier loaded.")
                return True
            else:
                logger.info("Base model specified. Heuristic/hybrid classifier active until fine-tuning.")
                self._is_loaded = False
                return True
        except Exception as e:
            logger.warning(f"Transformer grievance model loading deferred: {str(e)}")
            self._is_loaded = False
            return False

    def classify(self, title: str, description: str) -> Dict[str, Any]:
        """
        Classify grievance into category, priority, responsible department, and confidence.
        Calculates confidence score; if confidence < threshold, requires_confirmation is set to True.
        """
        full_text = f"{title} {description}".lower()

        # If fine-tuned transformer weights exist, use them
        if self._is_loaded and self.pipeline:
            try:
                results = self.pipeline(full_text[:512])[0]
                sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
                top = sorted_results[0]
                category = top["label"].lower()
                confidence = float(top["score"])

                priority = self._derive_priority(full_text)
                dept = CATEGORY_TO_DEPARTMENT.get(category, "Student Affairs")
                requires_confirmation = confidence < self.threshold

                return {
                    "category": category,
                    "priority": priority,
                    "department": dept,
                    "confidence": round(confidence, 4),
                    "requires_confirmation": requires_confirmation,
                }
            except Exception as e:
                logger.error(f"Inference error in grievance classifier: {str(e)}")

        # Heuristic / Keyword-based classification with calibrated confidence
        best_category = "other"
        highest_score = 0.0

        for category, keywords in CATEGORY_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in full_text)
            if matches > 0:
                score = min(0.96, 0.65 + (matches * 0.10))
            else:
                score = 0.15
            if score > highest_score:
                highest_score = score
                best_category = category

        confidence = round(highest_score if highest_score > 0.40 else 0.50, 4)
        priority = self._derive_priority(full_text)
        dept = CATEGORY_TO_DEPARTMENT.get(best_category, "Dean of Student Affairs")
        requires_confirmation = confidence < self.threshold

        return {
            "category": best_category,
            "priority": priority,
            "department": dept,
            "confidence": confidence,
            "requires_confirmation": requires_confirmation,
        }

    def _derive_priority(self, text: str) -> str:
        """Determine ticket urgency from contextual severity tokens."""
        if any(w in text for w in CRITICAL_KEYWORDS):
            return "critical"
        if any(w in text for w in HIGH_KEYWORDS):
            return "high"
        if any(w in text for w in LOW_KEYWORDS):
            return "low"
        return "medium"


grievance_classifier = GrievanceClassifier()
