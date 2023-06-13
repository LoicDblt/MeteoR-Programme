#! /usr/bin/python3
# Auteur : DIEBOLT Loïc

################################################################################
#                                    MeteoR                                    #
################################################################################

## Initialisation ##############################################################
# Couleurs pour les messages affichés à l'utilisateur
class couleur:
	BLEU_CLAIR = "\033[36m"
	BLEU_FONCE = "\033[94m"
	JAUNE = "\033[93m"
	ROUGE = "\033[91m"
	VERT = "\033[32m"
	FIN_STYLE = "\033[0m"

import os
import sys

# Vérifie le nombre d'arguments et sélectionne le mode de fonctionnement
# (local ou connecté)
if (len(sys.argv) == 1):
	mode_local = True

elif (len(sys.argv) == 5):
	mode_local = False

else:
	print(
		"{0}|Erreur| Usage : python3 {1} <Adresse SFTP> "
		.format(couleur.ROUGE, sys.argv[0]) +
		"<Chemin racine sur le serveur> <Identifiant SFTP> " +
		"<Clé SSH privée>{0}".format(couleur.FIN_STYLE)
	)
	exit()

# Message d'initialisation
os.system("clear")
print("{0}|Info| Initialisation du programme, veuillez patienter...{1}"
	.format(couleur.BLEU_CLAIR, couleur.FIN_STYLE)
)

## Import des modules ##########################################################
import adafruit_si7021
import Adafruit_SSD1306
import board
import datetime as dt
import glob
import locale
import paramiko
import PIL as pil
import shutil
import sqlite3
import time

## Messages d'erreur ###########################################################
"""
@brief	Affiche un message d'erreur en rouge, avec la date et l'heure

@param	message	Le message d'erreur à afficher
"""
def messageErreur(message):
	print("{0}|Erreur - {1} à {2}| {3}{4}".format(
		couleur.ROUGE,
		time.strftime("%d/%m"),
		time.strftime("%H:%M"),
		message, couleur.FIN_STYLE)
	)
	return

## Variables et initialisation #################################################
# Chemins et noms des bases de données
CHEMIN_SAUVEGARDE_LOCAL = "./sauvegardes"
NOM_BDD_MESURES = "donnees.db"
NOM_BDD_MOYENNES = "graphs.db"

# Créé le dossier de sauvegarde local s'il n'existe pas
if (os.path.isdir(CHEMIN_SAUVEGARDE_LOCAL) == False):
	os.mkdir(CHEMIN_SAUVEGARDE_LOCAL)

# Formatage de la date et de l'heure
locale.setlocale(locale.LC_ALL, "")

# Status
status_envoi = False
erreur_capteur_affichee = False
erreur_sftp_affichee = False

# Gestion du temps
erreur_sftp = False
temps_moyenne = dt.datetime.utcnow() + dt.timedelta(hours = 1)
NBR_JOURS = 31

# Mesures de température et d'humidité
temperature = 0
humidite = 0

# Paramètres de connexion au serveur SFTP
if (mode_local == False):
	ADRESSE_SFTP = sys.argv[1]
	CHEMIN_DOSSIER_WEB_SERVEUR = sys.argv[2]
	IDENTIFIANT = sys.argv[3]
	CLE_SSH_PRIVEE = sys.argv[4]
	PORT_SFTP = 22

## Initialisation capteur de température et d'humidité (Si7021) ################
while True:
	try:
		capteur = adafruit_si7021.SI7021(board.I2C())
		break

	except RuntimeError:
		if (erreur_capteur_affichee == False):
			messageErreur(
				"Initialisation du capteur échouée, " +
				"correction en cours, veuillez patienter..."
			)
			erreur_capteur_affichee = True

## Bases de données ############################################################
# Créé la base de données des mesures, si elle n'existe pas
bdd_mesures = sqlite3.connect(NOM_BDD_MESURES)
curseur_mesures = bdd_mesures.cursor()
curseur_mesures.execute("""
	CREATE TABLE IF NOT EXISTS meteor_donnees
	(date_mesure CHAR, temperature_ambiante FLOAT, humidite_ambiante FLOAT,
	max_temp FLOAT, min_temp FLOAT, max_humi FLOAT, min_humi FLOAT)
""")

# Initialise les mesures min et max de température et d'humidité, si la base de
# données est vide
curseur_mesures.execute("""SELECT MIN(max_humi) FROM meteor_donnees""")
mesure_min = curseur_mesures.fetchall()[0][0]

if (mesure_min == None):
	curseur_mesures.execute("""
		INSERT INTO meteor_donnees
		(date_mesure, max_temp, min_temp, max_humi, min_humi)
		VALUES (datetime("now", "localtime"), 0, 100, 0, 100)
	""")
	bdd_mesures.commit()

# Créé la base de données des moyennes, si elle n'existe pas
bdd_moyennes = sqlite3.connect(NOM_BDD_MOYENNES,
	detect_types = sqlite3.PARSE_COLNAMES|sqlite3.PARSE_DECLTYPES
)
curseur_moyennes = bdd_moyennes.cursor()
curseur_moyennes.execute("""
	CREATE TABLE IF NOT EXISTS meteor_graphs
	(date_mesure CHAR, temperature_ambiante FLOAT, humidite_ambiante FLOAT)
""")
bdd_moyennes.commit()

## Paramétrage de l'écran ######################################################
affichage = Adafruit_SSD1306.SSD1306_128_64(rst = None)
affichage.begin()
affichage.clear()
affichage.display()
AFFICHAGE_LARGEUR = affichage.width
AFFICHAGE_HAUTEUR = affichage.height
AFFICHAGE_HAUT = -2
AFFICHAGE_ABSCISSE = 0
AFFICHAGE_IMAGE = pil.Image.new('1', (AFFICHAGE_LARGEUR, AFFICHAGE_HAUTEUR))
POLICE = pil.ImageFont.load_default()
TRANSPARENT = 255

## Connexion par SFTP ##########################################################
"""
@brief	Etablie la connexion SFTP au serveur
@return 0 si la connexion est établie, -1 en cas d'erreur d'autentification,
		-2 en cas d'erreur de formatage de la clé privée, -3 en cas d'erreur de
		connexion au serveur
"""
def connexion_sftp():
	global client
	global sftp
	global erreur_sftp
	global erreur_sftp_affichee
	global mode_local

	if (mode_local == True):
		return

	try:
		cle_ssh = paramiko.Ed25519Key.from_private_key_file(CLE_SSH_PRIVEE)

		client = paramiko.Transport(ADRESSE_SFTP, PORT_SFTP)
		client.connect(username = IDENTIFIANT, pkey = cle_ssh)
		sftp = paramiko.SFTPClient.from_transport(client)

		erreur_sftp = False
		if (erreur_sftp_affichee == True):
			erreur_sftp_affichee = False
			print("{0}|Info - {1} à {2}| Connexion par SFTP rétablie{3}".format(
				couleur.VERT,
				time.strftime("%d/%m "),
				time.strftime("%H:%M"),
				couleur.FIN_STYLE)
			)
		return 0

	except paramiko.AuthenticationException:
		if (erreur_sftp_affichee == False):
			erreur_sftp_affichee = True
			messageErreur(
				"Identifiant ou mauvaise clé SSH fournie.\n" +
				"Une nouvelle tentative sera effectuée après chaque " +
				"nouvelle mesure.\nVeuillez relancer le programme si " +
				"vous souhaitez modifier les identifiants."
			)
		erreur_sftp = True
		return -1

	except paramiko.ssh_exception.SSHException:
			messageErreur(
				"Format de clé SSH non reconnu (chiffrement Ed25519 attendu)" +
				", passage en mode local"
			)
			mode_local = True
			return -2

	except OSError as erreur:
		messageErreur(erreur)
		return -3

	except:
		erreur_sftp = True
		messageErreur("La connexion par SFTP au serveur a échoué")
		return -4

"""
@brief	Ferme la connexion en SFTP au serveur, si elle est ouverte
"""
def deconnexion_sftp():
	if (mode_local == True):
		return

	if (erreur_sftp == False):
		if client: client.close()
		if sftp: sftp.close()
		return

## Envoi de fichiers par SFTP ##################################################
"""
@brief	Envoi la base de données SQLite au serveur

@param	nom_fichier	Le nom du fichier à envoyer

@return	0 si l'envoi s'est bien déroulé, -1 si le dossier n'existe pas sur le
		serveur, -2 si la connexion a échoué
"""
def envoi_fichier(nom_fichier):
	chemin = "{0}/bdd/{1}".format(CHEMIN_DOSSIER_WEB_SERVEUR, nom_fichier)
	try:
		sftp.put(nom_fichier, chemin)
		return 0

	except IOError:
		sftp.mkdir("{0}/bdd".format(CHEMIN_DOSSIER_WEB_SERVEUR))
		sftp.put(nom_fichier, chemin)
		return -1

	except:
		messageErreur("Tentative de reconnexion au serveur")
		deconnexion_sftp()
		connexion_sftp()
		return -2

"""
@brief	Gère l'envoi de la base de données SQLite au serveur.
		En cas, d'erreur de connexion, plusieurs tentatives seront effectuées.

@param	nom_fichier	Le nom du fichier à envoyer

@return	0 si l'envoi a réussi, -1 en cas d'erreur
"""
def gestion_envoi(nom_fichier):
	if (mode_local == True):
		return

	if (erreur_sftp == False):
		for nbr_essais in range(1, 3):
			try:
				envoi_fichier(nom_fichier)
				return 0

			except:
				time.sleep(5 * nbr_essais)
		messageErreur("L'envoi du fichier {0} a échoué".format(nom_fichier))
		return -1

## Récupération des mesures ####################################################
"""
@brief	Récupère la mesure de température ou d'humidité

@param	type_mesure	Chaîne de caractères indiquant le type de mesure
		("temperature" ou "humidite")

@return	La mesure récupérée, ou None en cas d'erreur
"""
def recup_mesure(type_mesure):
	if (type_mesure != "temperature" and type_mesure != "humidite"):
		messageErreur("recup_mesure | Type de mesure inconnu")
		return None

	# Récupération de la mesure (arrondie à 0.1)
	for _ in range(4):
		try:
			if (type_mesure == "temperature"):
				mesure = round(capteur.temperature, 1)

			elif (type_mesure == "humidite"):
				mesure = round(capteur.relative_humidity, 1)
			break

		except:
			mesure = None
			time.sleep(0.1)
	return mesure

"""
@brief	Récupère la mesure minimale ou maximale de température ou d'humidité

@param	type_operation	Chaîne de caractères indiquant le type d'opération
						("MIN" ou "MAX")
@param	type_mesure		Chaîne de caractères indiquant le type de mesure
						("temperature" ou "humidite")

@return	La mesure récupérée, -1 en cas d'erreur de type d'opération, ou -2 en
		cas d'erreur de type de mesure
"""
def recup_borne(type_operation, type_mesure):
	if (type_operation != "MIN" and type_operation != "MAX"):
		messageErreur("recup_borne | Type d'opération inconnu")
		return -1

	elif (
		type_mesure != "max_temp" and type_mesure != "min_temp" and
		type_mesure != "max_humi" and type_mesure != "min_humi"
	):
		messageErreur("recup_borne | Type de mesure inconnu")
		return -2

	curseur_mesures.execute("""
		SELECT {0}({1}) FROM meteor_donnees
	""".format(type_operation, type_mesure))
	return curseur_mesures.fetchall()[0][0]

## Enregistrement des mesures ##################################################
"""
@brief	Enregistre la mesure de température et d'humidité dans la base de
		données

@param	temperature	Mesure de température à enregistrer
@param	humidite	Mesure d'humidité à enregistrer

@return	0 si les mesures ont été enregistrées, -1 en cas d'erreur
"""
def enregistrement_mesures(temperature, humidite):
	if (temperature == None or humidite == None):
		return -1

	curseur_mesures.execute("""
		INSERT INTO meteor_donnees
		(date_mesure, temperature_ambiante, humidite_ambiante)
		VALUES (datetime("now", "localtime"), {0}, {1})
	""".format(temperature, humidite))
	bdd_mesures.commit()
	return 0

"""
@brief	Enregistre la mesure minimale ou maximale de température ou
		d'humidité, si la mesure est supérieure ou inférieure à la borne
		enregistrée dans la base de données

@param	mesure		Mesure à enregistrer
@param	type_mesure	Chaîne de caractères indiquant le type de mesure
					("temp" ou "humi")

@return	0 si la mesure a été enregistrée, -1 en cas d'erreur de type de mesure,
		-2 en cas de mesure nulle
"""
def enregistrer_borne(mesure, type_mesure):
	if (type_mesure != "temp" and type_mesure != "humi"):
		messageErreur("enregistrer_borne | Type de mesure inconnu")
		return -1

	elif (mesure == None):
		return -2

	elif (mesure > recup_borne("MAX", "max_{0}".format(type_mesure))):
		curseur_mesures.execute("""
			INSERT INTO meteor_donnees
			(date_mesure, max_{0})
			VALUES (datetime("now", "localtime"), {1})
		""".format(type_mesure, mesure))
		bdd_mesures.commit()
		return 0

	elif (mesure < recup_borne("MIN", "min_{0}".format(type_mesure))):
		curseur_mesures.execute("""
			INSERT INTO meteor_donnees
			(date_mesure, min_{0})
			VALUES (datetime("now", "localtime"), {1})
		""".format(type_mesure, mesure))
		bdd_mesures.commit()
		return 0

"""
@brief	Récupère la moyenne des mesure de température et d'humidite de l'heure
		précédente dans la base de données des mesures, et l'enregistre dans
		la base de données des moyennes
"""
def enregistrer_moyennes():
	# Récupère la moyenne de l'heure passée
	curseur_mesures.execute("""
		SELECT AVG(temperature_ambiante), AVG(humidite_ambiante)
		FROM meteor_donnees
		WHERE date_mesure >= datetime("now", "localtime", "-1 hour", "1 minute")
		AND temperature_ambiante IS NOT NULL
		AND humidite_ambiante IS NOT NULL
	""")
	moyenne_mesures = curseur_mesures.fetchall()[0]
	temperature = moyenne_mesures[0]
	humidite = moyenne_mesures[1]

	# Vérification que les données existent, dans le cas d'un changement de
	# fuseau été/hiver, puis ajoute dans la base de données des moyennes
	if (temperature != None and humidite != None):
		curseur_moyennes.execute("""
			INSERT INTO meteor_graphs
			(date_mesure, temperature_ambiante, humidite_ambiante)
			VALUES (datetime("now", "localtime"), {0}, {1})
		""".format(round(temperature / 1, 1), round(humidite / 1, 1)))
		bdd_moyennes.commit()
	return 0

## Gestion des sauvegardes #####################################################
"""
@brief	Supprimer les anciennes sauvegardes datant de plus de 31 jours
"""
def nettoyage_sauvegardes():
	# Récupérez tous les fichiers du répertoire avec leur date de modification
	fichiers = glob.glob(os.path.join(CHEMIN_SAUVEGARDE_LOCAL, '*'))
	dates_fichiers = [
		(fichier, os.path.getmtime(fichier))
		for fichier in fichiers
	]

	# Nombre de jours en secondes
	nombre_jours = NBR_JOURS * 24 * 60 * 60
	date_actuelle = time.time()

	# Parcours les fichiers et supprime ceux datant de plus de 31 jours
	for nom_fichier, date_fichier in dates_fichiers:
		if ((date_actuelle - date_fichier) > nombre_jours):
			os.remove(nom_fichier)
	return 0

"""
@brief	Créé une copie des bases de données de mesures et de moyennes dans le
		dossier de sauvegarde local
@return	0 si la copie s'est bien déroulée, -1 sinon
"""
def copie_sauvegarde_bdd():
	try:
		shutil.copy2("./{0}".format(NOM_BDD_MESURES), "{0}/{1}_{2}".format(
			CHEMIN_SAUVEGARDE_LOCAL,
			time.strftime("%d-%m-%Y"),
			NOM_BDD_MESURES
		))
		shutil.copy2("./{0}".format(NOM_BDD_MOYENNES), "{0}/{1}_{2}".format(
			CHEMIN_SAUVEGARDE_LOCAL,
			time.strftime("%d-%m-%Y"),
			NOM_BDD_MOYENNES
		))
		return 0

	except:
		messageErreur("Copie des bases de données de sauvegarde échouée")
		return -1

"""
@brief	Nettoye les base de données des mesures et des moyennes.
		Ne garde que les mesures de la journée en cours et les mesures minimales
		et maximales de la journée précédente, pour la base de données des
		mesures.
		Pour la base de données des moyennes, ne garde que les 31 derniers jours
@return	0 si le nettoyage s'est bien déroulé, -1 sinon
"""
def nettoyage_bdd():
	# Nettoyage de la base de données des mesures
	curseur_mesures.execute("""
		DELETE FROM meteor_donnees
		WHERE (max_temp, min_temp, max_humi, min_humi) NOT IN (
			SELECT MAX(max_temp), MIN(min_temp), MAX(max_humi), MIN(min_humi)
			FROM meteor_donnees
		)
		OR (
			temperature_ambiante IS NOT NULL
			AND humidite_ambiante IS NOT NULL
			AND date_mesure NOT IN (
				SELECT MAX(date_mesure)
				FROM meteor_donnees
			)
		)
	""")
	bdd_mesures.commit()

	# Nettoyage de la base de données des moyennes
	curseur_moyennes.execute("""
		DELETE FROM meteor_graphs
		WHERE (
			date_mesure <=
			datetime("now", "localtime", "-{0} days", "-3 minutes")
		)
	""".format(NBR_JOURS))
	bdd_moyennes.commit()
	return 0

## Affichage des mesures #######################################################
"""
@brief	Affiche les mesures de température et d'humidité sur l'écran

@param	temperature	Mesure de température à afficher
@param	humidite	Mesure d'humidité à afficher

@return	0 si l'affichage s'est bien déroulé, -1 sinon
"""
def afficher_mesures(temperature, humidite):
	if (temperature == None or humidite == None):
		return -1

	dessin = pil.ImageDraw.Draw(AFFICHAGE_IMAGE)
	dessin.rectangle(
		(0, 0, AFFICHAGE_LARGEUR, AFFICHAGE_HAUTEUR),
		outline = 0, fill = 0
	)

	dessin.text(
		(AFFICHAGE_ABSCISSE, AFFICHAGE_HAUT),
		"Date : " + str(time.strftime("%d %B")),
		font = POLICE, fill = TRANSPARENT
	)
	dessin.text(
		(AFFICHAGE_ABSCISSE, AFFICHAGE_HAUT + 16),
		"Température : " + str(temperature) + "°C",
		font = POLICE, fill = 255
	)
	dessin.text(
		(AFFICHAGE_ABSCISSE, AFFICHAGE_HAUT + 32),
		"Humidité : " + str(humidite) + "%",
		font = POLICE, fill = TRANSPARENT
	)
	dessin.text(
		(AFFICHAGE_ABSCISSE, AFFICHAGE_HAUT + 48),
		"Dernière mise à jour : ",
		font = POLICE, fill = TRANSPARENT
	)
	dessin.text(
		(AFFICHAGE_ABSCISSE, AFFICHAGE_HAUT + 56),
		str(time.strftime("%H:%M")),
		font = POLICE, fill = TRANSPARENT
	)

	affichage.image(AFFICHAGE_IMAGE)
	affichage.display()
	return 0

## Programme principal #########################################################
# Messages d'information
os.system("clear")

print("{0}|Info| Mode {1}{2}".format(
	couleur.BLEU_CLAIR,
	("connecté" if mode_local == False else "local"),
	couleur.FIN_STYLE
))

print("{0}|Info| Les messages d'erreur s'afficheront dans cette console{1}\n"
	.format(couleur.BLEU_FONCE, couleur.FIN_STYLE)
)

# Attente de la mise en route des services réseaux de l'OS
time.sleep(5)

connexion_sftp()
while True:
	# Calcul du temps de départ
	temps_arrivee = dt.datetime.utcnow() + dt.timedelta(minutes = 3)
	temps_arrivee = temps_arrivee.replace(second = 0, microsecond = 0)
	if (temps_arrivee.minute > 0 and temps_arrivee.minute < 3):
		temps_arrivee = temps_arrivee.replace(minute = 0)

	# Récupère les mesures
	temperature = recup_mesure("temperature")
	humidite = recup_mesure("humidite")

	# Enregistrement de la température et de l'humidité
	enregistrement_mesures(temperature, humidite)

	# Enregistrement des bornes min et max
	enregistrer_borne(temperature, "temp")
	enregistrer_borne(humidite, "humi")

	# Envoi de la base de données des mesures au serveur
	gestion_envoi(NOM_BDD_MESURES)

	# Renvoi la base de données des graphs si cela avait échoué précédemment
	if (status_envoi == False and gestion_envoi(NOM_BDD_MOYENNES) == True):
		status_envoi = True

	# Calcul et enregistrement des moyennes
	maintenant = dt.datetime.utcnow()
	if (maintenant.hour == temps_moyenne.hour):
		# Calcul l'heure pour la prochaine moyenne
		temps_moyenne = dt.datetime.utcnow() + dt.timedelta(hours = 1)

		# Enregistrement de la moyenne pour température et humidité, puis envoi
		enregistrer_moyennes()
		status_envoi = gestion_envoi(NOM_BDD_MOYENNES)

		# Nettoyage des bases de données une fois par jour
		# Vérifie que l'heure est bien minuit dans le fuseau local français
		if (
			(time.localtime().tm_isdst == 1 and maintenant.hour == 22) or
			(time.localtime().tm_isdst == 0 and maintenant.hour == 23)
		):
			copie_sauvegarde_bdd()
			nettoyage_sauvegardes()
			nettoyage_bdd()

	# Affichage des informations sur l'écran
	afficher_mesures(temperature, humidite)

	# Attente pour la mesure suivante
	duree_attente = (temps_arrivee - dt.datetime.utcnow()).total_seconds()
	if (duree_attente > 0):
		time.sleep(duree_attente)