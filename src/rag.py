"""CareerBot RH : pipeline RAG (Retrieval-Augmented Generation) sur un corpus RH.

Étapes : chargement et découpage du corpus -> recherche (BM25, TF-IDF, dense FAISS, hybride RRF)
-> génération d'une réponse citée (LLM local via Ollama, ou réponse extractive si aucun LLM n'est disponible).
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "data" / "corpus"

# ---------------------------------------------------------------- 1. Découpage

@dataclass
class Chunk:
    id: str          # "01_teletravail#Nombre de jours"
    doc: str         # "01_teletravail"
    title: str       # "Politique de télétravail"
    section: str     # "Nombre de jours"
    text: str        # texte de la section

    @property
    def full(self) -> str:
        # Le titre du document et de la section sont ajoutés au texte indexé :
        # cela aide la recherche quand la question reprend le thème plutôt que les mots exacts.
        return f"{self.title}. {self.section}. {self.text}"


def load_chunks(corpus_dir: Path = CORPUS_DIR, max_words: int = 120, overlap: int = 30) -> list[Chunk]:
    """Un chunk par section "## ". Les sections longues sont coupées en fenêtres glissantes."""
    chunks: list[Chunk] = []
    for f in sorted(corpus_dir.glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        title = re.search(r"^# (.+)$", raw, re.M).group(1).strip()
        parts = re.split(r"^## (.+)$", raw, flags=re.M)
        for i in range(1, len(parts), 2):
            section, body = parts[i].strip(), " ".join(parts[i + 1].split())
            words = body.split()
            if len(words) <= max_words:
                chunks.append(Chunk(f"{f.stem}#{section}", f.stem, title, section, body))
            else:
                step = max_words - overlap
                for j, start in enumerate(range(0, len(words), step)):
                    piece = " ".join(words[start:start + max_words])
                    chunks.append(Chunk(f"{f.stem}#{section}#{j}", f.stem, title, section, piece))
    return chunks

# ---------------------------------------------------------------- 2. Normalisation du texte

STOP = set("""a au aux avec ce ces dans de des du elle en et eux il je la le les leur lui ma mais me même mes moi mon
ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous c d j l m n s t y
été être est sont ai as avons avez ont suis es sommes êtes quoi quel quelle quels quelles combien comment quand où est-ce
puis peux peut faut dois doit si plus ça cela faire fait fais avoir aller va vais dire mon ma mes demain hier""".split())

try:
    import snowballstemmer
    _stem = snowballstemmer.stemmer("french").stemWord
except ImportError:  # le pipeline fonctionne aussi sans racinisation
    _stem = lambda w: w


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def tokenize(text: str) -> list[str]:
    text = text.lower().replace("’", "'")
    words = re.findall(r"[a-zà-ÿ0-9]+", text)
    return [strip_accents(_stem(w)) for w in words if w not in STOP and len(w) > 1]

# ---------------------------------------------------------------- 3. Recherche

class Retriever:
    name = "base"

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks

    def scores(self, query: str) -> np.ndarray:
        raise NotImplementedError

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        s = self.scores(query)
        top = np.argsort(-s)[:k]
        return [(self.chunks[i], float(s[i])) for i in top]


class BM25Retriever(Retriever):
    """Recherche lexicale classique : mots en commun, pondérés par leur rareté."""
    name = "BM25"

    def __init__(self, chunks):
        super().__init__(chunks)
        from rank_bm25 import BM25Okapi
        self.bm25 = BM25Okapi([tokenize(c.full) for c in chunks])

    def scores(self, query):
        return np.asarray(self.bm25.get_scores(tokenize(query)))


class TfidfRetriever(Retriever):
    """TF-IDF sur mots + n-grammes de caractères (plus tolérant aux variations d'orthographe)."""
    name = "TF-IDF"

    def __init__(self, chunks):
        super().__init__(chunks)
        from scipy.sparse import hstack
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._hstack = hstack
        docs = [" ".join(tokenize(c.full)) for c in chunks]
        self.word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(docs)
        self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True).fit(docs)
        self.X = self._vec(docs)

    def _vec(self, texts):
        from sklearn.preprocessing import normalize
        return normalize(self._hstack([self.word.transform(texts), self.char.transform(texts)]).tocsr())

    def scores(self, query):
        q = self._vec([" ".join(tokenize(query))])
        return (self.X @ q.T).toarray().ravel()


class LSAEncoder:
    """Encodeur dense local (TF-IDF + SVD). Sert de solution de repli quand aucun modèle
    d'embeddings pré-entraîné n'est disponible ; il ne capture pas de vrais synonymes."""
    name = "LSA"

    def __init__(self, chunks, dim: int = 48):
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        docs = [" ".join(tokenize(c.full)) for c in chunks]
        self.tfidf = TfidfVectorizer(sublinear_tf=True).fit(docs)
        self.svd = TruncatedSVD(n_components=min(dim, len(docs) - 1), random_state=0).fit(self.tfidf.transform(docs))

    def encode(self, texts, is_query=False):
        return self.svd.transform(self.tfidf.transform([" ".join(tokenize(t)) for t in texts]))


class E5Encoder:
    """Embeddings sémantiques multilingues (intfloat/multilingual-e5-small, ~470 Mo, CPU suffisant).
    À lancer sur une machine qui a accès à Hugging Face : pip install sentence-transformers."""
    name = "E5"

    def __init__(self, chunks=None, model: str = "intfloat/multilingual-e5-small"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)

    def encode(self, texts, is_query=False):
        prefix = "query: " if is_query else "passage: "  # préfixes recommandés pour la famille E5
        return self.model.encode([prefix + t for t in texts], normalize_embeddings=True)


class DenseRetriever(Retriever):
    """Recherche par similarité de vecteurs, indexés dans FAISS (produit scalaire sur vecteurs normalisés = cosinus)."""

    def __init__(self, chunks, encoder):
        super().__init__(chunks)
        import faiss
        self.encoder = encoder
        self.name = f"Dense ({encoder.name})"
        V = np.asarray(encoder.encode([c.full for c in chunks]), dtype="float32")
        faiss.normalize_L2(V)
        self.index = faiss.IndexFlatIP(V.shape[1])
        self.index.add(V)
        self._faiss = faiss

    def scores(self, query):
        q = np.asarray(self.encoder.encode([query], is_query=True), dtype="float32")
        self._faiss.normalize_L2(q)
        s, idx = self.index.search(q, len(self.chunks))
        out = np.empty(len(self.chunks), dtype="float32")
        out[idx[0]] = s[0]
        return out


class HybridRetriever(Retriever):
    """Fusion des classements par Reciprocal Rank Fusion : score = somme de 1 / (k + rang)."""

    def __init__(self, chunks, retrievers: list[Retriever], k: int = 60):
        super().__init__(chunks)
        self.retrievers, self.k = retrievers, k
        self.name = "Hybride (" + " + ".join(r.name for r in retrievers) + ")"

    def scores(self, query):
        total = np.zeros(len(self.chunks))
        for r in self.retrievers:
            ranks = np.empty(len(self.chunks))
            ranks[np.argsort(-r.scores(query))] = np.arange(1, len(self.chunks) + 1)
            total += 1.0 / (self.k + ranks)
        return total


def build_retrievers(chunks, dense: str = "auto") -> dict[str, Retriever]:
    """dense = "e5", "lsa" ou "auto" (E5 si disponible, sinon LSA)."""
    bm25, tfidf = BM25Retriever(chunks), TfidfRetriever(chunks)
    enc = None
    if dense in ("e5", "auto"):
        try:
            enc = E5Encoder(chunks)
        except Exception as e:  # pas de sentence-transformers ou pas d'accès au modèle
            if dense == "e5":
                raise
            print(f"[info] E5 indisponible ({type(e).__name__}), repli sur LSA.")
    enc = enc or LSAEncoder(chunks)
    dense_r = DenseRetriever(chunks, enc)
    return {"bm25": bm25, "tfidf": tfidf, "dense": dense_r,
            "hybrid": HybridRetriever(chunks, [bm25, tfidf, dense_r])}

# ---------------------------------------------------------------- 4. Génération

PROMPT = """Tu es CareerBot, l'assistant RH du Groupe Orvane.
Réponds à la question en français, en 2 à 4 phrases, uniquement à partir des extraits ci-dessous.
Cite tes sources entre crochets, par exemple [1].
Si les extraits ne contiennent pas la réponse, dis : « Je ne trouve pas cette information dans les documents RH, contactez l'équipe People Experience. »

Extraits :
{context}

Question : {question}
Réponse :"""


def build_context(hits) -> str:
    return "\n".join(f"[{i}] {c.title} > {c.section} : {c.text}" for i, (c, _) in enumerate(hits, 1))


class OllamaGenerator:
    """LLM local via Ollama (https://ollama.com) : `ollama pull mistral` puis `ollama serve`."""
    def __init__(self, model: str = "mistral", url: str = "http://localhost:11434/api/generate"):
        self.model, self.url = model, url
        self.name = f"{model.capitalize()} (Ollama, local)"

    def available(self) -> bool:
        try:
            urllib.request.urlopen(self.url.replace("/api/generate", "/api/tags"), timeout=2)
            return True
        except Exception:
            return False

    def answer(self, question, hits) -> str:
        body = json.dumps({"model": self.model, "prompt": PROMPT.format(context=build_context(hits), question=question),
                           "stream": False, "options": {"temperature": 0.1}}).encode()
        req = urllib.request.Request(self.url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())["response"].strip()


class MistralAPIGenerator:
    """LLM Mistral hébergé (La Plateforme, https://console.mistral.ai) : clé dans la variable MISTRAL_API_KEY.
    Sert pour la version en ligne, où Ollama n'est pas disponible."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY", "")
        self.model = model or os.environ.get("MISTRAL_MODEL", "mistral-small-latest")
        self.name = f"Mistral ({self.model}, API)"

    def available(self) -> bool:
        return bool(self.api_key)

    def answer(self, question, hits) -> str:
        body = json.dumps({"model": self.model, "temperature": 0.1, "max_tokens": 400,
                           "messages": [{"role": "user", "content": PROMPT.format(context=build_context(hits), question=question)}]}).encode()
        req = urllib.request.Request("https://api.mistral.ai/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json", "Accept": "application/json",
                                              "User-Agent": "careerbot-rh/1.0", "Authorization": f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:  # message lisible : code HTTP + début de la réponse de l'API
            detail = e.read().decode("utf-8", "replace")[:200]
            raise RuntimeError(f"API Mistral : erreur HTTP {e.code} {detail}") from None


class ExtractiveGenerator:
    """Sans LLM : renvoie les phrases des extraits les plus proches de la question (mots en commun pondérés
    par leur rareté dans le corpus), avec leur source. Refuse de répondre si aucun mot important ne correspond."""
    name = "Extractif"

    def __init__(self, chunks: list[Chunk] | None = None):
        chunks = chunks or load_chunks()
        n = len(chunks)
        df: dict[str, int] = {}
        for c in chunks:
            for w in set(tokenize(c.full)):
                df[w] = df.get(w, 0) + 1
        self.idf = {w: np.log((n + 1) / (d + 0.5)) for w, d in df.items()}

    def answer(self, question, hits, n_sentences: int = 2, min_score: float = 1.5) -> str:
        q = set(tokenize(question))
        cands = []
        for i, (c, _) in enumerate(hits, 1):
            for sent in re.split(r"(?<=[.!?])\s+", c.text):
                score = sum(self.idf.get(w, 0) for w in q & set(tokenize(sent)))
                cands.append((score - 1.0 * (i - 1), sent, i))
        cands.sort(key=lambda x: -x[0])
        if not cands or cands[0][0] < min_score:
            return "Je ne trouve pas cette information dans les documents RH, contactez l'équipe People Experience."
        same = [x for x in cands[1:] if x[2] == cands[0][2] and x[0] >= 0.5 * cands[0][0]]
        best = [cands[0]] + same[: n_sentences - 1]
        return " ".join(f"{sent} [{i}]" for _, sent, i in best)


class CareerBot:
    def __init__(self, retriever: str = "hybrid", dense: str = "auto", llm: str = "auto"):
        self.chunks = load_chunks()
        self.retrievers = build_retrievers(self.chunks, dense)
        self.retriever = self.retrievers[retriever]
        self.extractive = ExtractiveGenerator(self.chunks)
        self.generator = self.extractive
        candidates = {"ollama": [OllamaGenerator()], "mistral-api": [MistralAPIGenerator()],
                      "auto": [MistralAPIGenerator(), OllamaGenerator()]}.get(llm, [])
        for g in candidates:
            if g.available():
                self.generator = g
                break

    def ask(self, question: str, k: int = 3) -> dict:
        hits = self.retriever.search(question, k)
        gen, error = self.generator, None
        try:
            answer = gen.answer(question, hits)
        except Exception as e:  # LLM injoignable ou quota dépassé : on retombe sur la réponse extractive
            error = str(e) or type(e).__name__
            print(f"[info] {gen.name} indisponible ({error}), réponse extractive.")
            gen = self.extractive
            answer = gen.answer(question, hits)
        return {"question": question, "answer": answer, "generator": gen.name, "llm_error": error,
                "retriever": self.retriever.name,
                "sources": [{"rank": i, "id": c.id, "title": c.title, "section": c.section, "text": c.text, "score": round(s, 4)}
                            for i, (c, s) in enumerate(hits, 1)]}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Poser une question à CareerBot RH")
    ap.add_argument("question")
    ap.add_argument("--retriever", default="hybrid", choices=["bm25", "tfidf", "dense", "hybrid"])
    ap.add_argument("--dense", default="auto", choices=["auto", "e5", "lsa"])
    ap.add_argument("-k", type=int, default=3)
    ap.add_argument("--llm", default="auto", choices=["auto", "ollama", "mistral-api", "none"])
    a = ap.parse_args()
    res = CareerBot(a.retriever, a.dense, a.llm).ask(a.question, a.k)
    print(f"\n{res['answer']}\n\n[{res['retriever']} · {res['generator']}]")
    for s in res["sources"]:
        print(f"  [{s['rank']}] {s['title']} > {s['section']}  (score {s['score']})")
