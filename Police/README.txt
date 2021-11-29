Placer la police dans le dossier :
/usr/local/share/fonts

Lancer les commandes :
sudo fc-cache -fv (=> sudo apt install fontconfig si commande introuvable)
rm -fr /root/.cache/matplotlib (=> print(matplotlib.get_cachedir()) en python pour savoir le bon chemin)
