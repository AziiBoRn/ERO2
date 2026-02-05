# ERO2

## Présentation

**Étude des comportements de systèmes d’attente**  

Ce projet s’intéresse à la question suivante :  

Quel effet a la priorisation des utilisateurs sur les performances du système lors des rendus de TP prépa et de piscine C ?  

Dans ce rapport, nous analysons l’infrastructure de correction automatique d’EPITA.  
Nous étudions ce système de moulinettage sous différents angles mathématiques et expérimentaux.  

Pour rendre notre analyse pertinente, nous nous sommes appuyés sur :  
- des données réelles issues des graphiques disponibles sur Grafana  
- nos propres données scrappées directement depuis l’intra (tous les tags de chaque exercice avec leur temps de traitement en ms)  

Les résultats bruts de nos simulations sont disponibles dans le dossier backend/results/.

## Prérequis

- Python 3.x installé sur votre machine.

## Installation et lancement

1. Cloner le dépôt ou télécharger les fichiers.  
2. Installer les dépendances :
  
```bash
pip install -r requirements.txt
```

3. Se placer dans le dossier backend :

```bash
cd backend
```

4. Lancer le script principal pour générer les tags et simuler un scénario :

```bash
python -m main
```

## Aller plus loin

L'architecture utilisée peut être changée au niveau du `main.py`. Nous avons par défaut mis des paramètres "réalistes" mais tout peut être modifié. Les fichiers relatifs à la paramétrisation du système sont : `main.py`, `model.py`.

---

**Membres du groupe :**  
- Paul Pazart  
- Lucas Burgaud  
- Kylian Bozec  
- Etienne Senigout  
- Guillaume Hanry  
- Pierre Braud  