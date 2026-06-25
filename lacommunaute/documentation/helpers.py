import glob
import pathlib

import frontmatter
import markdown
from django.utils.safestring import mark_safe


CATEGORIES = [
    {
        "name": "Les bases de l'IAE",
        "slug": "les-bases-de-liae",
        "description": "Structures, acteurs dispositifs : reprenez les bases de l'IAE pour tout comprendre",
        "image": "images/documentation/fiche_pratique_108.jpg",
        "content": "",
    },
    {
        "name": "Mon parcours CIP: des ressources pour réussir son avenir dans l'accompagnement professionnel !",
        "slug": "mon-parcours-cip-des-ressources-pour-réussir-son-avenir-dans-laccompagnement-professionnel",
        "description": (
            "Découvrez les essentiels du CIP : Des ressources pour les futurs professionnels en insertion"
            " ou pour tout simplement mettre à jour vos pratiques professionnelle. Tout ce qu'il vous faut"
            " pour réussir votre certification au TP conseiller en insertion professionnelle et réussir"
            " sa prise en main du métier d'accompagnateur vers l'insertion."
        ),
        "image": "images/documentation/fiche_pratique_119.png",
        "content": "",
    },
    {
        "name": "Tout savoir sur les aides et contrats vers l'emploi",
        "slug": "tout-savoir-sur-les-aides-et-contrats-vers-lemploi",
        "description": "Connaitre les mesures, les mobiliser pour les personnes plus eloignées de l'emploi",
        "image": "images/documentation/fiche_pratique_129.png",
        "content": "",
    },
    {
        "name": "Lever les freins périphériques bloquant le retour à l’emploi",
        "slug": "lever-les-freins-périphériques-bloquant-le-retour-à-lemploi",
        "description": (
            "Des dispositifs pour lever les freins périphériques à l'emploi (mobilité, santé, logement,"
            " garde d'enfants...), liés aux obstacles socio-professionnels"
        ),
        "image": "images/documentation/fiche_pratique_131.png",
        "content": "Freins périphériques à l'emploi (mobilité, santé, logement, garde d'enfants...), liés aux obstacles socio-professionnels",  # noqa: E501
    },
    {
        "name": "Evaluer et développer les compétences !",
        "slug": "evaluer-et-développer-les-compétences",
        "description": (
            "Découvrez des fiches pratiques pour identifier, analyser et valoriser les compétences de vos"
            " publics. Accédez à des fiches pratiques conçues pour renforcer vos méthodes"
            " d’accompagnement et approfondir vos connaissances. Ces ressources vous aideront à mieux"
            " évaluer les compétences, à les faire reconnaître et à améliorer votre pratique"
            " professionnelle."
        ),
        "image": "images/documentation/fiche_pratique_133.png",
        "content": "",
    },
    {
        "name": "La Boîte à outils des CIP",
        "slug": "la-boîte-à-outils-des-cip",
        "description": (
            "Un espace dédié rassemblant des outils, des guides pour accompagner les acteurs de"
            " l'inclusion dans leur soutien aux personnes éloignées du marché du travail, confrontées à"
            " des obstacles multiples et complexes."
        ),
        "image": "images/documentation/fiche_pratique_149.png",
        "content": "",
    },
    {
        "name": "Le coin du règlementaire",
        "slug": "le-coin-du-règlementaire",
        "description": (
            "Réglementaire : votre repère clair et à jour pour comprendre droits, devoirs et démarches"
            " liées à l’emploi. Des informations sur les aides et prestations disponibles sous Régime"
            " Général ou Agricole.\nRéformes, allocations, aides... Explications fiables, conseils"
            " pratiques et ressources clés pour les professionnels de l’insertion et les personnes"
            " accompagnées."
        ),
        "image": "images/documentation/fiche_pratique_220.png",
        "content": """👉🏼 Ces rubriques proposent des informations générales.

**Toutefois**,  seule une étude personnalisée et circonstanciée du dossier de la personne permettra d'obtenir des informations exactes""",  # noqa: E501
    },
    {
        "name": "L'inclusion aujourd'hui, les défis de demain",
        "slug": "linclusion-aujourdhui-les-défis-de-demain",
        "description": (
            "Les replay de l'évènement du 1er février 2024 rassemblant l’ensemble des professionnels de"
            " l’inclusion. Ce évènement est organisé par la Communauté de l’inclusion, un service"
            " numérique qui permet à plus de 11000 professionnels de l’inclusion de partager leurs"
            " difficultés et identifier des moyens d’entraide."
        ),
        "image": "images/documentation/fiche_pratique_142.png",
        "content": """Initiée en 2019, la Plateforme de l’inclusion est une structure qui rassemble une dizaine de services numériques dont l’objectif est de lutter contre l’exclusion des personnes éloignées de l’emploi en facilitant les relations entre les acteurs de l’écosystème et la relation entre les accompagnateurs et les usagers.

Cet évènement a pour objectif de récolter les besoins terrain et partager les bonnes pratiques et solutions qui ont fonctionné.

Il est composé d’une dizaine ateliers de travail autour de thématiques précises : “Mieux accompagner les personnes les plus éloignées de l’emploi”, “Découvrir la cartographie de l’offre d’insertion”, “Personnes éloignées de l'emploi et Immersion professionnelle : le duo gagnant” de sorte à identifier les freins à l’accompagnement et les leviers pour les dépasser.""",  # noqa: E501
    },
    {
        "name": "Handicap et emploi : ressources pour l'insertion professionnelle",
        "slug": "handicap-et-emploi-ressources-pour-linsertion-professionnelle",
        "description": (
            "Découvrez dans cette rubrique dédiée au handicap, où vous trouverez des fiches pratiques,"
            " des études de cas et des informations à jour sur la législation, les aides et les"
            " accompagnements disponibles."
        ),
        "image": "images/documentation/fiche_pratique_227.png",
        "content": "",
    },
    {
        "name": "On a besoin de vous, de votre avis.",
        "slug": "on-a-besoin-de-vous-de-votre-avis",
        "description": (
            "Un espace pour faire entendre votre voix : idées, besoins, retours d’expérience… Ici, on"
            " vous consulte via des sondages et questionnaires mis à jour régulièrement — et bien sûr,"
            " on vous partage les résultats. Parce que c’est sur le terrain que se vivent les réalités…"
            " et que vos retours sont indispensables pour faire évoluer nos pratiques."
        ),
        "image": "images/documentation/fiche_pratique_243.png",
        "content": "",
    },
    {
        "name": "La boîte à outils des professionnels de l’insertion : la Plateforme de l’inclusion",
        "slug": "la-boîte-à-outils-des-professionnels-de-linsertion-la-plateforme-de-linclusion",
        "description": (
            "Tous les outils de la Plateforme de l’Inclusion au même endroit : objectifs, publics,"
            " cas d’usage, pas à pas. Une rubrique pensée pour les pros de l’insertion qui veulent aller"
            " vite, mieux coordonner, et sécuriser les démarches des personnes accompagnées."
        ),
        "image": "images/documentation/fiche_pratique_256.png",
        "content": """Les outils de la Plateforme de l’inclusion sont présentés de manière structurée, pour aider les acteurs du territoire à identifier rapidement les services utiles, leurs usages et les modalités d’activation.

Chaque outil est décrit de façon concise : finalité, publics concernés, principaux cas d’usage, conditions de mise en œuvre et ressources disponibles. Les contenus visent à faciliter la décision et le déploiement, en s’appuyant sur des repères clairs et des bénéfices attendus : meilleure coordination entre acteurs, continuité de parcours, simplification des démarches et gain de temps opérationnel.

L’ensemble constitue un point d’entrée unique pour comprendre l’écosystème, orienter les choix, et renforcer l’efficacité collective à l’échelle des territoires.""",  # noqa: E501
    },
]

for category in CATEGORIES:
    if content := category["content"]:
        category["html"] = mark_safe(markdown.markdown(content, extensions=["nl2br"]))


def parse_cards():
    cards = {}
    for category in CATEGORIES:
        filenames = glob.glob(rf"lacommunaute/documentation/data/{category['slug']}/*.md")
        for filename in filenames:
            obj = frontmatter.load(filename)
            card = obj.metadata
            card["content"] = obj.content
            card["html"] = mark_safe(markdown.markdown(obj.content, extensions=["nl2br"]))
            card["slug"] = pathlib.Path(filename).stem
            card["category_slug"] = category["slug"]
            card["image"] = f"images/documentation/{card['image']}"
            cards[card["slug"]] = card
    return {k: v for k, v in sorted(cards.items(), key=lambda item: item[1]["name"])}


CARDS = parse_cards()


def get_cards(category_slug):
    return [card for card in CARDS.values() if card["category_slug"] == category_slug]
