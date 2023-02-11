#! /usr/bin/python3
# Auteur : DIEBOLT Loïc

from adafruit_si7021 import SI7021
from board import I2C
from json import dumps
from time import sleep
import web

# Initialise le capteur
while True:
	try:
		capteur = SI7021(I2C())
		break
	except RuntimeError:
		continue

# Chaque url va appeler sa classe ("url", "classe")
urls = (
	"/temp", "temp",
	"/humi", "humi"
)

class temp:
	def GET(self):
		temperature = -1
		for i in range(4):
			try:
				temperature = round(capteur.temperature, 1)
				break
			except:
				sleep(i)
		return dumps(temperature)

class humi:
	def GET(self):
		humidite = -1
		for i in range(4):
			try:
				humidite = round(capteur.relative_humidity, 1)
				break
			except:
				sleep(i)
		return dumps(humidite)

# Lance le serveur
if __name__ == "__main__":
	app = web.application(urls, globals())
	app.internalerror = web.debugerror
	app.run()