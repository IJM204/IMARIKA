"""
Contexte Agronomique et Écologique du Burundi pour l'Assistant Imarika.
Documentation des régions agro-écologiques, des saisons culturales et des pratiques locales.
"""

BURUNDI_SEASONS = {
    "Saison A (Impeshi)": {
        "periode": "Septembre/Octobre à Janvier/Février",
        "description": "Première saison agricole correspondant au démarrage des pluies. Essentielle pour les cultures vivrières.",
        "cultures_principales": ["Haricot", "Maïs", "Sorgho", "Arachide", "Soja", "Patate douce"],
        "recommandations": "Labour profond dès août/septembre. Semis dès l'installation des pluies régulières. Apport de fumier organique bien décomposé et engrais de fond (ex: FOMI Imbura)."
    },
    "Saison B (Urugaryi)": {
        "periode": "Février à Juin/Juillet",
        "description": "Grande saison des pluies avec fortes précipitations (mars-avril).",
        "cultures_principales": ["Haricot", "Maïs", "Manioc", "Patate douce", "Éleusine", "Banane"],
        "recommandations": "Attention aux maladies fongiques (anthracnose, rouille) dues à l'humidité élevée. Butter les plants et assurer un drainage correct pour éviter l'asphyxie des racines."
    },
    "Saison C (Ici / Marais)": {
        "periode": "Juin à Septembre/Octobre (Saison sèche)",
        "description": "Cultures de contre-saison pratiquées exclusivement dans les marais et bas-fonds aménagés.",
        "cultures_principales": ["Haricot de marais", "Légumes maraîchers (choux, carottes, tomates)", "Maïs précoce", "Pomme de terre"],
        "recommandations": "Gestion rigoureuse du niveau d'eau dans les billons et fossés d'irrigation. Rotation des cultures pour briser le cycle des ravageurs."
    }
}

BURUNDI_REGIONS = {
    "Imbo": {
        "altitude": "775 - 1000 m",
        "provinces": ["Bujumbura Mairie", "Bujumbura Rural (plaine)", "Bubanza", "Cibitoke"],
        "climat": "Chaud et semi-aride (23-26°C), pluviométrie 750-1000 mm",
        "cultures": ["Riz irrigué", "Manioc", "Maïs", "Coton", "Palmier à huile", "Canne à sucre", "Tomate"]
    },
    "Mirwa": {
        "altitude": "1000 - 1500 m",
        "provinces": ["Escarpements de Bujumbura Rural", "Cibitoke", "Bubanza", "Bururi (versant ouest)"],
        "climat": "Pentes fortes, pluviométrie 1100-1400 mm",
        "cultures": ["Caféier Arabica", "Manioc", "Bananier", "Haricot"],
        "defis": "Érosion hydrique aiguë, nécessite des fossés anti-érosifs et haies de Pennisetum ou herbes de vétiver."
    },
    "Buyenzi": {
        "altitude": "1500 - 1900 m",
        "provinces": ["Ngozi", "Kayanza"],
        "climat": "Tempéré, pluviométrie abondante (1200-1500 mm)",
        "cultures": ["Caféier", "Haricot", "Maïs", "Bananier", "Manioc", "Patate douce"],
        "remarques": "Zone à très forte densité démographique, intensification agricole et fertilisation indispensables."
    },
    "Kirimiro": {
        "altitude": "1500 - 1800 m",
        "provinces": ["Gitega", "Karusi", "Muramvya", "Gitega (capitale politique)"],
        "climat": "Plateaux centraux, 18-21°C, pluviométrie 1100-1300 mm",
        "cultures": ["Haricot", "Bananier", "Maïs", "Caféier", "Manioc", "Patate douce", "Sorgho"]
    },
    "Bweru": {
        "altitude": "1350 - 1600 m",
        "provinces": ["Kirundo", "Muyinga"],
        "climat": "Plateaux du Nord-Est, déficits hydriques fréquents",
        "cultures": ["Sorgho", "Haricot", "Manioc", "Maïs", "Caféier"],
        "remarques": "Sensible aux sécheresses, promouvoir des variétés résistantes au stress hydrique et le paillage."
    },
    "Bututsi": {
        "altitude": "1800 - 2300 m",
        "provinces": ["Bururi", "Vyanda", "Matana"],
        "climat": "Frais et humide (14-17°C), crête Congo-Nil",
        "cultures": ["Théier", "Pomme de terre", "Blé", "Pois", "Maïs d'altitude", "Élevage bovin"]
    },
    "Mugamba": {
        "altitude": "1900 - 2600 m",
        "provinces": ["Hautes terres de Muramvya", "Kayanza", "Gitega occidental"],
        "climat": "Froid et très pluvieux (1300-2000 mm)",
        "cultures": ["Théier", "Pomme de terre", "Pois", "Blé", "Reboisement"]
    },
    "Mosso / Kumoso": {
        "altitude": "1100 - 1300 m",
        "provinces": ["Ruyigi", "Cankuzo", "Rutana"],
        "climat": "Chaud et modérément humide",
        "cultures": ["Canne à sucre (SOSUMO)", "Arachide", "Sorgho", "Maïs", "Haricot", "Manioc"]
    }
}

BURUNDI_FERTILIZATION_PRACTICES = """
Au Burundi, la fertilisation moderne repose sur :
1. Les engrais organo-minéraux nationaux FOMI (Fabrique d'Organo-Minéraux des Industries du Burundi) :
   - FOMI Imbura (engrais de fond riche en phosphore et matière organique, appliqué au semis).
   - FOMI Bagara (engrais de couverture riche en azote pour la croissance végétative).
   - FOMI Totahaza (spécial café et cultures pérennes).
2. L'amendement calcique (chaux dolomitique de Matongo) : Indispensable pour neutraliser l'acidité marquée (pH < 5.5) des sols ferrallitiques de haute et moyenne altitude.
3. Le fumier d'étable ou compost décomposé : base incontournable de la gestion de la matière organique des sols.
"""
