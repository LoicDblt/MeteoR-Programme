#! /bin/bash
# Auteur : DIEBOLT Loïc

readonly CHEMIN_LOCAL="/dossier/emplacement/programme"
readonly CHEMIN_SERVEUR="/racine/serveur"
readonly ADRESSE_SFTP="sftp.serveur.com"
readonly UTILISATEUR_SFTP="nom_utilisateur_SFTP"
readonly CHEMIN_CLE_SSH="/dossier/emplacement/clé_ssh_privée"

# Usage : python3 meteor.py <Adresse SFTP> <Chemin racine sur le serveur>
#		  <Identifiant SFTP> <Clé SSH privée>
screen -dmS meteor
screen -S meteor -p 0 -X stuff "cd $CHEMIN_LOCAL && \
python3 meteor.py \
$ADRESSE_SFTP \
$CHEMIN_SERVEUR \
$UTILISATEUR_SFTP \
$CHEMIN_CLE_SSH \n"

# Usage : python3 homeBridge_Si7021.py
screen -dmS homebridge
screen -S homebridge -p 0 -X stuff "cd $CHEMIN_LOCAL && \
python3 homeBridge_Si7021.py \n"