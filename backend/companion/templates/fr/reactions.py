"""
Offline fallback reaction messages (French).
Used when LLM is unavailable. Messages are pre-validated, non-prescriptive.
"""

IN_RANGE = "C'est enregistré ! Votre glycémie est dans la cible — continuez comme ça."

HIGH = (
    "C'est noté. Une glycémie élevée peut avoir plusieurs causes : "
    "repas récent, stress, activité réduite. Parlez-en à votre médecin si ça se répète."
)

LOW = (
    "C'est enregistré. Une glycémie basse mérite attention — "
    "si vous ressentez des symptômes, suivez votre protocole habituel et contactez votre équipe soignante."
)
