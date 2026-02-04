# -*- coding: utf-8 -*-
# main.py

from generation_poisson import generer_pushs_poisson
from analyse import compter_par_tranche, afficher_compteur_30min, tracer_courbe_compteur, tracer_courbe_poids

def main():
    # Génération
    print("\n--- Génération des pushs ---")
    data = generer_pushs_poisson(1000000)
    print(f"{len(data)} pushs générés.")

    # Analyse par tranche
    print("\n--- Comptage par tranche de 30 minutes ---")
    compteur = compter_par_tranche(data, 1)
    afficher_compteur_30min(compteur)

    # Tracés
    print("\n--- Affichage des courbes ---")
    #tracer_courbe_poids(interpolate_weight)
    tracer_courbe_compteur(compteur)


if __name__ == "__main__":
    main()
