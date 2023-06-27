#! /usr/bin/python3
# Auteur : DIEBOLT Loïc

################################################################################
#                             MeteoR - HomeBridge                              #
################################################################################

## Initialisation ##############################################################
import adafruit_si7021
import board
import json
import time
import web

# Initialise le capteur
while True:
	try:
		capteur = adafruit_si7021.SI7021(board.I2C())
		break

	except RuntimeError:
		continue

## Classes #####################################################################
# Chaque url va appeler sa classe ("url", "classe")
urls = (
	"/temp", "temp",
	"/humi", "humi"
)

# Classe pour la température
class temp:
	def GET(self):
		temperature = -1
		for i in range(4):
			try:
				temperature = round(capteur.temperature, 1)
				break

			except:
				time.sleep(i)
		return json.dumps(temperature)

# Classe pour l'humidité
class humi:
	def GET(self):
		humidite = -1
		for i in range(4):
			try:
				humidite = round(capteur.relative_humidity, 1)
				break

			except:
				time.sleep(i)
		return json.dumps(humidite)

## Programme principal #########################################################
# Lance le serveur
if __name__ == "__main__":
	app = web.application(urls, globals())
	app.internalerror = web.debugerror
	app.run()