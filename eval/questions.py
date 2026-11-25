"""Jeu d'évaluation : 60 questions de collaborateurs, chacune reliée à la section qui contient la réponse.
Les questions sont reformulées (synonymes, langage parlé) pour ne pas reprendre mot pour mot le texte."""
import json
from pathlib import Path

Q = [
# télétravail
("Combien de jours par semaine je peux bosser de chez moi ?", "01_teletravail", "Nombre de jours"),
("Je travaille en boutique, est-ce que j'ai droit au télétravail ?", "01_teletravail", "Éligibilité"),
("Est-ce que l'entreprise rembourse ma connexion internet quand je suis à la maison ?", "01_teletravail", "Indemnité"),
("Qui paie mon fauteuil de bureau pour travailler à domicile ?", "01_teletravail", "Indemnité"),
("Mon manager peut-il refuser ma demande de travail à distance sans explication ?", "01_teletravail", "Demande"),
# congés
("Combien de jours de vacances j'accumule chaque mois ?", "02_conges", "Congés payés"),
("Que deviennent mes jours de RTT non utilisés en fin d'année ?", "02_conges", "RTT"),
("Comment financer un congé sabbatique avec mes jours mis de côté ?", "02_conges", "Compte épargne-temps"),
("Je me marie le mois prochain, ai-je des jours offerts ?", "02_conges", "Absences pour événements familiaux"),
("Combien de jours d'absence pour la naissance de mon bébé ?", "02_conges", "Absences pour événements familiaux"),
# mobilité
("Au bout de combien de temps puis-je changer de poste en interne ?", "03_mobilite_interne", "Conditions"),
("Dois-je demander la permission à mon chef pour candidater ailleurs dans le groupe ?", "03_mobilite_interne", "Conditions"),
("Est-ce que je garde mon ancienneté si je pars dans une autre entité du groupe ?", "03_mobilite_interne", "Mobilité entre filiales"),
("Qui paie le déménagement si je change de ville pour un nouveau poste ?", "03_mobilite_interne", "Accompagnement"),
("Les postes ouverts sont-ils d'abord proposés aux salariés ?", "03_mobilite_interne", "Principe"),
("Peut-on parler à quelqu'un pour préparer un changement de poste ?", "03_mobilite_interne", "Accompagnement"),
# formation
("Combien d'argent est versé sur mon CPF chaque année ?", "04_formation", "Compte personnel de formation"),
("Le groupe complète-t-il mon compte formation ?", "04_formation", "Compte personnel de formation"),
("Où trouver des cours en ligne sur l'intelligence artificielle ?", "04_formation", "Orvane Academy"),
("Combien d'heures de e-learning puis-je faire sur mon temps de travail ?", "04_formation", "Orvane Academy"),
("Est-ce que l'entreprise peut payer mon master ?", "04_formation", "Formations diplômantes"),
("Quand est décidé le programme des formations de l'année ?", "04_formation", "Plan de formation"),
# entretiens
("À quelle période ont lieu les évaluations de fin d'année ?", "05_entretien_annuel", "Entretien annuel"),
("Combien d'objectifs sont fixés pour l'année ?", "05_entretien_annuel", "Entretien annuel"),
("Quelle différence entre l'entretien pro et l'entretien annuel ?", "05_entretien_annuel", "Entretien professionnel"),
("Quels sont les niveaux de notation de la performance ?", "05_entretien_annuel", "Évaluation"),
# onboarding
("Combien de temps dure le programme d'accueil des nouveaux ?", "06_onboarding", "Parcours d'intégration"),
("Qui m'aide à comprendre la culture de l'entreprise quand j'arrive ?", "06_onboarding", "Parrainage"),
("C'est quoi le rapport d'étonnement ?", "06_onboarding", "Rapport d'étonnement"),
("Quand vais-je recevoir mon ordinateur avant de commencer ?", "06_onboarding", "Avant l'arrivée"),
# mentorat
("Combien de temps dure un mentorat ?", "07_mentorat", "Durée et rythme"),
("Quand puis-je m'inscrire pour avoir un mentor ?", "07_mentorat", "Inscription"),
("Faut-il beaucoup d'expérience pour accompagner quelqu'un comme mentor ?", "07_mentorat", "Inscription"),
("Mon responsable peut-il être mon mentor ?", "07_mentorat", "Mise en relation"),
("À quoi sert le programme de mentorat ?", "07_mentorat", "Objectif"),
# réseau interne
("Comment rencontrer des collègues d'autres filiales pour échanger sur nos parcours ?", "08_reseau_interne", "Cafés carrière"),
("Peut-on parler de nos clients pendant un café carrière ?", "08_reseau_interne", "Cafés carrière"),
("Existe-t-il un groupe pour les jeunes de moins de 30 ans ?", "08_reseau_interne", "Réseaux d'affinité"),
("À quelle fréquence se retrouvent les communautés d'experts ?", "08_reseau_interne", "Communautés métiers"),
# rémunération
("Quand mon salaire est-il augmenté ?", "09_remuneration", "Révision salariale"),
("Quel est le montant maximum de mon bonus de cadre ?", "09_remuneration", "Rémunération variable"),
("Quelle part de la mutuelle est payée par l'employeur ?", "09_remuneration", "Avantages"),
("Je viens au travail à vélo, ai-je une aide ?", "09_remuneration", "Transport"),
("Quelle réduction ai-je sur les produits de la marque ?", "09_remuneration", "Avantages"),
# frais
("Dans quel délai dois-je envoyer mes justificatifs de dépenses ?", "10_notes_de_frais", "Déclaration"),
("Quel est le plafond pour une nuit d'hôtel à Paris ?", "10_notes_de_frais", "Plafonds"),
("Puis-je prendre l'avion pour un trajet de 3 heures ?", "10_notes_de_frais", "Transport professionnel"),
# déconnexion
("Suis-je obligé de répondre aux mails le soir ?", "11_deconnexion", "Principe"),
("À partir de quelle heure ne doit-on plus envoyer d'e-mails ?", "11_deconnexion", "Plages protégées"),
("Combien de temps dure une réunion par défaut ?", "11_deconnexion", "Réunions"),
# parentalité
("Mon salaire est-il maintenu pendant mon congé maternité ?", "12_parentalite", "Congé maternité et paternité"),
("Puis-je reprendre à temps partiel après mon congé maternité ?", "12_parentalite", "Retour de congé"),
("Existe-t-il une aide pour la crèche ?", "12_parentalite", "Garde d'enfants"),
# handicap
("À qui m'adresser pour adapter mon poste à mon handicap ?", "13_handicap", "Référent handicap"),
("Combien de jours pour mes démarches RQTH ?", "13_handicap", "Jours d'absence"),
# données
("Combien de temps mes données sont-elles gardées après mon départ ?", "14_donnees_personnelles", "Durée de conservation"),
("Comment demander la suppression de mes données personnelles ?", "14_donnees_personnelles", "Droits"),
# code de conduite / départ
("Un fournisseur m'offre un cadeau de 150 euros, puis-je l'accepter ?", "15_code_conduite", "Cadeaux"),
("Quelle est la durée de préavis pour un cadre qui démissionne ?", "16_depart", "Préavis"),
("Si je reviens dans le groupe après l'avoir quitté, refais-je une période d'essai ?", "16_depart", "Réseau des anciens"),
]

if __name__ == "__main__":
    out = Path(__file__).parent / "questions.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for i, (q, d, s) in enumerate(Q, 1):
            f.write(json.dumps({"id": i, "question": q, "doc": d, "section": s}, ensure_ascii=False) + "\n")
    print(f"{len(Q)} questions écrites dans {out}")
