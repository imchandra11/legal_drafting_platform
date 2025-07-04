import numpy as np
from transformers import AutoTokenizer
import onnxruntime as ort
from typing import List, Dict

class LegalSuggestionEngine:
    def __init__(self, model_path: str, tokenizer_name: str = "nlpaueb/legal-bert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.session = ort.InferenceSession(model_path)
        self.labels = ["Clarity", "Compliance", "Ambiguity", "Completeness"]
        
    def generate_suggestions(self, text: str) -> List[Dict]:
        inputs = self.tokenizer(
            text, 
            truncation=True, 
            max_length=512,
            return_tensors="np",
            padding="max_length"
        )
        
        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64)
        }
        
        outputs = self.session.run(None, ort_inputs)
        logits = outputs[0]
        predictions = np.argmax(logits, axis=-1)
        
        suggestions = []
        for i, pred in enumerate(predictions[0]):
            if pred != 0:  # Only suggest if issue detected
                suggestion = self._create_suggestion(
                    issue_type=self.labels[i],
                    confidence=logits[0][i][pred],
                    context=text
                )
                suggestions.append(suggestion)
                
        return suggestions
    
    def _create_suggestion(self, issue_type: str, confidence: float, context: str) -> Dict:
        return {
            "issue_type": issue_type,
            "confidence": float(confidence),
            "recommendation": self._get_recommendation(issue_type),
            "context": context[:200] + "..." if len(context) > 200 else context,
            "reason": f"Potential {issue_type.lower()} issue detected with confidence {confidence:.2f}"
        }
    
    def _get_recommendation(self, issue_type: str) -> str:
        recommendations = {
            "Clarity": "Consider simplifying language or defining terms explicitly",
            "Compliance": "Verify against current regulations in target jurisdiction",
            "Ambiguity": "Add specificity to avoid multiple interpretations",
            "Completeness": "Include necessary clauses for enforceability"
        }
        return recommendations.get(issue_type, "Review section for potential improvements")