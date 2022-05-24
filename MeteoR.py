#!/usr/bin/python3
#Author: DIEBOLT Loïc

##########################################################
##                        MeteoR                        ##
##########################################################

## Initialisation ########################################
	# Couleurs pour les messages affichés à l'utilisateur
class couleur:
	BLEU_CLAIR = "\033[36m"
	BLEU_FONCE = "\033[94m"
	JAUNE = "\033[93m"
	ROUGE = "\033[91m"
	FIN_STYLE = "\033[0m"

	# Vérifie le nombre d'arguments
from sys import argv
if (len(argv) != 6):
	print("%s|ERREUR| Usage : python3 %s <Adresse SFTP> <Port SFTP> <Chemin du dossier web sur serveur> <Identifiant SFTP> <Mot de passe SFTP>%s" %(couleur.ROUGE, argv[0], couleur.FIN_STYLE))
	exit()

	# Message d'initialisation
from os import system
system("clear")
print("%s|INFO| Initialisation du programme, veuillez patienter...%s" %(couleur.BLEU_CLAIR, couleur.FIN_STYLE))

## Import des modules ####################################
from adafruit_si7021 import SI7021
from Adafruit_SSD1306 import SSD1306_128_64
from board import I2C
from datetime import datetime, timedelta
from locale import LC_ALL, setlocale
from os import path, mkdir
from paramiko import Transport, SFTPClient, AuthenticationException
from PIL import Image, ImageDraw, ImageFont
from shutil import copy2
from sqlite3 import connect, PARSE_COLNAMES, PARSE_DECLTYPES
from time import localtime, sleep, strftime

## Variables et initialisation ###########################
	# Chemins
CHEMIN_DOSSIER_WEB_SERVEUR = argv[3]
CHEMIN_SAUVEGARDE_LOCAL = "sauvegardes"

if (path.isdir("./%s" %CHEMIN_SAUVEGARDE_LOCAL) == False):
	mkdir("./%s" %CHEMIN_SAUVEGARDE_LOCAL)

	# Formatages
setlocale(LC_ALL, "")

	# Status
status_envoi = True
erreur_capteur_affichee = False
hors_ligne = False

	# Initialisation du capteur de température et humidité (Si7021)
while True:
	try:
		capteur = SI7021(I2C())
		break
	except RuntimeError:
		if (erreur_capteur_affichee == False):
			print("%s\n|ERREUR| Initialisation du capteur échouée, correction en cours, veuillez patienter...%s" %(couleur.ROUGE, couleur.FIN_STYLE))
			erreur_capteur_affichee = True

	# Gestion du temps
erreur_sftp = False
temps_moyenne = datetime.utcnow() + timedelta(hours = 1)

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
if (bdd_deja_init_float == None):
	curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, max_temp, min_temp, max_humi, min_humi) VALUES (datetime('now', 'localtime'), 0, 100, 0, 100)""") # initialise les valeurs min et max de température et d'humidité
	bdd_donnees.commit()

	# BDD des graphs
bdd_graphs = connect(NOM_BDD_GRAPHS, detect_types=PARSE_COLNAMES|PARSE_DECLTYPES)
curseur_graphs = bdd_graphs.cursor()
curseur_graphs.execute("""CREATE TABLE IF NOT EXISTS meteor_graphs (date_mesure CHAR, temperature_ambiante FLOAT, humidite_ambiante FLOAT)""")
bdd_graphs.commit()

## Connexion par SFTP ####################################
def connexion_sftp():
	global session_sftp
	global sftp
	global erreur_sftp
	global hors_ligne
	try:
		session_sftp = Transport(argv[1], int(argv[2]))
		session_sftp.connect(username = argv[4], password = argv[5])
		sftp = SFTPClient.from_transport(session_sftp)
		erreur_sftp = False
	except AuthenticationException:
		if (hors_ligne == False):
			print(couleur.ROUGE + "|Erreur - " + strftime("%d/%m ") + "à " + strftime("%H:%M") + "| Identifiants de connexion au serveur SFTP erronés.\nFonctionnement hors-ligne jusqu'au redémarrage du programme..." + couleur.FIN_STYLE)
			hors_ligne = True
	except:
		print(couleur.JAUNE + "|Erreur - " + strftime("%d/%m ") + "à " + strftime("%H:%M") + "| La connexion par SFTP au serveur a échoué" + couleur.FIN_STYLE)
		erreur_sftp = True

def deconnexion_sftp():
	if (erreur_sftp == False):
		if session_sftp: session_sftp.close()
		if sftp: sftp.close()

## Envoi de fichiers par SFTP ############################
def envoi_fichier(nom_fichier):
	chemin = "%s/bdd/%s" %(CHEMIN_DOSSIER_WEB_SERVEUR, nom_fichier)
	sftp.put(nom_fichier, chemin)

def gestion_envoi(nom_fichier):
	if (
		erreur_sftp == False and
		hors_ligne == False
	):
		for nbr_essais in range(1, 3):
			try:
				envoi_fichier("%s" %nom_fichier)
				return True
			except:
				sleep(5*nbr_essais)
		print(couleur.JAUNE + "|Erreur - " + strftime("%d/%m ") + "à " + strftime("%H:%M") + "| L'envoi du fichier %s a échoué" %nom_fichier + couleur.FIN_STYLE)
	return False

## Récupération des valeurs minimales et maximales #######
def recup_max_min(operation, temp_humi):
	curseur_donnees.execute("""SELECT %s(%s) FROM meteor_donnees""" %(operation, temp_humi))
	max_min_temp_humi_valeur = curseur_donnees.fetchall()
	return max_min_temp_humi_valeur[0][0]

## Paramétrage de l'écran ################################
affichage = SSD1306_128_64(rst = None)
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
	# Messages d'information
system("clear")
print("%s|INFO| Initialisation terminée%s" %(couleur.BLEU_CLAIR, couleur.FIN_STYLE))
print("%s|INFO| Les messages d'erreur s'afficheront dans cette console%s\n" %(couleur.BLEU_FONCE, couleur.FIN_STYLE))

	# Attente mise en route des services réseaux
sleep(5)

while True:
	if (hors_ligne == False):
		connexion_sftp()

	# Calcul du temps de départ
	temps_arrivee = (datetime.utcnow() + timedelta(minutes = 3)).replace(second = 0, microsecond = 0)
	if (temps_arrivee.minute > 0 and temps_arrivee.minute < 3):
		temps_arrivee = temps_arrivee.replace(minute = 0)

	# Récupération des données (arrondies à 0.1 près)
		# Température
	temperature = round(capteur.temperature, 1)

		# Humidité
	humidite = round(capteur.relative_humidity, 1)

		# Enregistrement
	curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, temperature_ambiante, humidite_ambiante) VALUES (datetime('now', 'localtime'), %f, %f)""" %(temperature, humidite))
	bdd_donnees.commit()

		# Température MAX-MIN
	if (temperature > recup_max_min("MAX", "max_temp")):
		curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, max_temp) VALUES (datetime('now', 'localtime'), %f)""" %temperature)
		bdd_donnees.commit()

	if (temperature < recup_max_min("MIN", "min_temp")):
		curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, min_temp) VALUES (datetime('now', 'localtime'), %f)""" %temperature)
		bdd_donnees.commit()

		# Humidité MAX-MIN
	if (humidite > recup_max_min("MAX", "max_humi")):
		curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, max_humi) VALUES (datetime('now', 'localtime'), %f)""" %humidite)
		bdd_donnees.commit()

	if (humidite < recup_max_min("MIN", "min_humi")):
		curseur_donnees.execute("""INSERT INTO meteor_donnees (date_mesure, min_humi) VALUES (datetime('now', 'localtime'), %f)""" %humidite)
		bdd_donnees.commit()

		# Envoi de la BDD des données actuelles au serveur
	gestion_envoi(NOM_BDD_DONNEES)

		# Renvoi la BDD des graphs si cela avait échoué précédemment
	if (
		status_envoi == False and
		gestion_envoi(NOM_BDD_GRAPHS) == True
	):
		status_envoi = True

	# Calcul et enregistrement des moyennes
	maintenant = datetime.utcnow()
	if (maintenant.hour == temps_moyenne.hour):
			# Calcul l'heure pour la prochaine moyenne
		temps_moyenne = datetime.utcnow() + timedelta(hours = 1)

			# Ajout de la moyenne dans la BDD
		curseur_donnees.execute("""SELECT AVG(temperature_ambiante), AVG(humidite_ambiante) FROM meteor_donnees WHERE date_mesure >= datetime('now', 'localtime', '-1 hour', '1 minute') AND temperature_ambiante IS NOT NULL AND humidite_ambiante IS NOT NULL""")
		moyenne_donnees = curseur_donnees.fetchall()[0]

			# Vérification que les données existes (passage de UTC+1 à UTC+2)
		if (moyenne_donnees[0] != None and moyenne_donnees[1] != None):
			curseur_graphs.execute("""INSERT INTO meteor_graphs (date_mesure, temperature_ambiante, humidite_ambiante) VALUES (datetime('now', 'localtime'), %f, %f)""" %(round(moyenne_donnees[0]/1, 1), round(moyenne_donnees[1]/1, 1)))
			bdd_graphs.commit()

				# Envoi de la BDD des graphs
			status_envoi = gestion_envoi(NOM_BDD_GRAPHS)

			# Nettoyage des BDD, une fois par jour, à minuit (en fonction du fuseau)
		if (
			(localtime().tm_isdst == 1 and maintenant.hour == 22) or
			(localtime().tm_isdst == 0 and maintenant.hour == 23)
		):
				# Sauvegardes en local des BDD de la journée avant suppression
			copy2("./%s" %NOM_BDD_DONNEES, "./%s/donnees_sauvegarde.db" %CHEMIN_SAUVEGARDE_LOCAL)
			copy2("./%s" %NOM_BDD_GRAPHS, "./%s/graphs_sauvegarde.db" %CHEMIN_SAUVEGARDE_LOCAL)

				# Nettoyage BDD des graphs
			curseur_graphs.execute("""DELETE FROM meteor_graphs WHERE date_mesure <= datetime('now', 'localtime', '-31 days', '-3 minutes')""")
			bdd_graphs.commit()

				# Nettoyage BDD des données
			curseur_donnees.execute("""DELETE FROM meteor_donnees WHERE (max_temp NOT IN (SELECT MAX(max_temp) FROM meteor_donnees) OR min_temp NOT IN (SELECT MIN(min_temp) FROM meteor_donnees) OR max_humi NOT IN (SELECT MAX(max_humi) FROM meteor_donnees) OR min_humi NOT IN (SELECT MIN(min_humi) FROM meteor_donnees)) OR (temperature_ambiante IS NOT NULL AND humidite_ambiante IS NOT NULL AND date_mesure NOT IN (SELECT MAX(date_mesure) FROM meteor_donnees))""")
			bdd_donnees.commit()

	# Affichage des informations sur l'écran (SSD1306)
	dessin = ImageDraw.Draw(affichage_img)
	dessin.rectangle((0, 0, affichage_largeur, affichage_hauteur), outline = 0, fill = 0)
	dessin.text((affichage_abscisse, affichage_haut), "Date : " + str(strftime("%d %B")), font = POLICE, fill = TRANSPARENT)
	dessin.text((affichage_abscisse, affichage_haut + 16), "Température : " + str(temperature) + "°C", font = POLICE, fill = 255)
	dessin.text((affichage_abscisse, affichage_haut + 32), "Humidité : " + str(humidite) + "%", font = POLICE, fill = TRANSPARENT)
	dessin.text((affichage_abscisse, affichage_haut + 48), "Dernière mise à jour : ", font = POLICE, fill = TRANSPARENT)
	dessin.text((affichage_abscisse, affichage_haut + 56), str(strftime("%H:%M")), font = POLICE, fill = TRANSPARENT)
	affichage.image(affichage_img)
	affichage.display()

	# Fermeture de la session SFTP
	if (hors_ligne == False):
		deconnexion_sftp()

	# Attente pour la mesure suivante
	duree_attente = (temps_arrivee - datetime.utcnow()).total_seconds()
	if (duree_attente >= 0):
		sleep(duree_attente)
	else:
		print("%s|ERREUR| Durée d'attente calculée inférieure à 0 | temps_arrivee = %d - datetime.utcnow = %d%s\n" %(temps_arrivee, datetime.utcnow(), couleur.ROUGE, couleur.FIN_STYLE))