# MeteoR - Programme

## **Présentation**
Ce programme, écrit en Python 3, permet au travers d'un Raspberry Pi
possédant une sonde Si7021 et un écran SSD1306, de récupérer la température et
l'humidité ambiante d'une pièce.

Ce dernier va enregistrer les données de température et d'hygrométrie, puis
chaque heure générera la moyenne des mesures effectuées. Ces données seront
enregistrées dans des bases de données, qui seront transmises à [un site
internet](https://github.com/LoicDblt/MeteoR-Site), afin de les afficher par la
suite.  
Ainsi, on retrouvera un affichage local sur l'écran, avec les informations
actuelles, mais aussi au travers dudit site en proposant davantages
d'informations, telles que l'évolution de la température/humidité dans le temps
ou encore les minimums et maximums respectifs.

## **Installation**
### Sondes
Il est nécessaire d'installer la sonde de température/hygrométrie Si7021,
ainsi que l'écran SSD1306.
Les instructions de montage sont trouvables sur le site d'Adafruit (liens
ci-dessous).

#### Liens pour l'assemblage
* [Si7021](https://learn.adafruit.com/adafruit-si7021-temperature-plus-humidity-sensor/assembly)
* [SSD1306](https://learn.adafruit.com/monochrome-oled-breakouts/wiring-128x64-oleds)

 ---

### Dépendances
Il est nécessaire d'installer différents modules en amont du lancement du
programme.
Soit en utilisant le fichier des dépendances mis à disposition :
* ```pip install -r requirements.txt```

Soit en installant manuellement chaque module :
* Adafruit_SSD1306
  * ```sudo python -m pip install --upgrade pip setuptools wheel```
  * ```sudo pip install Adafruit-SSD1306```
* adafruit_si7021
  * ```sudo pip install adafruit-circuitpython-si7021```
* paramiko
  * ```sudo pip install paramiko```

**Remarque** Il peut être nécessaire de préciser la version de Python en
faisant usage de ```python3``` et ```pip3```.

---

### Programme
Une fois le programme récupéré et toutes les étapes précédentes effectuées,
il suffit de lancer la commande suivante :

```shell
python MeteoR.py <Adresse SFTP> <Port SFTP> <Chemin racine sur le serveur> <Identifiant SFTP> <Mot de passe SFTP>
```

**Remarque** Comme précédemment, il peut être nécessaire de préciser la
version de Python en utilisant ```python3```.

À noter, il est possible de lancer le programme en local uniquement. Il vous
suffit de compléter les champs avec des valeurs quelconques.

Il est recommandé de créer un ```screen``` afin de garder en permanence le
programme en fond, même lorsque la session SSH est fermée.  
Aussi, il est également possible de créer un script afin de lancer
automatiquement le programme au démarrage du Raspberry Pi.

---

### HomeBridge
Pour utiliser le capteur connecté au Raspberry avec HomeKit, il est possible
d'utiliser [HomeBridge](https://github.com/homebridge/homebridge/wiki/Install-Homebridge-on-Raspbian).  
Une fois celui-ci installé, il est nécessaire d'ajouter les plugins
(grâce à l'interface d'administration)
[HomeBridge HTTP Temperature sensor](https://github.com/Supereg/homebridge-http-temperature-sensor#readme)
et [HomeBridge HTTP Humidity sensor](https://github.com/Supereg/homebridge-http-humidity-sensor#readme).

Le programme *HomeBridge_Si7021.py* permet de fournir les données, aux plugins
installés précédemment, sous forme de json.