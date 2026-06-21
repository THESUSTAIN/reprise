"""Seed data pour le Vision Board — un seed par template."""

FEUILLE_DE_ROUTE_DEFAULT = {
    "title": "Vision Board 2029",
    "template": "feuille_de_route",
    "theme": {"palette": "navy-gold", "font": "fraunces"},
    "cards": [
        {"id": "title-1", "type": "title", "x": 3, "y": 3, "w": 32, "h": 16,
         "content": {"text": "Ma feuille de route vers ma vision"},
         "style": {"align": "left"}},
        {"id": "quote-1", "type": "quote", "x": 3, "y": 21, "w": 32, "h": 7,
         "content": {"text": "Discipline aujourd'hui, liberté demain."}},
        {"id": "timeline-1", "type": "timeline", "x": 3, "y": 30, "w": 32, "h": 65,
         "content": {"items": [
             {"id": "today", "label": "AUJOURD'HUI", "icon": "mountain",
              "items": ["Clarifier ma vision", "Structurer mon offre",
                        "Poser les fondations", "Créer du contenu"]},
             {"id": "j90", "label": "90 JOURS", "icon": "calendar",
              "items": ["Atteindre 100 clients", "Valider mon modèle",
                        "Lancer mon offre", "Générer 10K€ de CA"]},
             {"id": "j365", "label": "1 AN", "icon": "flag",
              "items": ["Atteindre 10K clients", "Développer mon équipe",
                        "Créer multiple sources de revenus", "100K€ de CA annuel"]},
             {"id": "j1095", "label": "3 ANS", "icon": "trophy",
              "items": ["Impacter à grande échelle", "Liberté géographique",
                        "Créer mon héritage", "1M€+ de CA annuel"]},
         ]}},
        {"id": "image-1", "type": "image", "x": 38, "y": 3, "w": 30, "h": 28,
         "content": {"src": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=900&q=80",
                     "alt": "Maison de rêve"}},
        {"id": "mission-1", "type": "mission", "x": 70, "y": 3, "w": 27, "h": 30,
         "content": {"label": "MA MISSION",
                     "text": "Aider les entrepreneurs à construire leur liberté financière, leur impact et une vie alignée avec leurs valeurs."}},
        {"id": "quote-2", "type": "quote-card", "x": 38, "y": 34, "w": 22, "h": 22,
         "content": {"text": "Le succès, c'est aimer sa vie.", "author": "Zayado"}},
        {"id": "image-2", "type": "image", "x": 62, "y": 34, "w": 22, "h": 22,
         "content": {"src": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=900&q=80",
                     "alt": "Méditation au sommet"}},
        {"id": "image-3", "type": "image", "x": 86, "y": 34, "w": 11, "h": 22,
         "content": {"src": "https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=600&q=80",
                     "alt": "Voiture de sport"}},
        {"id": "image-4", "type": "image", "x": 38, "y": 58, "w": 22, "h": 24,
         "content": {"src": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?auto=format&fit=crop&w=900&q=80",
                     "alt": "Setup créatif"}},
        {"id": "note-1", "type": "note", "x": 62, "y": 58, "w": 22, "h": 24,
         "content": {"lines": ["Rêver grand.", "Travailler dur.", "Impacter le monde."]}},
        {"id": "valeurs-1", "type": "valeurs", "x": 86, "y": 58, "w": 11, "h": 24,
         "content": {"label": "MES VALEURS", "values": [
             {"icon": "cross", "label": "FOI"},
             {"icon": "sparkle", "label": "INTÉGRITÉ"},
             {"icon": "wing", "label": "LIBERTÉ"},
             {"icon": "heart-hand", "label": "SERVICE"},
             {"icon": "gear", "label": "EXCELLENCE"},
         ]}},
    ],
}


# === ARBRE DE VIE === — 7 piliers + cercle central + titre
ARBRE_DEFAULT = {
    "title": "Mon Arbre de Vie 2029",
    "template": "arbre",
    "theme": {"palette": "navy-gold", "font": "fraunces"},
    "cards": [
        # Titre top
        {"id": "arbre-title", "type": "title", "x": 5, "y": 1, "w": 90, "h": 9,
         "content": {"text": "Visualisez ce qui compte vraiment et faites grandir chaque domaine de votre vie."},
         "style": {"align": "center"}},

        # Image arbre centrale
        {"id": "arbre-tree", "type": "image", "x": 35, "y": 22, "w": 30, "h": 56,
         "content": {"src": "https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?auto=format&fit=crop&w=900&q=80",
                     "alt": "Arbre de vie"}},

        # Cercle central MA VISION (mission card overlay)
        {"id": "arbre-vision", "type": "mission", "x": 41, "y": 42, "w": 18, "h": 18,
         "content": {"label": "MA VISION", "text": "Aligné"}},

        # 7 piliers — chacun est une "valeurs" card simplifiée mais avec texte + progress
        {"id": "p-sante", "type": "pillar", "x": 2, "y": 11, "w": 22, "h": 18,
         "content": {"label": "SANTÉ", "icon": "heart", "items": ["Énergie", "Sport", "Alimentation", "Bien-être"], "progress": 80}},
        {"id": "p-business", "type": "pillar", "x": 76, "y": 11, "w": 22, "h": 18,
         "content": {"label": "BUSINESS", "icon": "briefcase", "items": ["Projets", "Croissance", "Impact", "Revenus"], "progress": 90}},
        {"id": "p-relations", "type": "pillar", "x": 2, "y": 35, "w": 22, "h": 18,
         "content": {"label": "RELATIONS", "icon": "users", "items": ["Famille", "Amis", "Communauté", "Partenariats"], "progress": 75}},
        {"id": "p-apprentissage", "type": "pillar", "x": 76, "y": 35, "w": 22, "h": 18,
         "content": {"label": "APPRENTISSAGE", "icon": "book", "items": ["Compétences", "Lecture", "Formations", "Mentors"], "progress": 70}},
        {"id": "p-spiritualite", "type": "pillar", "x": 2, "y": 59, "w": 22, "h": 18,
         "content": {"label": "SPIRITUALITÉ", "icon": "leaf", "items": ["Foi", "Prière", "Méditation", "Service"], "progress": 85}},
        {"id": "p-equilibre", "type": "pillar", "x": 76, "y": 59, "w": 22, "h": 18,
         "content": {"label": "ÉQUILIBRE", "icon": "scale", "items": ["Temps libre", "Voyages", "Loisirs", "Repos"], "progress": 65}},
        {"id": "p-impact", "type": "pillar", "x": 39, "y": 81, "w": 22, "h": 17,
         "content": {"label": "IMPACT", "icon": "globe", "items": ["Aider les autres", "Créer de la valeur", "Laisser un héritage"], "progress": 88}},
    ],
}


TEMPLATE_SEEDS = {
    "feuille_de_route": FEUILLE_DE_ROUTE_DEFAULT,
    "arbre": ARBRE_DEFAULT,
}
