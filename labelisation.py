import asyncio
import httpx
import json
from asyncio import Semaphore

# Limite de requêtes en parallèle
sem = Semaphore(50)

#Génération du prompt
def build_prompt(comment):
    return f"""Tu es un assistant qui aide une entreprise à identifier les commentaires vraiment utiles pour **améliorer son application mobile**.

Voici un commentaire utilisateur :
"{comment['content']}"

Attribue un score de pertinence entre 0 et 100, où :
- 0 = inutile (avis positif ou négatif sans détails)
- 100 = extrêmement utile pour corriger un problème, ajouter une fonctionnalité ou amméliorer l'app.

Les bugs ou données incorrectes doivent être notés hautement, même si l'utilisateur reste poli ou commence positivement.

Ne prends pas en compte les commentaires simplement positifs si rien ne peut être amélioré.

Réponds uniquement par le score, en entier."""


# Appel Ollama
async def annotate_comment(comment):
    prompt = build_prompt(comment)
    async with sem:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    "https://ollama.kube.isc.heia-fr.ch/api/generate",
                    json={"model": "llama3:70b", "prompt": prompt, "stream": False},
                    timeout=60.0,
                )
                response = resp.json()["response"].strip()
                comment["relevance_score"] = response  # Ajoute la réponse directement
            except Exception as e:
                comment["relevance_score"] = "error"
                print(f"❌ Erreur sur commentaire : {e}")
    return comment



async def main():
    with open("data/dataset.json", encoding="utf-8") as f:
        comments = json.load(f)
        comments = comments[:100]

    tasks = [annotate_comment(c) for c in comments]  # limite optionnelle
    results = await asyncio.gather(*tasks)

    with open("data/dataset_relevance.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(results)} commentaires annotés enregistrés dans annotated_comments.json")

asyncio.run(main())