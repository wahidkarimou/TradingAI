# TradingAI — Système de signaux swing (V1)

Système gratuit qui reçoit des alertes TradingView pour XAUUSD, EURUSD et BTCUSD,
analyse le marché avec une logique de confluence à 3 couches, et affiche le signal
(BUY / SELL / WAIT) avec entrée, stop-loss et take-profit précis sur un dashboard web.

**Ce système ne passe aucun ordre réel.** C'est un outil d'aide à la décision.

## 1. Logique du signal

| Couche | Rôle | Indicateur | Timeframe |
|---|---|---|---|
| Tendance | Filtre le sens autorisé | EMA 50 vs EMA 200 | Daily |
| Momentum | Détecte le bon moment | RSI + MACD | H4 |
| Structure | Valide un niveau clé | Dernier support/résistance | H4 |

- **BUY** (confiance 3) : tendance haussière + momentum haussier + prix proche d'un support
- **SELL** (confiance 3) : tendance baissière + momentum baissier + prix proche d'une résistance
- **BUY/SELL** (confiance 2) : tendance + momentum alignés, mais pas encore sur un niveau clé
- **WAIT** : pas de confluence suffisante

SL = niveau de structure ± 0.5×ATR · TP = SL à distance ×2 (ratio risque/récompense 1:2, modifiable dans `analysis.py`)

## 2. Installation locale

```bash
cd TradingAI
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Le dashboard est accessible sur **http://localhost:5000**

Pour tester sans attendre une alerte TradingView :
```
http://localhost:5000/analyze/XAUUSD
```
(rafraîchis ensuite la page d'accueil pour voir le signal apparaître)

## 3. Déploiement gratuit (pour un accès 24/7 depuis ton téléphone)

TradingView ne peut pas envoyer d'alertes vers `localhost`. Il faut héberger le
serveur en ligne. Deux options gratuites :

### Option Render.com (recommandé, simple)
1. Crée un compte gratuit sur [render.com](https://render.com)
2. Pousse ce dossier sur un repo GitHub
3. "New Web Service" → connecte le repo
4. Build command : `pip install -r requirements.txt`
5. Start command : `python app.py`
6. Render te donne une URL du type `https://ton-projet.onrender.com`

⚠️ Le tier gratuit de Render met le service en veille après 15 min d'inactivité —
la première requête après une pause peut prendre ~30 secondes à répondre.

### Option Railway.app
Même principe, interface différente, tier gratuit avec quota d'heures/mois.

## 4. Configurer les alertes TradingView

Sur chaque graphique (XAUUSD, EURUSD, BTCUSD) :
1. Crée une alerte sur la condition de ton choix
2. Dans **Webhook URL**, mets : `https://ton-projet.onrender.com/webhook`
3. Dans le message JSON de l'alerte :
```json
{"symbol": "{{ticker}}"}
```

Chaque déclenchement d'alerte lance l'analyse et enregistre le signal.

## 5. Structure du projet

```
TradingAI/
├── app.py              # Serveur Flask (webhook + dashboard)
├── analysis.py         # Logique de confluence + calcul SL/TP
├── database.py         # Stockage SQLite de l'historique des signaux
├── requirements.txt
├── data/                # Créé automatiquement (contient signals.db)
└── templates/
    └── dashboard.html   # Interface web
```

## 6. Limites connues de cette V1

- **yfinance** est utilisé comme source de données (gratuit, mais parfois en léger
  différé et peu fiable sur certains symboles forex/métaux). Si les prix affichés
  semblent décalés par rapport à TradingView, c'est la première chose à vérifier.
  Alternative gratuite avec quota : [Twelve Data](https://twelvedata.com).
- Le système **ne simule pas encore de positions** ni ne calcule de performance —
  c'est volontaire pour cette V1, l'objectif est d'abord de juger la qualité des signaux.
- Aucune notification push : il faut consulter le dashboard manuellement.

## 7. Prochaines étapes possibles (V2)

- Simulation de positions (suivi entrée → SL/TP touché → résultat)
- Statistiques de performance (taux de réussite, gain moyen, par actif)
- Notifications (email ou autre canal)
- Ajout d'actifs supplémentaires
