import random
import math
from enum import Enum
from common.model import *
from uuid import UUID, uuid4

# -----------------------------------------------------------------------------------
# FONCTION D’INTENSITÉ λ(t)
# t est en minutes (0–1440)
# À AJUSTER SELON TES COURBES RÉELLES
# -----------------------------------------------------------------------------------

def intensity_lambda(t):
    """
    Fonction d’intensité λ(t) pour un processus de Poisson non-homogène.
    t : minute entre 14h (840) et minuit (1440)
    """

    # Helper pour faire une droite entre deux points (x1,y1) -> (x2,y2)
    def linear(x, x1, y1, x2, y2):
        if x < x1:
            return y1
        if x > x2:
            return y2
        return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

    # ----------------------------
    # 1) GROS PIC À 14h (840 min)
    # ----------------------------
    peak_14h = 90 * math.exp(-((t - 840) / 20) ** 2)  # pic très fort et serré

    # --------------------------------------
    # 2) BAISSE CONSTANTE entre 14h et 17h
    # 90 → 20 entre 840 et 1020
    # --------------------------------------
    baisse_14_17 = linear(t, 840, 90, 1020, 20)

    # ------------------------------
    # 3) PIC À 19h
    # t = 1140 minutes
    # ------------------------------
    peak_19h = 60 * math.exp(-((t - 1140) / 25) ** 2)

    # ------------------------------
    # 4) GROSSE BAISSE À 20h
    # chute de 60 → 10 entre 1140 et 1200
    # ------------------------------
    baisse_20h = linear(t, 1140, 60, 1200, 10)

    # -----------------------------------------
    # 5) MONTÉE CONSTANTE jusqu’à 22h
    # 10 → 50 entre 20h (1200) et 22h (1320)
    # -----------------------------------------
    montee_22h = linear(t, 1200, 10, 1320, 50)

    # ------------------------------
    # 6) PIC À 22h
    # ------------------------------
    peak_22h = 80 * math.exp(-((t - 1320) / 18) ** 2)

    # ------------------------------
    # 7) BAISSE APRÈS 22h
    # 50 → 5 entre 22h (1320) et minuit (1440)
    # ------------------------------
    baisse_22_minuit = linear(t, 1320, 50, 1440, 5)

    # --------------------------------------------------------------------------------
    # Combinaison :
    #   - baseline = min des composantes
    #   - les pics se superposent naturellement
    #   - max(...) pour respecter la montée/descente principale + pics
    # --------------------------------------------------------------------------------

    baseline = max(baisse_14_17, baisse_20h, montee_22h, baisse_22_minuit)

    return baseline + peak_14h + peak_19h + peak_22h


# -----------------------------------------------------------------------------------
# SIMULATION D’UN PROCESSUS DE POISSON NON-HOMOGENE
# Méthode du thinning d’Ogata
# -----------------------------------------------------------------------------------

def poisson_non_homogene(start_min, end_min):
    """
    Simule les instants (en minutes) d’un NHPP sur [start_min, end_min]
    en utilisant le thinning d’Ogata.
    """

    t = start_min
    instants = []

    # 1) Trouver un majorant M >= max λ(t)
    #    Valeur approx : on surapproche
    M = max(intensity_lambda(start_min),
            intensity_lambda((start_min + end_min)//2),
            intensity_lambda(end_min)) + 10

    while t < end_min:
        # Tirage du temps d'attente d’un PP homogène de taux M
        u = random.random()
        w = -math.log(u) / M
        t = t + w

        if t >= end_min:
            break

        # Acceptation avec probabilité λ(t) / M
        if random.random() < intensity_lambda(t) / M:
            instants.append(int(t))

    return sorted(instants)


# -----------------------------------------------------------------------------------
# GÉNÉRATION DES PUSHS
# -----------------------------------------------------------------------------------

def generer_pushs_poisson(n):
    """
    Génère des pushs selon un vrai processus de Poisson non-homogène.
    n = nombre *maximal* souhaité, mais en vrai NHPP, le nombre réel
    dépend de l’intégrale de λ(t). Si tu veux FORCER n, on peut adapter.
    """

    # Intervalle : de 14h00 à 24h00
    start = 14 * 60
    end = 24 * 60

    # On génère les instants selon NHPP
    instants = poisson_non_homogene(start, end)

    # Si trop d’événements (> n) on sous-échantillonne
    if len(instants) > n:
        instants = random.sample(instants, n)
        instants.sort()

    pushs = []
    for i, minute in enumerate(instants):
        h = minute // 60
        m = minute % 60
        created_hour = f"{h:02d}:{m:02d}"
        created_dt = datetime.strptime(created_hour, "%H:%M")

        pushs.append(Tag(
                id=uuid4(),
                time=created_dt,
                population=PopulationType.ING if random.random() < 0.5 else PopulationType.PREPA,
                exercise_name="exo1"
            ))

    return pushs
