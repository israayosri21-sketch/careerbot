"""Démo Streamlit de CareerBot RH.  Lancer depuis la racine du projet : streamlit run app/streamlit_app.py"""
import json
import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.rag import CareerBot  # noqa: E402

# En ligne (Streamlit Cloud), la clé Mistral est rangée dans les "Secrets" de l'app, jamais dans le code.
try:
    if "MISTRAL_API_KEY" in st.secrets:
        os.environ["MISTRAL_API_KEY"] = st.secrets["MISTRAL_API_KEY"]
except Exception:
    pass

st.set_page_config(page_title="CareerBot RH", page_icon="💬", layout="wide")

RETRIEVERS = {"Hybride (recommandé)": "hybrid", "BM25": "bm25", "TF-IDF": "tfidf", "Dense": "dense"}
EXAMPLES = [
    "Combien de jours par semaine puis-je télétravailler ?",
    "Au bout de combien de temps puis-je changer de poste en interne ?",
    "Mon responsable peut-il être mon mentor ?",
    "Je viens au travail à vélo, ai-je une aide ?",
]


@st.cache_resource(show_spinner="Indexation des documents RH…")
def load_bot(retriever: str, dense: str):
    return CareerBot(retriever=retriever, dense=dense)


with st.sidebar:
    st.header("Réglages")
    ret_label = st.selectbox("Méthode de recherche", list(RETRIEVERS))
    dense = st.radio("Embeddings denses", ["auto", "e5", "lsa"], help="auto = E5 si installé, sinon LSA (local)")
    k = st.slider("Nombre d'extraits utilisés", 1, 5, 3)
    res_file = ROOT / "eval" / "results.json"
    if res_file.exists():
        st.divider()
        st.subheader("Évaluation (60 questions)")
        res = json.loads(res_file.read_text(encoding="utf-8"))
        st.dataframe(
            [{"Méthode": r["retriever"], "R@1": f"{r['recall@1']:.0%}", "R@3": f"{r['recall@3']:.0%}",
              "MRR": f"{r['mrr@10']:.2f}"} for r in res["results"]],
            hide_index=True)

bot = load_bot(RETRIEVERS[ret_label], dense)

st.title("CareerBot RH")
st.caption("Assistant RH du Groupe Orvane (entreprise fictive). Les réponses viennent uniquement des documents RH, avec leurs sources.")

cols = st.columns(len(EXAMPLES))
for c, ex in zip(cols, EXAMPLES):
    if c.button(ex):
        st.session_state["q"] = ex

q = st.text_input("Votre question", key="q", placeholder="Ex. : combien de jours de congé pour mon mariage ?")
if q:
    out = bot.ask(q, k)
    st.markdown(f"### Réponse\n{out['answer']}")
    st.caption(f"Recherche : {out['retriever']} · Génération : {out['generator']}")
    st.markdown("#### Sources")
    for s in out["sources"]:
        with st.expander(f"[{s['rank']}] {s['title']} › {s['section']}  (score {s['score']})", expanded=s["rank"] == 1):
            st.write(s["text"])
