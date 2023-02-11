#! /bin/bash
# Auteur : DIEBOLT Loïc

# Usage : python3 meteor.py <Adresse SFTP> <Chemin racine sur le serveur>
#			 <Identifiant SFTP> <Mot de passe SFTP>
screen -dmS meteor
screen -S meteor -p 0 -X stuff "cd /dossier/local/emplacement/programme && \
python3 meteor.py \
sftp.serveur.com \
/chemin/racine/serveur \
nom_utilisateur_SFTP \
mot_de_passe_SFTP \n"

screen -dmS homebridge
screen -S homebridge -p 0 -X stuff "cd /dossier/local/emplacement/programme && \
python3 homeBridge_Si7021.py \n"