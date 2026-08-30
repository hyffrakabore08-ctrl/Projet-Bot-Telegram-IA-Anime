# 🏗️ BOT TELEGRAM IA + MINI APP + ANILIST

Projet complet de gestion d'animes pour canaux Telegram avec IA, Mini App et intégration AniList.

## 📋 FONCTIONNALITÉS

### Bot Telegram
- **Analyse de canaux** : Scan automatique des messages pour identifier les animes populaires
- **Top Animes** : Classement des animes par score (likes, vues, commentaires)
- **Recommandations IA** : Suggestions d'animes similaires basées sur les tendances
- **Statistiques AniList** : Informations détaillées sur chaque anime
- **Commandes en langage naturel** : Pas besoin de commandes slash, l'IA comprend vos demandes

### Mini App (Interface Web)
- **📊 Statistiques** : Visualisation des performances des canaux
- **📢 Publication** : Publication directe ou programmée de contenu
- **🎬 Animes à Venir** : Calendrier des sorties d'animes
- **👥 Groupes** : Suivi de l'activité des groupes liés
- **🎮 Contrôle Canal** : Gestion des statuts de canaux
- **⚙️ Paramètres** : Configuration du bot et de l'IA

## 🛠️ INSTALLATION

### Prérequis
- un hébergeur 
- Bot Telegram (via @BotFather)
- Token API 

### Variables d'Environnement

Créez un fichier `.env` ou configurez les secrets dans Hugging Face Spaces :

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_USER_ID=123456789
DATABASE_PATH=/data/app.db
DEBUG_MODE=false
```

### Installation Locale

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python app/main.py
```

### Déploiement sur Hugging Face Spaces

1. Créez un nouveau Space avec le SDK **Docker**
2. Ajoutez les variables d'environnement dans les secrets
3. Poussez le code sur le dépôt du Space
4. Le déploiement est automatique

## 📁 STRUCTURE DU PROJET

```
telegram-anime-manager/
├── Dockerfile                 # Configuration Docker pour HF Spaces
├── requirements.txt           # Dépendances Python
├── README.md                  # Ce fichier
├── app/
│   ├── main.py               # Point d'entrée principal
│   ├── config.py             # Configuration et variables
│   ├── database.py           # Initialisation SQLite
│   ├── bot/
│   │   ├── handlers.py       # Gestion des messages Telegram
│   │   ├── analyser.py       # Logique d'analyse des canaux
│   │   ├── anilist_api.py    # Client API AniList
│   │   ├── ia_agent.py       # Intégration Hugging Face IA
│   │   └── scheduler.py      # Publications programmées
│   ├── web/
│   │   ├── routes.py         # API FastAPI
│   │   └── static/
│   │       ├── index.html    # Interface Mini App
│   │       ├── style.css     # Styles (typo MAJUSCULES)
│   │       └── app.js        # JavaScript frontend
│   └── utils/
│       └── parser.py         # Nettoyage des titres d'anime
└── data/                     # Base de données SQLite (persistante)
```

## 🎯 UTILISATION

### Commandes Bot (Langage Naturel)

Le bot comprend des phrases comme :
- "VA SUR @MONCANAL ET DONNE MOI LE TOP 3 DES ANIMES"
- "ANALYSE LE CANAL 123456789"
- "QUELLES SONT LES STATS DE SOLO LEVELING ?"

### Typographie

**TOUTE L'INTERFACE EST EN MAJUSCULES** comme spécifié :
- Police : Arial Black / Arial Bold
- CSS : `text-transform: uppercase`
- Réponses du bot : converties en majuscules automatiquement

## 📊 ALGORITHME DE SCORE

Le score global d'un anime est calculé ainsi :

```
Score = (0.5 × Likes) + (0.3 × Vues) + (0.2 × Commentaires)
```

Ces pondérations sont configurables dans les paramètres.

## 🔒 SÉCURITÉ

- Accès restreint à l'ID admin configuré
- Tokens stockés dans les secrets (jamais en clair)
- Base de données SQLite protégée

## 🚀 LIMITATIONS

### Version Gratuite Hugging Face Spaces
- Mise en veille après 48h d'inactivité
- RAM limitée à 2 Go
- Solution : Utiliser Uptime Robot pour ping régulier

### API Telegram
- Nécessite que le bot soit admin des canaux
- Limitation à ~100 messages analysés pour performance

## 📝 LICENCE

MIT License - Libre utilisation et modification

---

**Développé avec ❤️ pour la communauté Anime**
