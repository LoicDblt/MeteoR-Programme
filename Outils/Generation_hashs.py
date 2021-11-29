#!/usr/bin/python3
#Author: DIEBOLT Loïc

##########################################################
##                 Génération de hashs                  ##
##########################################################

## Import
from hashlib import sha256

## Fonction
def hashing(mot_de_passe):
	hashing = sha256(str(mot_de_passe).encode("utf-8")).hexdigest()
	return hashing

## Programme
hasher = input("Entréee à hasher : ")
print(hashing(hasher))