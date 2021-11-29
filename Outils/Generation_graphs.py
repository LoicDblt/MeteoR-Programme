#!/usr/bin/python3
#Author: DIEBOLT Loïc

##########################################################
##                Génération des graphs                 ##
##########################################################

## Imports
from matplotlib import get_cachedir, pyplot as plt
from matplotlib.dates import DateFormatter, HourLocator, datetime as dt
from matplotlib.ticker import FormatStrFormatter
from PIL import Image
from sqlite3 import connect

## Variables et constantes
formatage = DateFormatter("%d/%m %H:%M")
bdd = connect("MeteoR.db") # ouverture base de données
curseur = bdd.cursor() # créé un curseur pour effectuer des actions sur la base

	# Chemin vers le cache de police de Matplot
print("Chemin vers le cache de matplot :", get_cachedir())

	# Police pour le graph
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = "Open Sans SemiBold"
plt.rcParams["font.size"] = 8

# Fonction
def graphs(temp_humi_bdd, jours, temp_humi_type, date_brute, temps):
	curseur.execute("""SELECT %s FROM meteor WHERE temperature_ambiante IS NOT NULL AND humidite_ambiante IS NOT NULL AND date_mesure >= datetime('now', 'localtime', '-%d days', '-3 minutes')""" %(temp_humi_bdd, jours))
	temp_humi_valeurs = curseur.fetchall()
	bdd.commit()
	f = plt.figure()
	ax = f.add_subplot(111)
	date = [dt.datetime.strptime("%s" %d, "%Y-%m-%d %H:%M:%S") for d in date_brute] # converti la date
	if temps == 24:
		ax.xaxis.set_major_locator(HourLocator(interval=4)) # interval d'heures entre chaque tick sur l'axe x
	elif temps == 72:
		ax.xaxis.set_major_locator(HourLocator(interval=12))
	else:
		ax.xaxis.set_major_locator(HourLocator(interval=24))
	ax.xaxis.set_major_formatter(formatage) # formate la date
	ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f")) # arrondi à 0.1
	ax.yaxis.set_major_locator(plt.MaxNLocator(6)) # nombre maximal de ticks sur l'axe y
	plt.plot(date, temp_humi_valeurs, "#0074FF")
	plt.xticks(rotation = 32)
	plt.savefig("graph_%s_%d.png" %(temp_humi_type, temps), dpi = 256)
	plt.close(f)
	img = Image.open("graph_%s_%d.png" %(temp_humi_type, temps))
	img.crop((65, 126, 65+1551, 126+1095)).save("graph_%s_%d.webp" %(temp_humi_type, temps), "WEBP") # (gauche, haut, gauche+largeur, haut+hauteur)
	img.close()

## Programme
curseur.execute("""SELECT date_mesure FROM meteor WHERE temperature_ambiante IS NOT NULL AND humidite_ambiante IS NOT NULL AND date_mesure >= datetime('now', 'localtime', '-1 day', '-3 minutes')""")
date_brute = curseur.fetchall()
bdd.commit()
print("Nombre de données :", len(date_brute))
graphs("temperature_ambiante", 1, "temperature", date_brute, 24)
graphs("humidite_ambiante", 1, "humidite", date_brute, 24)