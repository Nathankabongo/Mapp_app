from typing import Dict, Any, List
from datetime import datetime

class ExpertValidation:
    """
    Gestion des feedbacks géologiques (Expert Validation Loop).
    Permet au SGN-C de corriger les prédictions (Pertinent, À vérifier, Faux positif)
    et de renvoyer ces données dans la boucle d'apprentissage.
    """
    
    def __init__(self):
        self.feedbacks: List[Dict[str, Any]] = []
        
    def add_feedback(self, zone: str, status: str, comment: str, user_id: str) -> Dict[str, Any]:
        """Ajoute un feedback expert sur une prédiction."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "zone": zone,
            "status": status,  # "Pertinent", "À vérifier", "Faux positif"
            "comment": comment,
            "user_id": user_id
        }
        self.feedbacks.append(record)
        return record
        
    def get_training_dataset(self) -> List[Dict[str, Any]]:
        """Retourne les feedbacks pour réentraîner le modèle."""
        return [f for f in self.feedbacks if f["status"] in ["Pertinent", "Faux positif"]]
