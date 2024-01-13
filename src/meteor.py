#! /usr/bin/python3
# Auteur : DIEBOLT Loïc

################################################################################
#                                    MeteoR                                    #
################################################################################

## Initialisation ##############################################################
import os
import sys

# Couleurs pour les messages affichés à l'utilisateur
class couleur:
	BLEU_CLAIR = "\033[36m"
	BLEU_FONCE = "\033[94m"
	ROUGE = "\033[91m"
	VERT = "\033[32m"
	FIN_STYLE = "\033[0m"

# Vérifie le nombre d'arguments et sélectionne le mode de fonctionnement
# (local ou connecté)
if (len(sys.argv) == 1):
	mode_local = True

elif (len(sys.argv) == 5):
	mode_local = False

else:
	print(
		f"{couleur.ROUGE}|Erreur| Usage : python3 {sys.argv[0]} <Adresse SFTP> "
		"<Chemin racine sur le serveur> <Identifiant SFTP> " +
		f"<Clé SSH privée>{couleur.FIN_STYLE}"
	)
	exit()

# Message d'initialisation
os.system("clear")
print(
	f"{couleur.BLEU_CLAIR}|Info| Initialisation du programme, veuillez " +
	f"patienter...{couleur.FIN_STYLE}"
)

## Import des modules ##########################################################
import adafruit_si7021
import Adafruit_SSD1306
import board
import datetime as dt
import glob
import locale
import paramiko
from PIL import Image, ImageDraw, ImageFont
import shutil
import sqlite3
import time

## Journalisation des erreurs ##################################################
"""
@brief	Enregistre un message dans le fichier de journalisation

@param	message	Le message à enregistrer
"""
def enregistrer_log(message):
	with open(CHEMIN_JOURNAUX, 'a') as file:
		file.write(message + "\n")

"""
@brief	Affiche un message d'erreur dans la console et l'enregistre dans le
		fichier de journalisation

@param	message	Le message d'erreur à afficher
"""
def message_console_log(typeErr, message):
	messageDate = (f"|{typeErr} - {time.strftime('%d/%m')} à " +
		f"{time.strftime('%H:%M')}| {message}")
	enregistrer_log(messageDate)

	# Affiche le message d'erreur dans la console
	if (typeErr == "Erreur"):
		print(f"{couleur.ROUGE}{messageDate}{couleur.FIN_STYLE}")
	else:
		print(f"{couleur.BLEU_CLAIR}{messageDate}{couleur.FIN_STYLE}")

	return

## Variables et initialisation #################################################
# Dossier de sauvegarde des informations
DOSSIER_STOCKAGE = os.path.expanduser('~') + "/MeteoR-Stockage/"

# Chemin et nom du fichier de journalisation
NOM_JOURNAL = ("meteor_" + dt.datetime.now().strftime("%d-%m-%Y_%H-%M-%S") +
	".log")
DOSSIER_JOURNAUX = DOSSIER_STOCKAGE + "journaux/"
CHEMIN_JOURNAUX = DOSSIER_JOURNAUX + NOM_JOURNAL

# Chemins et noms des bases de données
NOM_BDD_MESURES = "mesures.db"
NOM_BDD_MOYENNES = "moyennes.db"

DOSSIER_BDD = DOSSIER_STOCKAGE + "bdd/"
CHEMIN_BDD_MESURES = DOSSIER_BDD + NOM_BDD_MESURES
CHEMIN_BDD_MOYENNES = DOSSIER_BDD + NOM_BDD_MOYENNES

DOSSIER_SAUV = DOSSIER_STOCKAGE + "sauvegardes/"
CHEMIN_SAUV_MESURES = DOSSIER_SAUV + "mesures/"
CHEMIN_SAUV_MOYENNES = DOSSIER_SAUV + "moyennes/"

# Créé les dossiers
## Dossier de sauvegarde des informations
if (os.path.isdir(DOSSIER_STOCKAGE) == False):
	os.mkdir(DOSSIER_STOCKAGE)

## Dossier de journalisation
if (os.path.isdir(DOSSIER_JOURNAUX) == False):
	os.mkdir(DOSSIER_JOURNAUX)

## Dossier de sauvagarde
if (os.path.isdir(DOSSIER_SAUV) == False):
	os.mkdir(DOSSIER_SAUV)

## Dossiers de sauvegarde des BDD de mesures
if (os.path.isdir(CHEMIN_SAUV_MESURES) == False):
	os.mkdir(CHEMIN_SAUV_MESURES)

## Dossiers de sauvegarde des BDD de moyennes
if (os.path.isdir(CHEMIN_SAUV_MOYENNES) == False):
	os.mkdir(CHEMIN_SAUV_MOYENNES)

## Dossier de stockage des BDD
if (os.path.isdir(DOSSIER_BDD) == False):
	os.mkdir(DOSSIER_BDD)

# Formatage de la date et de l'heure
locale.setlocale(locale.LC_ALL, "")

# Status
status_envoi = False
erreur_capteur_affichee = False
erreur_sftp_affichee = False

# Gestion du temps
erreur_sftp = False
heure_moyenne = dt.datetime.utcnow() + dt.timedelta(hours = 1)
NBR_JOURS_MOIS = 31
MOIS_SECONDES = NBR_JOURS_MOIS * 24 * 60 * 60
DELAIS_MESURE = 3

# Mesures de température et d'humidité
temperature = 0
humidite = 0
MARGE_MESURE = 5

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
			message_console_log(
				"Erreur",
				"Initialisation du capteur échouée, " +
				"correction en cours, veuillez patienter..."
			)
			erreur_capteur_affichee = True

## Bases de données ############################################################
# Créé la base de données des mesures, si elle n'existe pas
bdd_mesures = sqlite3.connect(CHEMIN_BDD_MESURES)
curseur_mesures = bdd_mesures.cursor()
curseur_mesures.execute("""
	CREATE TABLE IF NOT EXISTS mesures
	(date CHAR, temp FLOAT, humi FLOAT,
	max_temp FLOAT, min_temp FLOAT, max_humi FLOAT, min_humi FLOAT)
""")
bdd_mesures.commit()

# Initialise les mesures min et max de température et d'humidité, si la base de
# données est vide
curseur_mesures.execute("""
	CREATE TABLE IF NOT EXISTS bornes
	(date CHAR, max_temp FLOAT, min_temp FLOAT, max_humi FLOAT,
	min_humi FLOAT)
""")
bdd_mesures.commit()

curseur_mesures.execute("""SELECT MIN(max_humi) FROM bornes""")
mesure_min = curseur_mesures.fetchall()[0][0]

if (mesure_min == None):
	curseur_mesures.execute("""
		INSERT INTO bornes
		(date, max_temp, min_temp, max_humi, min_humi)
		VALUES (datetime("now", "localtime"), 0, 100, 0, 100)
	""")
	bdd_mesures.commit()

# Créé la base de données des moyennes, si elle n'existe pas
bdd_moyennes = sqlite3.connect(CHEMIN_BDD_MOYENNES,
	detect_types = sqlite3.PARSE_COLNAMES|sqlite3.PARSE_DECLTYPES
)
curseur_moyennes = bdd_moyennes.cursor()
curseur_moyennes.execute("""
	CREATE TABLE IF NOT EXISTS moyennes
	(date CHAR, temp FLOAT, humi FLOAT)
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
AFFICHAGE_IMAGE = Image.new('1', (AFFICHAGE_LARGEUR, AFFICHAGE_HAUTEUR))
POLICE = ImageFont.load_default()
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
			message_console_log("Info", "Connexion par SFTP rétablie")
		return 0

	except paramiko.AuthenticationException:
		if (erreur_sftp_affichee == False):
			erreur_sftp_affichee = True
			message_console_log(
				"Erreur",
				"Identifiant ou mauvaise clé SSH fournie.\n" +
				"Une nouvelle tentative sera effectuée après chaque " +
				"nouvelle mesure.\nVeuillez relancer le programme si " +
				"vous souhaitez modifier les identifiants."
			)
		erreur_sftp = True
		return -1

	except paramiko.ssh_exception.SSHException:
			message_console_log(
				"Erreur",
				"Format de clé SSH non reconnu (chiffrement Ed25519 attendu)" +
				", passage en mode local"
			)
			mode_local = True
			return -2

	except OSError as erreur:
		message_console_log("Erreur", erreur)
		return -3

	except:
		erreur_sftp = True
		message_console_log("Erreur", "Connexion SFTP au serveur échouée")
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
def envoi_bdd(nom_fichier):
	chemin = f"{CHEMIN_DOSSIER_WEB_SERVEUR}/bdd/{nom_fichier}"
	try:
		sftp.put(DOSSIER_BDD + nom_fichier, chemin)
		return 0

	except IOError:
		sftp.mkdir(f"{CHEMIN_DOSSIER_WEB_SERVEUR}/bdd")
		sftp.put(DOSSIER_BDD + nom_fichier, chemin)
		return -1

	except:
		message_console_log("Erreur", "Tentative de reconnexion au serveur")
		deconnexion_sftp()
		connexion_sftp()
		return -2

"""
@brief	Gère l'envoi de la base de données SQLite au serveur.
		En cas, d'erreur de connexion, plusieurs tentatives seront effectuées.

@param	nom_fichier	Le nom du fichier à envoyer

@return	0 si l'envoi a réussi, -1 en cas d'erreur
"""
def gestion_envoi_bdd(nom_fichier):
	if (mode_local == True):
		return

	if (erreur_sftp == False):
		for nbr_essais in range(1, 3):
			try:
				envoi_bdd(nom_fichier)
				return 0

			except:
				time.sleep(5 * nbr_essais)
		message_console_log(
			"Erreur",
			f"Envoi du fichier \"{DOSSIER_BDD + nom_fichier}\" échoué"
		)
		return -1

## Récupération des mesures ####################################################
"""
@brief	Récupère la mesure de température ou d'humidité et vérifie qu'elle n'est
		pas aberrante (un écart de +/- MARGE_MESURE)

@param	type_mesure	Chaîne de caractères indiquant le type de mesure
		("temp" ou "humi")

@return	La mesure récupérée, ou None en cas d'erreur
"""
def recup_mesure(type_mesure):
	if (type_mesure != "temp" and type_mesure != "humi"):
		message_console_log("Erreur", "recup_mesure | Type de mesure inconnu")
		return None

	# Récupération de la mesure (arrondie à une décmiale près)
	mesure = None
	for _ in range(4):
		try:
			if (type_mesure == "temp"):
				mesure = round(capteur.temperature, 1)

			elif (type_mesure == "humi"):
				mesure = round(capteur.relative_humidity, 1)

		except:
			time.sleep(0.1)
			continue

		# Récupère la dernière date et mesure liée
		donnees_prec = curseur_mesures.execute(f"""
			SELECT date, {type_mesure}
			FROM mesures
			ORDER BY date DESC LIMIT 1
		""").fetchall()

		if (len(donnees_prec) > 0):
			donnees_prec = donnees_prec[0]

		else:
			break

		date_prec = dt.datetime.strptime(donnees_prec[0], "%Y-%m-%d %H:%M:%S")
		delta_minutes = (dt.datetime.now() - date_prec).total_seconds() / 60

		# Si la mesure est aberrante, on en refait une
		# Cela n'est effectué que si la mesure précédente date d'il y a
		# moins de 12 minutes
		if (
			delta_minutes < (DELAIS_MESURE * 4) and
			(
				mesure > (donnees_prec[1] + MARGE_MESURE) or
				mesure < (donnees_prec[1] - MARGE_MESURE)
			)
		):
			time.sleep(1)
			continue

		else:
			break

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
		message_console_log("Erreur", "recup_borne | Type d'opération inconnu")
		return -1

	elif (
		type_mesure != "max_temp" and type_mesure != "min_temp" and
		type_mesure != "max_humi" and type_mesure != "min_humi"
	):
		message_console_log("Erreur", "recup_borne | Type de mesure inconnu")
		return -2

	curseur_mesures.execute(f"""
		SELECT {type_operation}({type_mesure})
		FROM bornes
	""")
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
		INSERT INTO mesures
		(date, temp, humi)
		VALUES (datetime("now", "localtime"), ?, ?)
	""", (temperature, humidite))
	bdd_mesures.commit()
	return 0

"""
@brief	Enregistre la mesure minimale et/ou maximale, en fonction de la valeur
		minimale ou maximale stockée dans la base de données

@param	mesure		Mesure à enregistrer
@param	type_mesure	Chaîne de caractères indiquant le type de mesure
					("temp" ou "humi")

@return	0 si la mesure a été enregistrée, -1 en cas d'erreur de type de mesure,
		-2 en cas de mesure nulle
"""
def enregistrer_bornes(mesure, type_mesure):
	if (type_mesure != "temp" and type_mesure != "humi"):
		message_console_log(
			"Erreur",
			"enregistrer_bornes | Type de mesure inconnu"
		)
		return -1

	elif (mesure == None):
		return -2

	if (mesure > recup_borne("MAX", f"max_{type_mesure}")):
		curseur_mesures.execute(f"""
			INSERT INTO bornes
			(date, max_{type_mesure})
			VALUES (datetime("now", "localtime"), ?)
		""", (mesure,))
		bdd_mesures.commit()

	if (mesure < recup_borne("MIN", f"min_{type_mesure}")):
		curseur_mesures.execute(f"""
			INSERT INTO bornes
			(date, min_{type_mesure})
			VALUES (datetime("now", "localtime"), ?)
		""", (mesure,))
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
		SELECT AVG(temp), AVG(humi)
		FROM mesures
		WHERE date >= datetime("now", "localtime", "-1 hour", "1 minute")
		AND temp IS NOT NULL
		AND humi IS NOT NULL
	""")
	moyenne_mesures = curseur_mesures.fetchall()[0]
	temperature = moyenne_mesures[0]
	humidite = moyenne_mesures[1]

	# Vérification que les données existent, dans le cas d'un changement de
	# fuseau été/hiver, puis ajoute dans la base de données des moyennes
	if (temperature != None and humidite != None):
		curseur_moyennes.execute("""
			INSERT INTO moyennes
			(date, temp, humi)
			VALUES (
				datetime("now", "localtime"),
				?,
				?
			)
		""", (round(temperature / 1, 1), round(humidite / 1, 1)))
		bdd_moyennes.commit()
	return 0

## Gestion des sauvegardes #####################################################
"""
@brief	Supprimer les anciennes sauvegardes des bases de données datant de plus
		de 31 jours

@param	chemin_sauv	Dossier où se trouvent les sauvegardes, dans le dossier
					"DOSSIER_SAUV" (ie. "mesures/" ou "moyennes/")

@return	0 si les sauvegardes ont été supprimées, -1 en cas d'erreur
"""
def nettoyage_sauvegardes_bdd(chemin_sauv):
	# Récupérez tous les fichiers du répertoire avec leur date de modification
	try:
		fichiers = glob.glob(
			os.path.join(chemin_sauv, '*')
		)
		dates_fichiers = [
			(fichier, os.path.getmtime(fichier))
			for fichier in fichiers
		]
	except:
		return -1

	# Parcours les fichiers et supprime ceux datant de plus de 31 jours
	date_actuelle = time.time()
	for nom_fichier, date_fichier in dates_fichiers:
		if ((date_actuelle - date_fichier) > MOIS_SECONDES):
			os.remove(nom_fichier)
	return 0

"""
@brief	Créé une copie des bases de données de mesures et de moyennes dans le
		dossier de sauvegarde

@param	chemin_sauv	Dossier où se trouvent les sauvegardes, dans le dossier
					"DOSSIER_SAUV" (ie. "mesures/" ou "moyennes/")
@param	nom_bdd		Nom de la base de données à sauvegarder

@return	0 si la copie s'est bien déroulée, -1 sinon
"""
def copie_sauvegarde_bdd(chemin_sauv, nom_bdd):
	try:
		# Format du type : ../sauvegardes/mesures/01-01-1970_mesures.db
		shutil.copy2(
			f"{DOSSIER_BDD + nom_bdd}",
			f"{chemin_sauv}{time.strftime('%d-%m-%Y')}_" +
			f"{nom_bdd}"
		)
		return 0

	except:
		message_console_log(
			"Erreur",
			f"Sauvegarde de la base de données \"{DOSSIER_BDD + nom_bdd}\" " +
			"échouée"
		)
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
	## Nettoyage des mesures
	curseur_mesures.execute("""
		DELETE FROM mesures
		WHERE date NOT IN (
			SELECT MAX(date)
			FROM mesures
		)
	""")
	bdd_mesures.commit()

	## Nettoyage des bornes
	curseur_mesures.execute("""
		DELETE FROM bornes
		WHERE (max_temp, min_temp, max_humi, min_humi) NOT IN (
			SELECT MAX(max_temp), MIN(min_temp), MAX(max_humi), MIN(min_humi)
			FROM bornes
		)
	""")
	bdd_mesures.commit()

	# Nettoyage de la base de données des moyennes
	curseur_moyennes.execute(f"""
		DELETE FROM moyennes
		WHERE date <= datetime("now", "localtime", "-{NBR_JOURS_MOIS} days")
	""")
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

	dessin = ImageDraw.Draw(AFFICHAGE_IMAGE)
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
status_message = ("connecté" if mode_local == False else "local")

message_console_log("Info", f"Mode {status_message}")
print(
	f"{couleur.BLEU_FONCE}|Info| Les messages d'erreur s'afficheront dans " +
	f"cette console et sont enregistrés dans le fichier \"{CHEMIN_JOURNAUX}\"" +
	f"{couleur.FIN_STYLE}\n"
)

# Attente de la mise en route des services réseaux de l'OS
time.sleep(5)

connexion_sftp()
while True:
	# Calcul de l'heure de départ de la mesure
	heure_arrivee = dt.datetime.utcnow() + dt.timedelta(minutes = DELAIS_MESURE)
	heure_arrivee = heure_arrivee.replace(second = 0, microsecond = 0)
	if (heure_arrivee.minute > 0 and heure_arrivee.minute < DELAIS_MESURE):
		heure_arrivee = heure_arrivee.replace(minute = 0)

	# Récupère les mesures
	temperature = recup_mesure("temp")
	humidite = recup_mesure("humi")

	# Enregistrement de la température et de l'humidité
	enregistrement_mesures(temperature, humidite)

	# Enregistrement des bornes min et max
	enregistrer_bornes(temperature, "temp")
	enregistrer_bornes(humidite, "humi")

	# Envoi de la base de données des mesures au serveur
	gestion_envoi_bdd(NOM_BDD_MESURES)

	# Renvoi la base de données des moyennes si cela avait échoué précédemment
	if (status_envoi == False and gestion_envoi_bdd(NOM_BDD_MOYENNES) == True):
		status_envoi = True

	# Calcul et enregistrement des moyennes
	heure_actuelle = dt.datetime.utcnow()
	if (heure_actuelle.hour == heure_moyenne.hour):
		# Calcul l'heure pour la prochaine moyenne
		heure_moyenne = dt.datetime.utcnow() + dt.timedelta(hours = 1)

		# Enregistrement de la moyenne pour température et humidité, puis envoi
		enregistrer_moyennes()
		status_envoi = gestion_envoi_bdd(NOM_BDD_MOYENNES)

		# Nettoyage des bases de données une fois par jour
		# Vérifie que l'heure est bien minuit dans le fuseau local français
		if (
			(time.localtime().tm_isdst == 1 and heure_actuelle.hour == 22) or
			(time.localtime().tm_isdst == 0 and heure_actuelle.hour == 23)
		):
			# Nettoyage des dossiers de sauvegarde
			nettoyage_sauvegardes_bdd(CHEMIN_SAUV_MESURES)
			nettoyage_sauvegardes_bdd(CHEMIN_SAUV_MOYENNES)

			# Sauvegarde des bases de données
			copie_sauvegarde_bdd(CHEMIN_SAUV_MESURES, NOM_BDD_MESURES)
			copie_sauvegarde_bdd(CHEMIN_SAUV_MOYENNES, NOM_BDD_MOYENNES)

			# Nettoyage des bases de données
			nettoyage_bdd()

	# Affichage des informations sur l'écran
	afficher_mesures(temperature, humidite)

	# Attente pour la mesure suivante
	duree_attente = (heure_arrivee - dt.datetime.utcnow()).total_seconds()
	if (duree_attente > 0):
		time.sleep(duree_attente)