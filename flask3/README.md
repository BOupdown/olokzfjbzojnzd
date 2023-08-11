
# T-manager 2023

L'application T-manager permet de faire des requêtes sur l'API RT Wrapper, récupérer les tickets en astreinte et les stocker dans la base de données de l'application. Elle permet aussi de créer des ticket dans cette base données qui ne seront pas supprimés ni réinitialisé tant que l'utilisateur ne le désire pas. 

L'application fait touner différentes fonctions qui permettent de calculer les temps d'intervention et les revenus sur ces temps d'intervention.



## Le langage utilisé

L'application a été entièrement codée en python à l'aide du framework Flask. 

La base de données est en Postgres et pgAdmin a été utilisé pour créer les tables et différentes colonnes de cette base de données.

L'API est RT Wrapper.

## Update des tickets des collaborateurs

L'application sera accessible pour l'instant à l'aide d'un seul identifiant

    id = laurent.lataste 
    mdp = mdpAdmin


Vous serez accueili dans la page Home où vous aurez accès à différents onglets. Dans Collaborateurs, vous aurez accès aux différents collaborateurs avec différentes données importantes. Pour effectuer une requête à l'API et mettre à jour ces données il faut mettre un intervalle de temps et lancer le Search en haut à gauche. Ceci fait, il faudra cliquer sur les boutons 'tiquets' et ensuite revenir et mettre à jour avec le bouton 'mise à jour'. Ceci demande quelques améliorations, ce n'est pas encore automatisé parfaitement.

En cliquant sur Tickets vous pourrez accéder aux tickets du collaborateur correspondant.

Sur cette même page, il est possible de télécharger le CSV. Attention à bien mettre à jour les tickets avant de faire le téléchargement !


## Calendrier

Le calendrier des astreintes est accessible en cliquant sur l'onglet Calendrier. 

Sur cette page, vous pourrez ajouter et modifer les personnes qui sont astreinte les jour de la semaine.

'Ajouter' ajoute pour chaque jour de la semaine la saisie. 'Modifier' modifie pour chaque jour de la semaine.

Attention à ne pas ajouter en double !
## Profil collaborateurs

Dans cette page, vous pourrez modifier les données des collaborateurs : mail, numéro de téléphone, salaire, nom, prénom et forfait.
## Acknowledgements

 - [fullcalendar](https://fullcalendar.io/docs)
 - [flask](https://flask.palletsprojects.com/en/2.3.x/)
 - [RT Wrapper](https://rt-wrapper.axione.fr/docs#/)
 - [pgAdmin](https://www.pgadmin.org/) 




## Auteur

Omar BENZEROUAL

Avec l'aide de Josué BALMA, Alexis THEALLIER et Laurent LATASTE.