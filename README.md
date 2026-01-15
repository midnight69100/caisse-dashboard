# 📊 Dashboard Caisse – Analyse des ventes

Ce projet présente un **dashboard interactif développé avec Streamlit**
permettant d’analyser un export de **caisse enregistreuse**.

L’objectif est de transformer des données brutes issues d’une caisse
en **indicateurs clairs et exploitables** pour la prise de décision.

---

## 🎯 Objectifs du projet
- Nettoyer et uniformiser un export de caisse (CSV)
- Contrôler la qualité des données (dates, montants, doublons)
- Produire des KPI métiers pertinents
- Visualiser les résultats via un dashboard web interactif

---

## 📈 Indicateurs disponibles
- Chiffre d’affaires total
- Nombre de transactions
- Panier moyen
- Répartition des paiements (CB / Espèces)
- Analyse du chiffre d’affaires par heure
- Analyse du chiffre d’affaires par jour
- Top prestations
- Performance par employé

---

## 🛠️ Stack technique
- Python
- Pandas (nettoyage et agrégation)
- Streamlit (dashboard)
- Matplotlib (visualisations)

---

## 🚀 Démo en ligne
👉 **Application Streamlit** :  
➡️ https://TON-URL.streamlit.app

*(remplacer par l’URL réelle après déploiement)*

---

## 📂 Données
- Données simulées / anonymisées
- Format : CSV
- Possibilité d’importer un fichier utilisateur directement dans l’application

---

## ▶️ Lancer le projet en local

```bash
pip install -r requirements.txt
streamlit run app.py
