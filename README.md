# CareerBot RH : un assistant RAG pour les questions RH

CareerBot répond aux questions des collaborateurs à partir des documents RH d'une entreprise fictive, le Groupe Orvane, et cite toujours ses sources. S'il ne trouve pas la réponse, il le dit au lieu d'inventer.

## Structure

```
data/build_corpus.py     génère les 16 documents RH (data/corpus/*.md)
src/rag.py               pipeline : découpage, recherche (BM25, TF-IDF, dense FAISS, hybride RRF), génération
eval/questions.py        génère les 60 questions annotées (eval/questions.jsonl)
eval/evaluate.py         Recall@1/3/5, MRR@10, test de refus hors sujet, graphique
app/streamlit_app.py     démo Streamlit
app/web_demo.html        démo web autonome (BM25 dans le navigateur)
```

## Installation

```bash
pip install -r requirements.txt
python data/build_corpus.py
python eval/questions.py
```

Pour les embeddings sémantiques (recommandé), installer aussi `sentence-transformers`. Le modèle `intfloat/multilingual-e5-small` (~470 Mo) se télécharge au premier lancement.

Pour une génération par LLM local : installer [Ollama](https://ollama.com), puis `ollama pull mistral`. Sans Ollama, CareerBot donne une réponse extractive : des phrases tirées mot pour mot des documents.

## Mettre la démo en ligne avec Mistral (Streamlit Cloud)

En ligne, Ollama n'est pas disponible : CareerBot appelle alors l'API Mistral (modèle `mistral-small-latest`, modifiable avec la variable `MISTRAL_MODEL`).

1. Créer une clé API sur [console.mistral.ai](https://console.mistral.ai) (offre gratuite).
2. Mettre ce dossier sur GitHub (la clé n'est jamais dans le code).
3. Sur [share.streamlit.io](https://share.streamlit.io), créer une app : fichier principal `app/streamlit_app.py`.
4. Dans *Advanced settings > Secrets*, coller : `MISTRAL_API_KEY = "ta-clé"`.

Ordre de choix du générateur : API Mistral si une clé est présente, sinon Mistral local via Ollama, sinon réponse extractive. Si le LLM ne répond pas (quota, réseau), la réponse extractive prend le relais.

## Utilisation

```bash
python -m src.rag "Combien de jours par semaine puis-je télétravailler ?"
python -m src.rag "Mon manager peut-il être mon mentor ?" --retriever bm25
streamlit run app/streamlit_app.py
```

## Évaluation

```bash
python -m eval.evaluate --dense lsa   # encodeur dense local, sans téléchargement
python -m eval.evaluate --dense e5    # embeddings multilingual-e5-small
```

Résultats avec l'encodeur local LSA (60 questions, 55 passages) :

| Méthode | Recall@1 | Recall@3 | Recall@5 | MRR@10 |
|---|---|---|---|---|
| BM25 | 66,7 % | 90,0 % | 91,7 % | 0,781 |
| TF-IDF (mots + caractères) | 73,3 % | 91,7 % | 93,3 % | 0,815 |
| Dense (LSA) | 65,0 % | 86,7 % | 90,0 % | 0,759 |
| Hybride (BM25 + TF-IDF + Dense, RRF) | 68,3 % | 91,7 % | 93,3 % | 0,789 |

Questions hors sujet correctement refusées : 5 sur 6.

Les 5 questions que l'hybride ne place pas dans le top 3 sont surtout des écarts de vocabulaire (fauteuil / siège, chef / manager, master / formation diplômante, je me marie / mariage). C'est ce que les embeddings E5 doivent améliorer : relancer l'évaluation avec `--dense e5` pour le mesurer.

## Limites

- Corpus fictif et petit (16 documents) : les chiffres sont indicatifs.
- L'évaluation mesure la recherche, pas encore la fidélité des réponses générées par le LLM.
- Les questions ont été écrites et annotées à la main par une seule personne.
