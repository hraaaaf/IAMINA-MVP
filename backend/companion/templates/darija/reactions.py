"""
Offline fallback reaction messages (Moroccan Darija).
Used when LLM is unavailable. Messages are pre-validated, non-prescriptive.
Note: These messages do NOT replace medical advice — always defer clinical decisions to the physician.
"""

IN_RANGE = "Mzyan! Sukkar dyalek f l-mijan — kml hkka w sir b-xir."

HIGH = (
    "Msjjl. Sukkar 3ali ykon 3andu bzzaf d-l-asbab: makla, dghit, wlla qillat l-haraka. "
    "Had chi ila tkarrar, had l-kalam m3a tbibk."
)

LOW = (
    "Msjjl. Sukkar naqs khasso l-intibah — "
    "ila 3ndek l-3radat, tba3 l-brotokol dyalek w tkllm m3a l-fariq dyalek d-sihha."
)
