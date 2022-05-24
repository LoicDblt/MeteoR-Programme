# MeteoR - Programme

# **Présentation**
Ce programme, écrit en Python 3, permet au travers d'un Raspberry Pi possédant une sonde Si7021 et un écran SSD1306,
de récupérer la température et l'humidité ambiante d'une pièce. Il va ainsi permettre d'afficher de manière locale sur l'écran les informations actuelles, mais aussi au travers d'un site web en affichant en plus d'informations, telles que l'évolution de la température/humidité dans le temps ou les minimums et maximums respectifs.

Ce programme enregistre donc les données de température et d'hygrométrie, puis chaque heure générera la moyenne des mesures effectuées. Ces données seront enregistrées dans des bases de données, qui seront transmises à un site internet, afin de les afficher par la suite, de manière claire et lisible.

# **Installation**

 # Sondes
 Il est nécessaire d'installer la sonde de température/hygrométrie Si7021, ainsi que l'écran SSD1306.  
 Les schémas d'installations sont trouvables notamment sur le site d'Adafruit.
 
 ## Liens
 https://learn.adafruit.com/adafruit-si7021-temperature-plus-humidity-sensor/assembly  
 https://learn.adafruit.com/monochrome-oled-breakouts/wiring-128x64-oleds
 
 # Dépendances
 
 Il est nécessaire d'installer différents modules en amont du lancement du programme, à savoir :
 * Adafruit_SSD1306
 * adafruit_si7021
 * board
 * paramiko
 
 # Programme
 Une fois le programme récupéré et toutes les étapes précédentes effectuées, il suffit de le lancer avec la commande :
 
 ```python3 MeteoR.py <Adresse SFTP> <Port SFTP> <Chemin du dossier web sur serveur> <Identifiant SFTP> <Mot de passe SFTP>```
 
 Il est recommandé de créer un ```screen``` afin de garder en permanence le programme en fond.  
 Aussi, il est possible de créer un script afin de lancer automatiquement le programme en démarrage du Raspbery Pi. Cela peut être utile afin de garder une grande disponibilité, notamment en cas de coupures de courant.
 
