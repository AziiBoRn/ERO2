import matplotlib.pyplot as plt

def compter_par_tranche(data, pas_minutes=30):
    compteur = {}
    for push in data:
        h, m = map(int, push["created_hour"].split(":"))
        total = h * 60 + m

        # On ramène le temps à la tranche désirée
        tranche = (total // pas_minutes) * pas_minutes

        hh = tranche // 60
        mm = tranche % 60
        key = f"{hh:02d}:{mm:02d}"

        compteur[key] = compteur.get(key, 0) + 1

    return compteur


def afficher_compteur_30min(compteur):
    for t in sorted(compteur.keys()):
        print(f"{t} -> {compteur[t]} pushs")


def tracer_courbe_poids(interpolate_weight):
    minutes = list(range(14*60, 24*60))
    poids = [interpolate_weight(m) for m in minutes]
    heures = [m/60 for m in minutes]
    plt.figure(figsize=(10,4))
    plt.plot(heures, poids)
    plt.title("Courbe des poids horaires")
    plt.xlabel("Heure")
    plt.ylabel("Poids")
    plt.grid(True)
    plt.show()


def tracer_courbe_compteur(compteur):
    tranches = sorted(compteur.keys())
    valeurs = [compteur[t] for t in tranches]
    heures = []
    for t in tranches:
        h, m = map(int, t.split(":"))
        heures.append(h + m/60)
    plt.figure(figsize=(10,4))
    plt.plot(heures, valeurs)
    plt.title("Nombre de pushs par tranche")
    plt.xlabel("Heure")
    plt.ylabel("Pushs")
    plt.grid(True)
    plt.show()
