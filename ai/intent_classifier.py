import os
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger

INTENT_LABELS = [
    "academic_information",
    "student_services",
    "events",
    "opportunities",
    "placement",
    "attendance",
    "examination",
    "documents",
    "grievance",
    "general",
]

# Keyword / semantic anchors for zero-shot or fallback classification
INTENT_KEYWORDS: Dict[str, List[str]] = {
    "academic_information": ["syllabus", "curriculum", "courses", "credits", "faculty", "classes", "timetable", "gpa", "cgpa", "subject"],
    "student_services": ["id card", "canteen", "hostel admission", "bonafide certificate", "medical leave", "outpass", "scholarship form"],
    "events": ["symposium", "tech fest", "culturals", "hackathon", "workshop", "annual day", "sports day", "seminar", "conference"],
    "opportunities": ["internship", "fellowship", "research grant", "project competition", "hackathon opportunity", "scholarship"],
    "placement": ["campus drive", "tcs", "wipro", "placement cell", "interview", "salary package", "training", "resume", "aptitude"],
    "attendance": ["attendance percentage", "leave letter", "od", "on duty", "shortage", "biometric", "absent", "condonation"],
    "examination": ["hall ticket", "semester exam", "arrears", "results", "revaluation", "grade sheet", "internal marks", "model exam"],
    "documents": ["transcript", "degree certificate", "bonafide", "tc", "transfer certificate", "conduct certificate", "marksheet"],
    "grievance": ["complaint", "issue", "broken", "dirty", "ragging", "food quality", "wifi down", "fan repair", "bus delay", "grievance"],
    "general": ["college timing", "principal", "campus address", "contact number", "holiday", "working day", "library hours"],
}


class IntentClassifier:
    """
    Hugging Face Transformers-based Intent Classification Engine.
    Configurable via HF_INTENT_MODEL environment variable.
    Includes confidence scoring, threshold gating, and fallback heuristics.
    """

    def __init__(self):
        self.model_name = settings.HF_INTENT_MODEL
        self.threshold = settings.CLASSIFIER_CONFIDENCE_THRESHOLD
        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self._is_loaded = False
        self._custom_model_dir = "./models/intent_model"

    def load_model(self) -> bool:
        """Attempt to load trained transformer weights or Hugging Face model."""
        try:
            from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

            model_path = self._custom_model_dir if os.path.exists(self._custom_model_dir) else self.model_name
            logger.info(f"Loading intent classification model from: {model_path}")

            if os.path.exists(self._custom_model_dir):
                self.tokenizer = AutoTokenizer.from_pretrained(self._custom_model_dir)
                self.model = AutoModelForSequenceClassification.from_pretrained(self._custom_model_dir)
                self.pipeline = pipeline("text-classification", model=self.model, tokenizer=self.tokenizer, return_all_scores=True)
                self._is_loaded = True
                logger.info("Custom fine-tuned intent classifier loaded successfully.")
                return True
            else:
                # Starting model without custom heads yet: pipeline will initialize on first training
                logger.info(f"Base model '{self.model_name}' specified. Hybrid semantic fallback active until fine-tuning.")
                self._is_loaded = False
                return True
        except Exception as e:
            logger.warning(f"Transformer intent model loading deferred: {str(e)}")
            self._is_loaded = False
            return False

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict intent from query with confidence score.
        If confidence < threshold, flag requires_confirmation=True.
        """
        text_lower = text.lower().strip()

        # If fine-tuned transformer pipeline is active, run model inference
        if self._is_loaded and self.pipeline:
            try:
                results = self.pipeline(text)[0]
                sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
                top = sorted_results[0]
                label = top["label"].lower()
                confidence = float(top["score"])

                requires_confirmation = confidence < self.threshold
                return {
                    "intent": label,
                    "confidence": round(confidence, 4),
                    "requires_confirmation": requires_confirmation,
                    "probabilities": {r["label"]: round(float(r["score"]), 4) for r in sorted_results[:5]},
                }
            except Exception as e:
                logger.error(f"Inference error in intent model: {str(e)}")

        # Resilient heuristic & keyword scoring fallback
        best_intent = "general"
        highest_score = 0.0
        scores: Dict[str, float] = {}

        for intent, keywords in INTENT_KEYWORDS.items():
            match_count = sum(1 for kw in keywords if kw in text_lower)
            if match_count > 0:
                score = min(0.95, 0.60 + (match_count * 0.15))
            else:
                score = 0.10
            scores[intent] = round(score, 4)
            if score > highest_score:
                highest_score = score
                best_intent = intent

        confidence = round(highest_score, 4) if highest_score > 0 else 0.50
        requires_confirmation = confidence < self.threshold

        return {
            "intent": best_intent,
            "confidence": confidence,
            "requires_confirmation": requires_confirmation,
            "probabilities": scores,
        }


intent_classifier = IntentClassifier()
