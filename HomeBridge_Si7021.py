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

# Chaque page va appeler sa classe
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
			except OSError:
				sleep(2)
				continue
			except RuntimeError:
				sleep(2)
				continue
		return dumps(temperature)

class humi:
	def GET(self):
		humidite = -1
		for i in range(4):
			try:
				humidite = round(capteur.relative_humidity, 1)
				break
			except OSError:
				sleep(2)
				continue
			except RuntimeError:
				sleep(2)
				continue
		return dumps(humidite)

# Lance le serveur
if __name__ == "__main__":
	app = web.application(urls, globals())
	app.internalerror = web.debugerror
	app.run()