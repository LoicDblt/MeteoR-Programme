#!/usr/bin/python3
#Author: DIEBOLT Loïc

##########################################################
##                        MeteoR                        ##
##########################################################

## Initialisation ########################################
	# Couleurs
class couleur:
	BLEUC = "\033[36m"
	BLEUF = "\033[94m"
	JAUNE = "\033[93m"
	ROUGE = "\033[91m"
	VERT = "\033[32m"
	FINSTYLE = "\033[0m"

	# Test le nombre d'arguments
from sys import argv

if len(argv) != 5:
	print("%s|ERREUR| Usage : python3 %s <Adresse SFTP> <Port SFTP> <Identifiant SFTP> <Mot de passe SFTP>%s\n" %(couleur.ROUGE, argv[0], couleur.FINSTYLE))
	exit()

	# Message d'initilisation
from os import system
system("clear")
print("%s|INFO| Initialisation du programme, veuillez patienter...%s\n" %(couleur.BLEUC, couleur.FINSTYLE))

## SFTP ##################################################
from hashlib import sha256
def hashing(entree):
	hashing = sha256(str(entree).encode("UTF-8")).hexdigest()
	return hashing

	# Demande et vérification des identifiants
if (
	hashing(argv[3]) != "b717456caf8f0dcf4f0731e9691a6d801326b8f5fa5d61519064715a32800dd8" or
	hashing(argv[4]) != "bf615597de06885bde0376a4e9e89e23a06c5db51f9a96771fbba2c7f32f9912"
):
	print("%s|ERREUR| Identifiant ou mot de passe incorrect, veuillez réessayer%s\n" %(couleur.ROUGE, couleur.FINSTYLE))
	exit()

	# Modules à importer
from adafruit_si7021 import SI7021
from Adafruit_SSD1306 import SSD1306_128_64
from board import I2C
from datetime import datetime, timedelta
from hashlib import sha256
from locale import LC_ALL, setlocale
from matplotlib import use, pyplot as plt
from matplotlib.dates import DateFormatter, HourLocator, datetime as dt
from matplotlib.ticker import FormatStrFormatter
from os import path, mkdir
from paramiko import Transport, SFTPClient
from PIL import Image, ImageDraw, ImageFont
from shutil import copy2
from sqlite3 import connect, PARSE_COLNAMES, PARSE_DECLTYPES
from time import sleep, strftime

## Variables et divers ###################################

	# Chemins
OPEN_SANS = ImageFont.truetype("/usr/local/share/fonts/open-sans-600.ttf", 72)
CHEMIN_SERVEUR = "/home/clients/062d753a5000ca0d94fdbe882000fa5b/web"
CHEMIN_SAUVEGARDE = "sauvegardes"

if (path.isdir("./%s" %CHEMIN_SAUVEGARDE) == False):
	mkdir("./%s" %CHEMIN_SAUVEGARDE)

	# Formatages
use("Agg")
setlocale(LC_ALL, "")
FORMATAGE = DateFormatter("%d/%m %H:%M")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = "Open Sans SemiBold"
plt.rcParams["font.size"] = 8

	# Status
status_envois = [[True, 24], [True, 72], [True, 168]]
erreur_capteur_affichee = False

	# Initialisation du capteur Si7021
while True:
	try:
		capteur = SI7021(I2C())
		break
	except RuntimeError:
		if erreur_capteur_affichee == False:
			print("%s\n|ERREUR| Initialisation du capteur échouée, correction en cours, veuillez patienter...%s\n" %(couleur.ROUGE, couleur.FINSTYLE))
			erreur_capteur_affichee = True

	# Gestion du temps
erreur_sftp = deja_fait = False
temps_graphique = datetime.now() + timedelta(hours=1)

	# Constantes
NOM_BDD_DONNEES = "donnees.db"
NOM_BDD_GRAPHS = "graphs.db"

## SQLite ################################################
	# BDD des données
bdd_donnees = connect(NOM_BDD_DONNEES)
curseur_donnees = bdd_donnees.cursor()
curseur_donnees.execute("""CREATE TABLE IF NOT EXISTS meteor_donnees (date_mesure CHAR, temperature_ambiante FLOAT, humidite_ambiante FLOAT, max_temp FLOAT, min_temp FLOAT, max_humi FLOAT, min_humi FLOAT)""")
curseur_donnees.execute("""SELECT MIN(max_humi) FROM meteor_donnees""")
bdd_deja_init = curseur_donnees.fetchall()
bdd_deja_init_float = bdd_deja_init[0][0] # détermine si la base de données est déjà initialisée
if bdd_deja_init_float == None:
	curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, max_temp, min_temp, max_humi, min_humi) VALUES (datetime('now', 'localtime'), 0, 100, 0, 100)""") # initialise les valeurs max et min de température et humidité
	bdd_donnees.commit()

	# BDD des graphiques
bdd_graphs = connect(NOM_BDD_GRAPHS, detect_types=PARSE_COLNAMES|PARSE_DECLTYPES)
curseur_graphs = bdd_graphs.cursor()
curseur_graphs.execute("""CREATE TABLE IF NOT EXISTS meteor_graphs (date_mesure CHAR, temperature_ambiante FLOAT, humidite_ambiante FLOAT)""")
bdd_graphs.commit()

## Connexion par SFTP ####################################
def connexion_sftp():
	global session_sftp
	global sftp
	global erreur_sftp
	try:
		session_sftp = Transport(argv[1], int(argv[2]))
		session_sftp.connect(username = argv[3], password = argv[4])
		sftp = SFTPClient.from_transport(session_sftp)
		erreur_sftp = False
	except:
		erreur_sftp = True
		print(couleur.JAUNE + "|Erreur - " + strftime("%d/%m ") + "à " + strftime("%H:%M") + "| La connexion par SFTP au serveur a échoué" + couleur.FINSTYLE)

def deconnexion_sftp():
	if erreur_sftp == False:
		if session_sftp: session_sftp.close()
		if sftp: sftp.close()

## Envoi de fichiers par SFTP ############################
def envoi_fichier(nom_fichier):
	if nom_fichier == NOM_BDD_DONNEES:
		chemin = "%s/bdd/%s" %(CHEMIN_SERVEUR, nom_fichier)
	else:
		chemin = "%s/img/graphs/%s" %(CHEMIN_SERVEUR, nom_fichier)
	sftp.put(nom_fichier, chemin)

def gestion_envoi(nom_fichier):
	if erreur_sftp == False:
		for nbr_essais in range(1, 3):
			try:
				envoi_fichier("%s" %nom_fichier)
				return True
			except:
				sleep(5*nbr_essais)
		print(couleur.JAUNE + "|Erreur - " + strftime("%d/%m ") + "à " + strftime("%H:%M") + "| L'envoi du fichier %s a échoué" %nom_fichier + couleur.FINSTYLE)
	return False

## Récupération des valeurs minimales et maximales #######
def recup_max_min(max_min_op, max_min_temp_humi):
	curseur_donnees.execute("""SELECT %s(%s) FROM meteor_donnees""" %(max_min_op, max_min_temp_humi))
	max_min_temp_humi_valeur = curseur_donnees.fetchall()
	return max_min_temp_humi_valeur[0][0]

## Création du graphique #################################
def graphs(temp_humi_bdd, jours, temp_humi_type, date_brute, temps):
	curseur_graphs.execute("""SELECT %s FROM meteor_graphs WHERE date_mesure >= datetime('now', 'localtime', '-%d days', '-3 minutes')""" %(temp_humi_bdd, jours))
	temp_humi_valeurs = curseur_graphs.fetchall()
	f = plt.figure()
	ax = f.add_subplot(111)
	date = [dt.datetime.strptime("%s" %d, "%Y-%m-%d %H:%M:%S") for d in date_brute] # converti la date
	if temps == 24:
		ax.xaxis.set_major_locator(HourLocator(interval=4)) # interval d'heures entre chaque tick sur l'axe x
	elif temps == 72:
		ax.xaxis.set_major_locator(HourLocator(interval=12))
	else:
		ax.xaxis.set_major_locator(HourLocator(interval=24))
	ax.xaxis.set_major_formatter(FORMATAGE) # formate la date
	ax.yaxis.set_major_formatter(FormatStrFormatter("%.1f")) # arrondi à 0.1
	ax.yaxis.set_major_locator(plt.MaxNLocator(6)) # nombre maximal de ticks sur l'axe y
	plt.plot(date, temp_humi_valeurs, "#0074FF")
	plt.xticks(rotation = 32)
	plt.savefig("graph_%s_%d.png" %(temp_humi_type, temps), dpi = 256, transparent = True)
	plt.close(f)
	img = Image.open("graph_%s_%d.png" %(temp_humi_type, temps))
	img.crop((65, 126, 65+1551, 126+1095)).save("graph_%s_%d.webp" %(temp_humi_type, temps), "WEBP") # (gauche, haut, gauche+largeur, haut+hauteur)
	img.close()
	return gestion_envoi("graph_%s_%d.webp" %(temp_humi_type, temps))

## Ecran #################################################
affichage = SSD1306_128_64(rst=None)
affichage.begin()
affichage.clear()
affichage.display()
affichage_largeur = affichage.width
affichage_hauteur = affichage.height
affichage_haut = -2
affichage_abscisse = 0
affichage_img = Image.new("1", (affichage_largeur, affichage_hauteur))
POLICE = ImageFont.load_default()
TRANSPARENT = 255

## Programme principal ###################################
system("clear")
print("%s|INFO| Initialisation terminée%s" %(couleur.BLEUC, couleur.FINSTYLE))
print("%s|INFO| Les messages d'erreur s'afficheront dans cette console%s\n" %(couleur.BLEUF, couleur.FINSTYLE))
while True:
	connexion_sftp()

	# Calcul du temps de départ
	temps_arrivee = (datetime.now() + timedelta(minutes = 3)).replace(second = 0, microsecond = 0)
	if (temps_arrivee.minute > 0 and temps_arrivee.minute < 3):
		temps_arrivee = temps_arrivee.replace(minute = 0)

	# Détection de changement d'heure
	verif_changement_heure = int((temps_arrivee - datetime.now()).total_seconds())
	if verif_changement_heure < 0:
		print("%s|INFO| Passage à l'heure d'hiver%s" %(couleur.BLEUC, couleur.FINSTYLE))
		temps_arrivee = (temps_arrivee + timedelta(hours = 1))
	elif verif_changement_heure > 180:
		print("%s|INFO| Passage à l'heure d'été%s" %(couleur.BLEUC, couleur.FINSTYLE))
		temps_arrivee = (temps_arrivee + timedelta(hours = -1))

	# Données
		# Température
	temperature = round(capteur.temperature, 1)

		# Humidité
	humidite = round(capteur.relative_humidity, 1)

		# Enregistrement
	curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, temperature_ambiante, humidite_ambiante) VALUES (datetime('now', 'localtime'), %f, %f)""" %(temperature, humidite))
	bdd_donnees.commit()

		# Température MAX-MIN
	if temperature > recup_max_min("MAX", "max_temp"):
		curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, max_temp) VALUES (datetime('now', 'localtime'), %f)""" %temperature)
		bdd_donnees.commit()

	if temperature < recup_max_min("MIN", "min_temp"):
		curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, min_temp) VALUES (datetime('now', 'localtime'), %f)""" %temperature)
		bdd_donnees.commit()

		# Humidité MAX-MIN
	if humidite > recup_max_min("MAX", "max_humi"):
		curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, max_humi) VALUES (datetime('now', 'localtime'), %f)""" %humidite)
		bdd_donnees.commit()

	if humidite < recup_max_min("MIN", "min_humi"):
		curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, min_humi) VALUES (datetime('now', 'localtime'), %f)""" %humidite)
		bdd_donnees.commit()

		# Envoi de la BDD au serveur web
	gestion_envoi(NOM_BDD_DONNEES)

		# Renvoi des graphiques qui ont échoué
	for i in range(len(status_envois)):
		if (
			status_envois[i][0] == False and
			gestion_envoi("graph_temperature_%s.webp" %(status_envois[i][1])) == True and
			gestion_envoi("graph_humidite_%s.webp" %(status_envois[i][1])) == True
		):
			status_envois[i][0] = True

	# Graphiques
		# Changement d'heure (hiver, -1 heure)
	curseur_graphs.execute("""SELECT MAX(date_mesure) as "[timestamp]" FROM meteor_graphs""")
	derniere_mesure = curseur_graphs.fetchall()[0][0]
	maintenant = datetime.now()
	if (
		(
			derniere_mesure == None and
			maintenant.hour == temps_graphique.hour
		)
		or
		(
			derniere_mesure != None and
			(
				maintenant.hour == temps_graphique.hour and
				maintenant.hour != derniere_mesure.hour or
				maintenant.date() != derniere_mesure.date()
			)
		)
	):
		curseur_donnees.execute("""SELECT AVG(temperature_ambiante), AVG(humidite_ambiante) FROM meteor_donnees WHERE date_mesure >= datetime('now', 'localtime', '-1 hour', '1 minute') AND temperature_ambiante IS NOT NULL AND humidite_ambiante IS NOT NULL""")
		moyenne_donnees = curseur_donnees.fetchall()[0]

		# Changement d'heure (été, +1 heure)
		if (moyenne_donnees[0] == None or moyenne_donnees[1] == None):
			curseur_donnees.execute("""SELECT AVG(temperature_ambiante), AVG(humidite_ambiante) FROM meteor_donnees WHERE date_mesure >= datetime('now', 'localtime', '-2 hours', '1 minute') AND temperature_ambiante IS NOT NULL AND humidite_ambiante IS NOT NULL""")
			moyenne_donnees = curseur_donnees.fetchall()[0]

		curseur_graphs.execute("""INSERT INTO meteor_graphs (date_mesure, temperature_ambiante, humidite_ambiante) VALUES (datetime('now', 'localtime'), %f, %f)""" %(round(moyenne_donnees[0]/1, 1), round(moyenne_donnees[1]/1, 1)))
		bdd_graphs.commit()

		temps_graphique = datetime.now() + timedelta(hours=1)

		# Graphique sur 1 jour
		curseur_graphs.execute("""SELECT date_mesure FROM meteor_graphs WHERE date_mesure >= datetime('now', 'localtime', '-1 day', '-3 minutes')""")
		date_brute = curseur_graphs.fetchall()
		if (
			graphs("temperature_ambiante", 1, "temperature", date_brute, 24) == False or
			graphs("humidite_ambiante", 1, "humidite", date_brute, 24) == False
		):
			status_envois[0][0] = False

		# Graphique sur 3 jours
		curseur_graphs.execute("""SELECT date_mesure FROM meteor_graphs WHERE date_mesure >= datetime('now', 'localtime', '-3 days', '-3 minutes')""")
		date_brute = curseur_graphs.fetchall()
		if (
			graphs("temperature_ambiante", 3, "temperature", date_brute, 72) == False or
			graphs("humidite_ambiante", 3, "humidite", date_brute, 72) == False
		):
			status_envois[1][0] = False

		# Graphique sur 1 semaine
		curseur_graphs.execute("""SELECT date_mesure FROM meteor_graphs WHERE date_mesure >= datetime('now', 'localtime', '-7 days', '-3 minutes')""")
		date_brute = curseur_graphs.fetchall()
		if (
			graphs("temperature_ambiante", 7, "temperature", date_brute, 168) == False or
			graphs("humidite_ambiante", 7, "humidite", date_brute, 168) == False
		):
			status_envois[2][0] = False

		# Nettoyage des BDD
		if maintenant.hour == 00:
			# Sauvegardes
			copy2("./%s" %NOM_BDD_DONNEES, "./%s/donnees_sauvegarde.db" %CHEMIN_SAUVEGARDE)
			copy2("./%s" %NOM_BDD_GRAPHS, "./%s/graphs_sauvegarde.db" %CHEMIN_SAUVEGARDE)

			# BDD des graphiques
			curseur_graphs.execute("""DELETE FROM meteor_graphs WHERE date_mesure <= datetime('now', 'localtime', '-7 days', '-3 minutes')""")
			bdd_graphs.commit()

			# BDD des données
			curseur_donnees.execute("""DELETE FROM meteor_donnees WHERE (max_temp NOT IN (SELECT MAX(max_temp) FROM meteor_donnees) OR min_temp NOT IN (SELECT MIN(min_temp) FROM meteor_donnees) OR max_humi NOT IN (SELECT MAX(max_humi) FROM meteor_donnees) OR min_humi NOT IN (SELECT MIN(min_humi) FROM meteor_donnees)) OR (temperature_ambiante IS NOT NULL AND humidite_ambiante IS NOT NULL AND date_mesure NOT IN (SELECT MAX(date_mesure) FROM meteor_donnees))""")
			bdd_donnees.commit()

	# Ecran
	dessin = ImageDraw.Draw(affichage_img)
	dessin.rectangle((0, 0, affichage_largeur, affichage_hauteur), outline = 0, fill = 0)
	dessin.text((affichage_abscisse, affichage_haut), "Date : " + str(strftime("%d %B")), font = POLICE, fill = TRANSPARENT)
	dessin.text((affichage_abscisse, affichage_haut+16), "Température : " + str(temperature) + "°C", font = POLICE, fill = 255)
	dessin.text((affichage_abscisse, affichage_haut+32), "Humidité : " + str(humidite) + "%", font = POLICE, fill = TRANSPARENT)
	dessin.text((affichage_abscisse, affichage_haut+48), "Dernière mise à jour : ", font = POLICE, fill = TRANSPARENT)
	dessin.text((affichage_abscisse, affichage_haut+56), str(strftime("%H:%M")), font = POLICE, fill = TRANSPARENT)
	affichage.image(affichage_img)
	affichage.display()

	# Fermeture de session SFTP
	deconnexion_sftp()

	# Attente pour la mesure suivante
	duree_attente = (temps_arrivee - datetime.now()).total_seconds()
	if (duree_attente >= 0):
		sleep(duree_attente)
	else:
		print("%s|ERREUR| Durée d'attente calculée inférieure à 0 | temps_arrivee = %d - datetime.now = %d%s\n" %(temps_arrivee, datetime.now(), couleur.ROUGE, couleur.FINSTYLE))