"""Pure-Python TF-IDF engine (no scikit-learn / compiled extensions).

Why: on locked-down Windows machines an Application Control policy can block the compiled
``.pyd`` files shipped with scikit-learn. TF-IDF is small enough to implement directly, using the
same defaults as scikit-learn's ``TfidfVectorizer(ngram_range=(1, 2), stop_words="english")``:
lower-casing, ``\\b\\w\\w+\\b`` tokens, smoothed IDF ``ln((1+n)/(1+df)) + 1`` and L2 normalisation.
Vectors are sparse ``{term: weight}`` dicts.
"""
import logging
import math
import re
from collections import Counter
from typing import Dict, List

logger = logging.getLogger("rag_embeddings")

SparseVector = Dict[str, float]

_TOKEN_RE = re.compile(r"(?u)\b\w\w+\b")
STOP_WORDS = frozenset("""
a about above after again against all almost also although always am among an and any are around as at be because been before being
below between both but by can cannot could did do does doing down during each either else enough even ever every few for from further
had has have having he her here hers herself him himself his how however i if in into is it its itself just least less may me might
more most much must my myself neither no nor not now of off often on once only or other others our ours ourselves out over own per
rather same shall she should since so some such than that the their theirs them themselves then there these they this those though
through thus to too toward under until up upon us very via was we were what when where whether which while who whom whose why will
with within without would yet you your yours yourself yourselves
""".split())


def _analyze(text: str) -> List[str]:
    """Lower-case, tokenise, drop stop words, then add bigrams of the remaining tokens."""
    words = [w for w in _TOKEN_RE.findall(str(text or "").lower()) if w not in STOP_WORDS]
    return words + [f"{a} {b}" for a, b in zip(words, words[1:])]


def _normalise(vec: SparseVector) -> SparseVector:
    norm = math.sqrt(sum(v * v for v in vec.values()))
    return {t: v / norm for t, v in vec.items()} if norm else {}


class TFIDFEmbeddingEngine:
    """Lightweight TF-IDF embedding engine for local RAG search."""

    def __init__(self):
        self.idf: Dict[str, float] = {}
        self.is_fitted = False

    def fit_transform(self, texts: List[str]) -> List[SparseVector]:
        clean = [str(t or "").strip() for t in texts]
        if not clean or not any(clean):
            self.is_fitted = False
            return []
        docs = [Counter(_analyze(t)) for t in clean]
        if not any(docs):
            self.is_fitted = False
            raise ValueError("empty vocabulary; perhaps the documents only contain stop words")
        df: Counter = Counter()
        for d in docs:
            df.update(d.keys())
        n = len(docs)
        self.idf = {term: math.log((1 + n) / (1 + count)) + 1.0 for term, count in df.items()}
        self.is_fitted = True
        return [self._vectorise(d) for d in docs]

    def _vectorise(self, counts: Counter) -> SparseVector:
        return _normalise({t: c * self.idf[t] for t, c in counts.items() if t in self.idf})

    def transform(self, texts: List[str]) -> List[SparseVector]:
        if not self.is_fitted:
            raise ValueError("Vectorization engine has not been fitted on document corpus yet.")
        return [self._vectorise(Counter(_analyze(t))) for t in texts]


def cosine(a: SparseVector, b: SparseVector) -> float:
    """Cosine similarity of two L2-normalised sparse vectors (their dot product)."""
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b.get(t, 0.0) for t, w in a.items())
