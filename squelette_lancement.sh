#! /bin/bash
# Auteur : DIEBOLT Loïc

# Usage : python3 meteor.py <Adresse SFTP> <Chemin racine sur le serveur>
#		  <Identifiant SFTP> <Clé SSH privée>
screen -dmS meteor
screen -S meteor -p 0 -X stuff "cd /dossier/local/emplacement/programme && \
python3 meteor.py \
sftp.serveur.com \
/racine/serveur \
nom_utilisateur_SFTP \
/chemin/local/clé_ssh_privée \n"

screen -dmS homebridge
screen -S homebridge -p 0 -X stuff "cd /dossier/local/emplacement/programme && \
python3 homeBridge_Si7021.py \n"