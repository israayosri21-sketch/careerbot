"""Génère le corpus RH fictif du Groupe Orvane (données inventées, à but pédagogique)."""
from pathlib import Path

DOCS = {
"01_teletravail": """# Politique de télétravail

## Éligibilité
Le télétravail est ouvert à tous les collaborateurs en CDI ou en CDD de plus de 6 mois, après la fin de leur période d'essai. Les postes en boutique, en atelier et en logistique ne sont pas éligibles, car ils exigent une présence physique.

## Nombre de jours
Chaque collaborateur éligible peut télétravailler jusqu'à 2 jours par semaine. Les jours sont fixés avec le manager et ne sont pas reportables d'une semaine sur l'autre. Une présence sur site est obligatoire le mardi, jour des réunions d'équipe.

## Indemnité
Une indemnité forfaitaire de 30 euros par mois est versée pour couvrir les frais d'internet et d'électricité. Le Groupe prend aussi en charge un écran et un siège ergonomique, à hauteur de 300 euros, une seule fois.

## Demande
La demande se fait dans l'outil RH MyOrvane, rubrique « Mon organisation ». Le manager a 15 jours pour répondre. Un refus doit être motivé par écrit.
""",
"02_conges": """# Congés et absences

## Congés payés
Chaque collaborateur acquiert 2,5 jours ouvrables de congés payés par mois travaillé, soit 30 jours ouvrables par an. La période de prise des congés va du 1er mai au 30 avril de l'année suivante.

## RTT
Les collaborateurs au forfait jours bénéficient de 10 jours de RTT par an. Les RTT non pris au 31 décembre sont perdus, sauf s'ils sont versés sur le compte épargne-temps.

## Compte épargne-temps
Le compte épargne-temps permet de mettre de côté jusqu'à 10 jours par an, dans la limite de 60 jours au total. Les jours épargnés peuvent financer un congé sabbatique ou une formation longue.

## Absences pour événements familiaux
Le mariage ou le PACS du collaborateur donne droit à 5 jours d'absence rémunérée. La naissance d'un enfant donne droit à 3 jours, en plus du congé de paternité. Le décès d'un parent proche donne droit à 3 jours.
""",
"03_mobilite_interne": """# Mobilité interne

## Principe
Le Groupe Orvane privilégie la mobilité interne : toute offre est publiée en interne pendant 10 jours avant d'être ouverte aux candidats externes.

## Conditions
Un collaborateur peut postuler à une mobilité après 18 mois dans son poste actuel. Il n'a pas besoin de l'accord préalable de son manager pour postuler, mais il doit l'informer s'il est retenu pour un entretien.

## Mobilité entre filiales
Les mobilités entre filiales du Groupe sont possibles en France et à l'international. L'ancienneté acquise est conservée en cas de mobilité entre filiales.

## Accompagnement
Chaque candidat interne peut demander un entretien avec un conseiller carrière de l'équipe People Experience. En cas de mobilité géographique, le Groupe prend en charge les frais de déménagement jusqu'à 5 000 euros et une semaine de congé supplémentaire pour s'installer.
""",
"04_formation": """# Formation et développement des compétences

## Plan de formation
Chaque année, le manager et le collaborateur identifient ensemble les formations utiles lors de l'entretien annuel. Le plan de formation est validé en décembre pour l'année suivante.

## Compte personnel de formation
Le compte personnel de formation (CPF) est crédité de 500 euros par an pour un salarié à temps plein, dans la limite de 5 000 euros. Le Groupe abonde le CPF de 1 000 euros pour les formations certifiantes liées au métier.

## Orvane Academy
L'Orvane Academy propose plus de 200 modules en ligne : management, data, intelligence artificielle, langues et savoir-faire métiers. Les modules sont accessibles gratuitement depuis MyOrvane, sur le temps de travail, dans la limite de 2 heures par semaine.

## Formations diplômantes
Une formation diplômante peut être financée à 100 % si le collaborateur a au moins 2 ans d'ancienneté et s'engage à rester 2 ans dans le Groupe après l'obtention du diplôme.
""",
"05_entretien_annuel": """# Entretien annuel et entretien professionnel

## Entretien annuel
L'entretien annuel a lieu entre janvier et mars. Il fait le bilan des objectifs de l'année écoulée et fixe 3 à 5 objectifs pour l'année suivante. Le collaborateur prépare l'entretien avec une auto-évaluation dans MyOrvane.

## Entretien professionnel
L'entretien professionnel est distinct de l'entretien annuel. Il porte sur les perspectives d'évolution et les besoins de formation, et a lieu tous les 2 ans. Tous les 6 ans, il fait un bilan complet du parcours.

## Évaluation
La performance est évaluée sur 4 niveaux : à développer, conforme, très bon, exceptionnel. Le niveau d'évaluation sert de base à la révision salariale d'avril.
""",
"06_onboarding": """# Intégration des nouveaux arrivants

## Avant l'arrivée
Le nouvel arrivant reçoit son matériel informatique et ses accès une semaine avant son premier jour. Un message de bienvenue de son manager lui présente son équipe et son programme.

## Parcours d'intégration
Le parcours d'intégration dure 3 mois. Il comprend une journée d'accueil Groupe, des rencontres avec les équipes partenaires et un point d'étape avec le manager à 1 mois puis à 3 mois.

## Parrainage
Chaque nouvel arrivant est accompagné par un parrain ou une marraine d'une autre équipe pendant ses 6 premiers mois. Le parrain répond aux questions pratiques et aide à comprendre la culture du Groupe.

## Rapport d'étonnement
À la fin du premier mois, le nouvel arrivant rédige un rapport d'étonnement, partagé avec son manager et l'équipe People Experience, pour améliorer l'accueil des prochains arrivants.
""",
"07_mentorat": """# Programme de mentorat

## Objectif
Le programme de mentorat met en relation un mentoré et un mentor plus expérimenté d'une autre filiale, pour échanger sur le développement de carrière.

## Durée et rythme
Un cycle de mentorat dure 9 mois, avec une rencontre d'une heure par mois, sur site ou en visioconférence. Le mentor et le mentoré signent une charte de confidentialité.

## Inscription
Les inscriptions ouvrent deux fois par an, en mars et en septembre, dans MyOrvane. Tout collaborateur ayant au moins 1 an d'ancienneté peut devenir mentoré. Pour devenir mentor, il faut au moins 5 ans d'expérience professionnelle.

## Mise en relation
L'équipe People Experience propose un binôme à partir des objectifs exprimés par le mentoré. Le mentor ne peut pas être le manager direct ou indirect du mentoré.
""",
"08_reseau_interne": """# Réseaux internes et communautés

## Communautés métiers
Les communautés métiers rassemblent des collaborateurs de différentes filiales autour d'une même expertise, par exemple la data, le marketing digital ou le retail. Elles se réunissent une fois par trimestre.

## Cafés carrière
Les cafés carrière sont des échanges virtuels de 30 minutes entre deux collaborateurs de filiales différentes. Ils sont organisés chaque mois sur inscription volontaire. Les sujets portent sur les méthodes et les parcours, jamais sur des informations commerciales.

## Réseaux d'affinité
Le Groupe soutient plusieurs réseaux d'affinité, dont un réseau de femmes leaders et un réseau des jeunes talents de moins de 30 ans. Chaque réseau dispose d'un budget annuel de 10 000 euros pour ses événements.
""",
"09_remuneration": """# Rémunération et avantages

## Révision salariale
La révision salariale a lieu chaque année en avril. Elle tient compte du niveau d'évaluation de l'entretien annuel et du positionnement du salaire par rapport au marché.

## Rémunération variable
Les cadres bénéficient d'une prime sur objectifs pouvant atteindre 10 % du salaire annuel, versée en mars. Une prime d'intéressement collective est versée à tous les salariés en juin, selon les résultats du Groupe.

## Avantages
Les collaborateurs bénéficient de tickets restaurant d'une valeur de 10 euros, pris en charge à 60 % par l'employeur, d'une mutuelle prise en charge à 70 %, et d'une remise de 30 % sur les produits du Groupe.

## Transport
L'abonnement de transport en commun est remboursé à 75 %. Un forfait mobilités durables de 600 euros par an est proposé aux collaborateurs qui viennent à vélo ou en covoiturage.
""",
"10_notes_de_frais": """# Notes de frais et déplacements

## Déclaration
Les notes de frais sont déclarées dans MyOrvane avec le justificatif scanné, dans un délai de 30 jours après la dépense. Elles sont remboursées sur la paie du mois suivant.

## Plafonds
Le repas d'affaires est remboursé jusqu'à 35 euros par personne en France. L'hôtel est remboursé jusqu'à 180 euros la nuit à Paris et 120 euros en province.

## Transport professionnel
Le train est la règle pour les trajets de moins de 4 heures. L'avion en classe économique est autorisé au-delà. La classe affaires est réservée aux vols de plus de 8 heures.
""",
"11_deconnexion": """# Droit à la déconnexion

## Principe
Chaque collaborateur a le droit de ne pas répondre aux messages professionnels en dehors de ses horaires de travail, le week-end et pendant ses congés.

## Plages protégées
Aucun e-mail ne doit être envoyé entre 20 h et 8 h, ni le week-end, sauf urgence. Les outils de messagerie proposent l'envoi différé pour respecter ces plages.

## Réunions
Les réunions ne commencent pas avant 9 h et ne se terminent pas après 18 h. Une réunion dure 45 minutes au maximum par défaut, pour laisser du temps entre deux rendez-vous.
""",
"12_parentalite": """# Parentalité

## Congé maternité et paternité
Le Groupe maintient 100 % du salaire pendant le congé maternité et le congé de paternité, au-delà des indemnités de la Sécurité sociale.

## Retour de congé
Au retour d'un congé maternité ou d'adoption, la collaboratrice ou le collaborateur peut reprendre à temps partiel à 80 % pendant 3 mois, payé à 100 %.

## Garde d'enfants
Le Groupe réserve des places en crèche interentreprises dans les principales villes. Une aide de 50 euros par mois est versée pour la garde d'un enfant de moins de 3 ans lorsqu'aucune place n'est disponible.
""",
"13_handicap": """# Handicap et inclusion

## Référent handicap
Chaque filiale dispose d'un référent handicap, joignable de façon confidentielle depuis MyOrvane.

## Aménagements
Le Groupe finance l'aménagement du poste de travail, du matériel adapté et des horaires aménagés pour les collaborateurs en situation de handicap.

## Jours d'absence
Les collaborateurs bénéficiant d'une reconnaissance de travailleur handicapé disposent de 2 jours d'absence rémunérée par an pour leurs démarches médicales et administratives.
""",
"14_donnees_personnelles": """# Protection des données personnelles des collaborateurs

## Données collectées
Le Groupe collecte uniquement les données nécessaires à la gestion administrative, à la paie et au développement de carrière. Les données de santé ne sont jamais stockées dans MyOrvane.

## Durée de conservation
Les dossiers des collaborateurs sont conservés pendant 5 ans après leur départ. Les candidatures non retenues sont supprimées au bout de 2 ans.

## Droits
Chaque collaborateur peut demander l'accès, la rectification ou la suppression de ses données en écrivant au délégué à la protection des données (DPO). Une réponse est apportée sous 1 mois.
""",
"15_code_conduite": """# Code de conduite

## Confidentialité
Les informations sur les clients, les prix, les lancements de produits et la stratégie sont confidentielles. Elles ne doivent pas être partagées entre filiales en dehors des canaux prévus.

## Cadeaux
Un collaborateur ne peut pas accepter de cadeau d'une valeur supérieure à 100 euros de la part d'un fournisseur. Tout cadeau doit être déclaré à son manager.

## Alerte
Tout manquement au code de conduite peut être signalé de façon anonyme sur la plateforme d'alerte éthique, accessible 24 h sur 24.
""",
"16_depart": """# Départ du Groupe

## Préavis
Le préavis de démission est d'1 mois pour les employés et de 3 mois pour les cadres. Il peut être réduit d'un commun accord avec le manager.

## Entretien de sortie
Chaque collaborateur qui quitte le Groupe se voit proposer un entretien de sortie avec l'équipe People Experience, pour recueillir son retour sur son expérience.

## Réseau des anciens
Les anciens collaborateurs peuvent rejoindre le réseau Orvane Alumni pour garder le contact et être informés des offres d'emploi. Un ancien collaborateur peut être réembauché sans période d'essai s'il revient dans les 2 ans.
""",
}

if __name__ == "__main__":
    out = Path(__file__).parent / "corpus"
    out.mkdir(exist_ok=True)
    for name, text in DOCS.items():
        (out / f"{name}.md").write_text(text.strip() + "\n", encoding="utf-8")
    print(f"{len(DOCS)} documents écrits dans {out}")
