#!/usr/bin/python3
#Author: DIEBOLT Loïc

##########################################################
##               Génération des moyennes                ##
##########################################################

## Paramètres
JOUR = "2021-08-01" # Jour de la dernière mesure (YYYY-MM-DD)
HEURE_FIN = 23 # Heure de la dernière mesure

## Imports
from sqlite3 import connect

## Variables
bdd_donnees = connect("donnees.db")
curseur_donnees = bdd_donnees.cursor()

bdd_graphs = connect("graphs.db")
curseur_graphs = bdd_graphs.cursor()

curseur_graphs.execute("""DELETE FROM meteor_graphs WHERE date_mesure > "%s 00:03:00" """ %(JOUR))
bdd_graphs.commit()

## Programme
for i in range (1, HEURE_FIN):
	if i == 10:
		date1 = "%s 0%d:00:03" %(JOUR, i-1)
		date2 = "%s %d:00:03" %(JOUR, i)

	elif i < 10:
		date1 = "%s 0%d:00:03" %(JOUR, i-1)
		date2 = "%s 0%d:00:03" %(JOUR, i)
	
	else:
		date1 = "%s %d:00:03" %(JOUR, i-1)
		date2 = "%s %d:00:03" %(JOUR, i)

	print(date1, "-", date2)

	curseur_donnees.execute("""SELECT AVG(temperature_ambiante), AVG(humidite_ambiante) FROM meteor_donnees WHERE date_mesure >= "%s" AND date_mesure < "%s" AND temperature_ambiante IS NOT NULL AND humidite_ambiante IS NOT NULL""" %(date1, date2))
	moyenne_donnees = curseur_donnees.fetchall()[0]

	# En cas de changement d'heure
	if (moyenne_donnees[0] == None or moyenne_donnees[1] == None):
		date1 = "%s 0%d:00:03" %(JOUR, i-2)

		curseur_donnees.execute("""SELECT AVG(temperature_ambiante), AVG(humidite_ambiante) FROM meteor_donnees WHERE date_mesure >= "%s" AND date_mesure < "%s" AND temperature_ambiante IS NOT NULL AND humidite_ambiante IS NOT NULL""" %(date1, date2))
		moyenne_donnees = curseur_donnees.fetchall()[0]

	curseur_graphs.execute("""INSERT INTO meteor_graphs (date_mesure, temperature_ambiante, humidite_ambiante) VALUES (?, ?, ?)""", (date2, round(moyenne_donnees[0]/1, 1), round(moyenne_donnees[1]/1, 1),))
	bdd_graphs.commit()