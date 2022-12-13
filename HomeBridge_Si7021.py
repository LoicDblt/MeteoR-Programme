from adafruit_si7021 import SI7021
from board import I2C
import web
from json import dumps

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
		return dumps(round(capteur.temperature, 1))

class humi:
	def GET(self):
		return dumps(round(capteur.relative_humidity, 1))

# Lance le serveur
if __name__ == "__main__":
	app = web.application(urls, globals())
	app.internalerror = web.debugerror
	app.run()