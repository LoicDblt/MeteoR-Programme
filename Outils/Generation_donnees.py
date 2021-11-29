#!/usr/bin/python3
#Author: DIEBOLT Loïc

##########################################################
##               Génération des données                 ##
##########################################################

## Imports
from PIL import Image, ImageDraw, ImageFont

## Variables et constantes
LARGEUR, HAUTEUR = (341, 85) # taille des images (longueur, hauteur)
open_sans = ImageFont.truetype("/usr/local/share/fonts/open-sans-600.ttf", 72)

## Fonction
def valeur_actuelle(nom_fichier, valeur, couleur, type_sonde):
	img = Image.new("RGBA", (LARGEUR, HAUTEUR), (0, 0, 0, 0))
	dessin = ImageDraw.Draw(img)
	largeur, hauteur = open_sans.getsize(valeur)
	if type_sonde == "DS18B20":
		dessin.text(((LARGEUR-largeur)/2, (HAUTEUR-hauteur)/2), valeur + " °C", font = open_sans, fill = couleur)
		img.crop((99, 18, 99+242, 18+73)).save(nom_fichier) # (gauche, haut, gauche+largeur, haut+hauteur)
	else:
		dessin.text(((LARGEUR-largeur)/2, (HAUTEUR-hauteur)/2), valeur +" %", font = open_sans, fill = couleur)
		img.crop((90, 18, 90+242, 18+73)).save(nom_fichier, "WEBP")
	img.close()

## Programme
	# Témpérature
print("-- Température --")
max_t = input("Température maximale : ")
min_t = input("Température minimale : ")
amb_t = input("Température ambiante : ")

	# Humidité
print("\n-- Humidité --")
max_h = input("Humidité maximale : ")
min_h = input("Humidité minimale : ")
amb_h = input("Humidité ambiante : ")

	# Témpérature
valeur_actuelle("max_temp.webp", max_t, "#F9700E", "DS18B20")
valeur_actuelle("min_temp.webp", min_t, "#09A4DD", "DS18B20")
valeur_actuelle("temp_actu.webp", amb_t, "#000000", "DS18B20")


	# Humidité
valeur_actuelle("max_humi.webp", max_h, "#09A4DD", "DHT22")
valeur_actuelle("min_humi.webp", min_h, "#F9700E", "DHT22")
valeur_actuelle("humidite_actu.webp", amb_h, "#000000", "DHT22")