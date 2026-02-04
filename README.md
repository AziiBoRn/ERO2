# ERO2

**Membres du groupe :**

- Paul Pazart
- Lucas Burgaud
- Kylian Bozec
- Etienne Senigout
- Guillaume Hanry
- Pierre Braud

Un rapport exhaustif situé à la racine du repository contient toutes les informations théoriques (problématique, systèmes) liées au projet ainsi que les solutions adaptées et notre analyse des différents scénarios simulés.

Les résultats bruts de nos simulations sont disponibles dans le dossier `backend/results/`.

### Prérequis

- Python 3.x installé sur votre machine

### Installation

1. Cloner le dépôt ou télécharger les fichiers.
2. Ouvrir un terminal et se placer dans le dossier `backend` :

```bash
cd backend
```

2. Lancer le script principal pour générer des tags et simuler un scénario :

A noter : l'architecture utilisée peut être changée au niveau du `main.py`. Nous avons par défaut mis des paramètres "réalistes" mais tout peut être modifié. Les fichiers relatifs à la paramétrisation du système sont : `main.py`, `model.py` et les scripts de chaque architecture (`waterfall.py`, etc).

```bash
python3 -m main
```
