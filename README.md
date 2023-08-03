# MeteoR - Programme
Ce programme, écrit en Python 3, permet au travers d'un Raspberry Pi
relié à une sonde Si7021 et un écran SSD1306, de récupérer la température et
l'humidité relative d'une pièce.

## **Sommaire**
- [Programme](#meteor---programme)
  - [Présentation](#présentation)
  - [Installation](#installation)
    - [Composants](#composants)
    - [Liens pour l'assemblage](#liens-pour-lassemblage)
    - [Dépendances](#dépendances)
  - [Lancement du programme](#lancement-du-programme)

## **Présentation**
Le programme MeteoR va enregistrer les données de température et d'hygrométrie,
puis chaque heure générera la moyenne des mesures effectuées. Ces données seront
enregistrées dans des bases de données, qui seront transmises à [un site
internet](https://github.com/LoicDblt/MeteoR-Site), afin de les afficher par la
suite.
<br>

Ainsi, on retrouvera un affichage local sur l'écran, avec les informations
actuelles, mais aussi au travers dudit site en proposant davantage
d'informations, telles que l'évolution de la température/humidité dans le temps
ou encore les minimums et maximums respectifs.

## **Installation**
### Composants
Il est nécessaire d'installer la sonde de température/hygrométrie Si7021,
ainsi que l'écran SSD1306.
Les instructions de montage sont trouvables sur le site d'Adafruit (liens
ci-dessous).

### Liens pour l'assemblage
* [Si7021](https://learn.adafruit.com/adafruit-si7021-temperature-plus-humidity-sensor/assembly)
* [SSD1306](https://learn.adafruit.com/monochrome-oled-breakouts/wiring-128x64-oleds)

### Dépendances
Il est nécessaire d'installer différents modules en amont du lancement du
programme.
Soit en utilisant le fichier des dépendances mis à disposition :
```
pip install -r requirements.txt
```
<br>

Soit en installant manuellement chaque module :
* Adafruit_SSD1306
  ```
  python -m pip install --upgrade pip setuptools wheel
  pip install Adafruit-SSD1306
  ```
* adafruit_si7021
  ```
  pip install adafruit-circuitpython-si7021
  ```
* paramiko
  ```
  pip install paramiko
  ```
* Pillow
  ```
  pip install Pillow
  ```
<br>

> **Remarque**  
Il peut être nécessaire de préciser la version de Python en
faisant usage de ```python3``` et ```pip3```.

## **Lancement du programme**
Une fois le programme récupéré et toutes les étapes précédentes effectuées,
il suffit de lancer la commande suivante, en prenant soin de placer la clé SSH
publique, utilisant le chiffrement Ed25519, sur le serveur au préalable :

```shell
python meteor.py <Adresse SFTP> <Port SFTP> <Chemin racine sur le serveur> <Identifiant SFTP> <Clé SSH privée>
```
<br>

> **Remarque**  
Comme précédemment, il peut être nécessaire de préciser la
version de Python en utilisant ```python3```.

> **Mode local**  
Pour lancer le programme sans adjoindre de serveur et donc uniquement obtenir
les informations sur l'écran connecté au Raspberry, il suffit de ne pas
renseigner les différents arguments précédemment indiqués.
<br>

Il est recommandé de créer un ```screen``` afin de garder en permanence le
programme en fond, même lorsque la session SSH est fermée.  
Aussi, il est également possible d'utiliser un script (cf. le fichier
*squelette_lancement.sh*), afin de lancer automatiquement le programme
au démarrage du Raspberry Pi, avec l'aide d'une tâche CRON.