from flask import Flask, render_template, request, redirect, url_for, session, make_response, send_file, jsonify
from datetime import datetime, timedelta, date, timezone
import psycopg2
import psycopg2.extras
import calendar
import csv
import io
import pdfkit
import os
import requests
import json
import re
import pytz
from ldap3 import Server, Connection, SIMPLE, SYNC, ASYNC, SUBTREE, ALL
from decimal import Decimal







app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretKey'
app.config['LDAP_HOST'] = '10.1.84.55'
app.config['LDAP_PORT'] = 389  # Default LDAP port
app.config['LDAP_BASE_DN'] = 'ou=users,dc=axione,dc=fr'  # Base DN for user search
app.config['LDAP_USER_DN'] = 'cn=%s,ou=users,dc=axione,dc=fr'  # User DN pattern
app.config['LDAP_USER_RDN_ATTR'] = 'cn'  # Attribute to identify users
app.config['LDAP_USER_LOGIN_ATTR'] = 'cn'  # Attribute to use for user login
app.config['LDAP_BIND_USER_DN'] = 'cn=app-ldap,ou=applications,ou=users,dc=axione,dc=fr'  # Admin user DN
app.config['LDAP_BIND_USER_PASSWORD'] = 'ldap'  # Admin user password
app.config['LDAP_GROUP_DN'] = 'cn=Administrateur,ou=roles,ou=astreintemco,ou=applications,dc=axione,dc=fr'





#Détails de la base de données
db_host="localhost"
db_port="5432"
db_name="gae"
db_user="postgres"
db_password="aequo3AVoo4y"

def get_db_connection():
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    return conn

#Page principale du site sur laquel on se login
@app.route('/')
def pageLogin():
    return render_template('connexion.html')

#Référence dans le connexion.html
@app.route('/login', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        #identifiant utilisateur
        admin = request.form['admin']
        #mot de passe
        mdp = request.form['mdp']

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


        cursor.execute("""
        UPDATE "login"
        SET admin = %s, "mdp" = %s
        WHERE "id" = %s
        """, (admin, mdp, 2))
        conn.commit()

        #Une ligne de login contient l'id et le mdp de l'admin, l'autre ligne contient ce qu'a tapé l'utilisateur pour se connecter
        #id pour se connecter : laurent.lataste
        #mdp pour se connecter : mdpAdmin
        cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
        vrai = cursor.fetchone()
        cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
        faux = cursor.fetchone()

        cursor.close()
        conn.close()

        #Vérification si c'est bien l'admin qui essaie de se connecter
        if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
            return redirect(url_for('home'))
        else:
            return render_template('connexion.html')

#Référence dans le base.html
@app.route('/deco', methods=['GET', 'POST'])
def deco():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("""
    UPDATE "login"
    SET admin = %s, "mdp" = %s
    WHERE "id" = %s
    """, ('aleatoire', 'aleatoire', 2))
    conn.commit()

         

    cursor.close()
    conn.close()

    return render_template('connexion.html')


#Référence dans le base.html
@app.route('/home')
def home():
    return render_template('home.html')

#Ref dans le tickets.html
@app.route('/ticket/appel', methods=['GET', 'POST'])
def appel():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()

    #  Current time UTC
    now_utc = datetime.now(timezone.utc)

    # Convert the UTC time to Paris time
    paris_timezone = pytz.timezone('Europe/Paris')
    now_paris = now_utc.astimezone(paris_timezone)

    now = now_paris
    current_hour = now_paris.hour
    formatted_date2 = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    current_datetime = datetime.utcnow()
    formatted_date = current_datetime.strftime('%d-%m-%Y')  # Format to 'd-m-Y'
    cursor.execute("SELECT * FROM \"calendrier\" WHERE \"date\" = %s", (formatted_date,))
    calendrier = cursor.fetchone()
    cursor.execute("SELECT * FROM \"Ferie\" ORDER BY id")
    joursFerie = cursor.fetchall()
    #jours feriés
    jourCommeDimanche = False

    for jour in joursFerie:
        if jour['date'] == formatted_date:
            jourCommeDimanche = True

    if not calendrier:
        # Handle the case where no records were found for the given date
        # You may raise an exception, return an error message, or handle it as needed.
        return jsonify({"error": "No records found for the given date"})

    personne1_id = calendrier['personne1']
    personne2_id = calendrier['personne2']
    personne3_id = calendrier['personne3']
    personne4_id = calendrier['personne4']


    cursor.execute("SELECT * FROM \"User\" WHERE \"id\" = %s", (personne1_id,))
    personne1 = cursor.fetchone()

    cursor.execute("SELECT * FROM \"User\" WHERE \"id\" = %s", (personne2_id,))
    personne2 = cursor.fetchone()

    cursor.execute("SELECT * FROM \"User\" WHERE \"id\" = %s", (personne3_id,))
    personne3 = cursor.fetchone()

    cursor.execute("SELECT * FROM \"User\" WHERE \"id\" = %s", (personne4_id,))
    personne4 = cursor.fetchone()

    if 14 <= current_hour <= 18 and not(jourCommeDimanche) and not (est_weekend(formatted_date)):
        data = {
            "items": [
                {
                    "ressource": personne4['nom'] + " " + personne4['prenom'],
                    "date_debut": formatted_date2,
                    "numero_phone": personne4['numeroPhone'],
                    "numero_gsm": personne4['numeroGsm'],
                    "email": personne4['email']
                }
            ]
        }
    elif  8 <= current_hour <= 12 and not(jourCommeDimanche) and not (est_weekend(formatted_date)):
        data = {
            "items": [
                {
                    "ressource": personne3['nom'] + " " + personne3['prenom'],
                    "date_debut": formatted_date2,
                    "numero_phone": personne3['numeroPhone'],
                    "numero_gsm": personne3['numeroGsm'],
                    "email": personne3['email']
                }
            ]
        }
    else:
    # Create the data for the single row in calendrier
        data = {
            "items": [
                {
                    "type_astreinte": "Titulaire",
                    "ressource": personne1['nom'] + " " + personne1['prenom'],
                    "date_debut": formatted_date2,
                    "numero_phone": personne1['numeroPhone'],
                    "numero_gsm": personne1['numeroGsm'],
                    "email": personne1['email']
                },
                {
                    "type_astreinte": "Backup",
                    "ressource": personne2['nom'] + " " + personne2['prenom'],
                    "date_debut": formatted_date2,
                    "numero_phone": personne2['numeroPhone'],
                    "numero_gsm": personne2['numeroGsm'],
                    "email": personne2['email']
                }
            ]
        }

    # Make sure to close the cursor and connection after use.
    cursor.close()
    conn.close()

    # Renvoyer les données au format JSON
    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
            return jsonify(data)
    else:
        return render_template('connexion.html')
    

def verifierHNO(heure1, heure2):
    heureDebut = heure1.split(':')
    heureFin = heure2.split(':')
    debut_minutes = int(heureDebut[0]) * 60 + int(heureDebut[1])
    fin_minutes = int(heureFin[0]) * 60 + int(heureFin[1])
    if (debut_minutes >= 0 and debut_minutes <= 8*60) or (fin_minutes >= 0 and fin_minutes <= 8*60):
        return True
    elif (debut_minutes >= 18*60 and debut_minutes <= 24*60) or (fin_minutes >= 18*60 and fin_minutes <= 24*60):
        return True
    else:
        return False
        


@app.route('/update_event', methods=['GET', 'POST'])
def edit_event():
    if request.method == 'POST':
        date = request.form['date']
        prenom1 = request.form['prenom1']
        prenom2 = request.form['prenom2']
        prenom3 = request.form['prenom3']
        prenom4 = request.form['prenom4']


        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
        vrai = cursor.fetchone()
        cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
        faux = cursor.fetchone()

        cursor.execute("""
        UPDATE "calendrier"
        SET personne1 = %s, "personne2" = %s, personne3 = %s, personne4 = %s
        WHERE "date" = %s
        """, (prenom1, prenom2, prenom3, prenom4, date))
        conn.commit()

        cursor.close()
        conn.close()

    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
            return redirect(url_for('calendrier'))
    else:
        return render_template('connexion.html')
    

@app.route("/renderCsv/")
def generate_csv():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()

    cursor.execute("SELECT \"id\", \"prenom\", \"nom\", \"statut\", \"mensuelBrut\", \"tauxHoraire\" FROM \"User\"")
    users = cursor.fetchall()

    headers = ["id","Prénom", "Nom", "Statut", "Mensuel Brut", "Taux Horaire", "Libellé Mail", "Numéro Ticket", "Date d'Intervention", "Heure Début", "Heure Fin", "Temps d'Intervention"]
    current_date = datetime.now().strftime("%d-%m-%Y")
    filename = request.args.get('filename', f"result_{current_date}.csv")

    csv_data = io.StringIO()
    writer = csv.writer(csv_data, delimiter=',')
    writer.writerow(headers)

    for user in users:
        cursor.execute("SELECT \"libelleMail\", \"numeroTicket\", \"dateIntervention\", \"heureDebut\", \"heureFin\", \"tempsIntervention\" FROM \"Ticket\" WHERE \"idUser\" = %s ORDER BY \"numeroTicket\"", (user['id'],))
        tickets = cursor.fetchall()

        for ticket in tickets:
            ticket_row = [*user, *ticket]
            writer.writerow(ticket_row)

        cursor.execute("SELECT \"tempsIntervention\", \"total\" FROM \"User\" WHERE \"id\" = %s", (user['id'],))
        final = cursor.fetchall()

        totaux_row1 = ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]
        totaux_row1[-2] = "Temps total d'intervention"
        totaux_row1[-1] = "Total Paie"
        writer.writerow(totaux_row1)

        totaux_row2 = ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]
        totaux_row2[-2] = final[0][0]
        totaux_row2[-1] = final[0][1]
        writer.writerow(totaux_row2)

    cursor.close()
    conn.close()

    return send_file(
        io.BytesIO(csv_data.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename  # Set the download name
    )

    

def convert_date_format(date_str):
    # Convertir la chaîne en objet de date
    date_obj = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')

    # Formater la date dans le format souhaité 'jj-mm-aaaa'
    formatted_date = date_obj.strftime('%d-%m-%Y')
    return formatted_date

def is_within_one_hour(date_str1, date_str2):
    date_format = "%Y-%m-%d %H:%M:%S"
    date1 = datetime.strptime(date_str1, date_format)
    date2 = datetime.strptime(date_str2, date_format)
    time_difference = abs(date1 - date2)
    one_hour = timedelta(hours=1)
    return time_difference < one_hour


@app.route('/search_tickets', methods=['GET', 'POST'])
def search_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    number1 = 1

    cursor.execute("DELETE FROM \"Ticket\" WHERE verif is null")    
    conn.commit()

    var = 'b21hci5iZW56ZXJvdWFsOmFlcXVvM0FWb280eV8='  # Base64 encoded username:password
    url = 'https://rt-wrapper.axione.fr/v2/tickets/search'
    url2 = 'https://rt-wrapper.axione.fr/tickets/'
    headers = {'Authorization': f'Basic {var}', "Content-type": "application/json"}
    
    if request.method == 'POST':
        dateDeb = request.form['start_date']
        dateFn = request.form['end_date']
        start_date = datetime.strptime(dateDeb, '%d-%m-%Y').strftime('%Y-%m-%d')
        end_date = datetime.strptime(dateFn, '%d-%m-%Y').strftime('%Y-%m-%d')


    # Récupérez les paramètres de recherche à partir du corps de la requête
    search_params = {
        "search_format": "i",
        "queue": "SI",
        "custom_fields": {
            "CF.{equipe}": "MCO",
            "CF.{Criticite}": "majeur"
        },
        "created__gt": start_date,
        "created__lt": end_date
    }

    
    

    try:
        # Effectuez la requête POST à l'API de l'entreprise avec les paramètres de recherche
        response = requests.post(url, json=search_params, headers=headers)
        
        json_dicti = response.json()
        ma_liste=[]
        json_dicti3 = []  

        for ticket in json_dicti:
            if type(ticket) == dict:
                numericalId = ticket.get('id')

                search_params3 = {
                    "id": numericalId,
                    "custom_fields": {
                        "CF.{Alarme Prometheus}": {
                            "$ne": None  # Rechercher les entités avec une valeur non nulle pour le champ "Alarme Prometheus"
                        }
                    }
                }

                response3 = requests.get(url2 + numericalId, json=search_params3, headers=headers)
                data_from_response3 = response3.json()
                json_dicti3.append(data_from_response3)



        # Vérifiez le statut de la réponse
        if response.status_code == 201:
            ticket_created_dates = {}
            cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
            vrai = cursor.fetchone()
            cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
            faux = cursor.fetchone()
            cursor.execute("SELECT * FROM \"User\" ORDER BY id")
            users = cursor.fetchall()    

            

            # Si la requête a réussi, renvoyez les données de la réponse en tant que JSON
            for ticket in json_dicti3:
                if type(ticket) == dict:
                    ma_liste.append(ticket.get('numerical_id'))
                    numericalId = ticket.get('numerical_id')
                    


                    search_params2 = {
                        "id": numericalId
                    }

                    if numericalId is not None:
                        response2 = requests.get(url2 + numericalId + '/history', json=search_params2, headers=headers)
                        data = response2.json()
                    
                    created_values_given_taken = []
                    content = ""
                    retenueStatut = 0


                    for entry in data:
                        if isinstance(entry, dict):
                            if (('Given' in entry.get('description', '') or 'Taken' in entry.get('description', '') or 'Donné' in entry.get('description', '') or 'donné' in entry.get('description', '')) and not ( 'Alarme' in entry.get('description', '') or 'Alarm' in entry.get('description', '') or 'alarm' in entry.get('description', '') or 'alarme' in entry.get('description', '') ) and (retenueStatut < 1)):
                                created_values_given_taken.append(entry['created'])
                                retenueStatut = 1
                            if (('Status' in entry.get('description', '') or 'Statut' in entry.get('description', '')) and (retenueStatut == 1) and not ( 'Alarme' in entry.get('description', '') or 'Alarm' in entry.get('description', '') or 'alarm' in entry.get('description', '') or 'alarme' in entry.get('description', ''))):
                                retenueStatut = 2
                                created_values_given_taken.append(entry['created'])
                            if 'Subject' in entry.get('field', ''):
                                content = entry.get('new_value')
                            if 'created' in entry.get('description', '') and (retenueStatut != 1):
                                creationDate = entry.get('created')
                            if ('Given to' in entry.get('description', '') ):
                                retenueStatut = 1
                                name_given = entry.get('creator')
                            if ('Taken by' in entry.get('description', '') ):
                                retenueStatut = 1
                                name_given = entry.get('creator')
                            if ('Donné à' in entry.get('description', '') ):
                                retenueStatut = 1
                                name_given = entry.get('creator')
                            if ('Pris par' in entry.get('description', '') ):
                                retenueStatut = 1
                                name_given = entry.get('creator')






                    if creationDate is not None:
                        if name_given != 'RT_System':
                            ticket_created_dates[numericalId] = {
                                'Dates Changements': created_values_given_taken,
                                'Contenu': content,
                                'CreationDate': creationDate,
                                'personne': name_given
                            }
                    
        
            for key, value in ticket_created_dates.items():
                utilisateur = value.get('personne')

                if utilisateur == 'interne-kse':
                    user = 1
                elif utilisateur == 'alban.lamberty':
                    user = 2
                elif utilisateur == 'adrien.pupier':
                    user = 3
                elif utilisateur == 'geoffrey.novais':
                    user = 4
                elif utilisateur == 'tristan.jadas':
                    user = 5
                elif utilisateur == 'josue.balma':
                    user = 6

                date_changements = value.get("Dates Changements")
                date_time_str = value.get("CreationDate")
                input_format = '%Y-%m-%d %H:%M:%S'
                output_format = '%H:%M'
                
                if len(date_changements) == 2:
                    if is_within_one_hour(date_time_str, date_changements[0]):
                        date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
                        formatted_date = date_time_obj.strftime("%d-%m-%Y")
                        input_datetime = datetime.strptime(date_changements[0], input_format)
                        heure1 = input_datetime.strftime(output_format)
                        input_datetime = datetime.strptime(date_changements[1], input_format)
                        heure2 = input_datetime.strftime(output_format)
                        if verifierHNO(heure1, heure2):                        
                            cursor.execute("INSERT INTO \"Ticket\" (\"libelleMail\", \"numeroTicket\", \"dateIntervention\", \"heureDebut\", \"heureFin\", \"idUser\") VALUES (%s, %s, %s, %s, %s, %s)",
                                   (value.get("Contenu"), key, formatted_date, heure1, heure2, user))
                            conn.commit()  
        
            cursor.execute("SELECT * FROM \"User\"")
            users = cursor.fetchall()


            for user in users:

                cursor.execute("SELECT \"heureDebut\", \"heureFin\", \"dateIntervention\", \"tempsIntervention\" FROM \"Ticket\" WHERE \"idUser\" = %s ORDER BY \"numeroTicket\"", (user['id'],))
                tickets = cursor.fetchall()

                total_earnings = 0
                tempsInterventionTotal = 0

                for ticket in tickets:
                    heure_debut = ticket['heureDebut']
                    heure_fin = ticket['heureFin']
                    dateIntervention = ticket['dateIntervention']
                    tempsInterventionPartiel = ticket['tempsIntervention']
                    earnings = calculate_earnings(heure_debut, heure_fin, float(user['tauxHoraire']), dateIntervention)
                    total_earnings += earnings
                    if tempsInterventionPartiel is not None:
                        tempsInterventionTotal += tempsInterventionPartiel



                # Arrondir les gains totaux à deux décimales
                total_earnings = round(total_earnings, 2)
                tempsInterventionTotal = round(tempsInterventionTotal, 2)

                # Mettre à jour la base de données avec les gains totaux
                cursor.execute("""
                    UPDATE \"User\"
                    SET total = %s, "tempsIntervention" = %s
                    WHERE id = %s
                    """, (total_earnings, tempsInterventionTotal, user['id']))
                conn.commit()
            

            cursor.close()
            conn.close()
                    

            if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
                return render_template('users2.html', users=users)
            else:
                return render_template('connexion.html')
            
            

                
        else:
            return jsonify({'message': 'Erreur lors de la requête à l\'API'}), response.status_code
        
    except requests.exceptions.RequestException as e:
        return jsonify({'message': 'bigerreur à l\'API'}), 500



@app.route('/users', methods=['GET', 'POST'])
def users():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()
    cursor.execute("SELECT * FROM \"User\" ORDER BY id")
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
        return render_template('users.html', users=users)
    else:
        return render_template('connexion.html')

@app.route('/modif', methods=['GET', 'POST'])
def modif():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()
    cursor.execute("SELECT * FROM \"User\" ORDER BY id")
    users = cursor.fetchall()        
    cursor.close()
    conn.close()
    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
        return render_template('modif.html', users=users)
    else:
        return render_template('connexion.html')


@app.route('/calendrier', methods=['GET', 'POST'])
def calendrier():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()
    cursor.execute("SELECT * FROM calendrier ORDER BY id")
    calendrier = cursor.fetchall()
    cursor.execute("SELECT * FROM \"User\" ORDER BY id")
    users = cursor.fetchall()
    dates = []

    events = []
    for event_info in calendrier:
        date_str = event_info['date']
        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
        formatted_date = date_obj.strftime("%Y-%m-%d")

        event1 = {
            'title1': event_info['personne1'],
            'start': formatted_date,
            'title2': event_info['personne2'],
            'title3': event_info['personne3'],
            'title4': event_info['personne4']
        }

        events.append(event1)

    nouvel_evenement = None
    if request.method == 'POST':
        # Récupérer les valeurs soumises dans le formulaire
        date = request.form['date']
        prenom1 = request.form['prenom1']
        prenom2 = request.form['prenom2']
        prenom3 = request.form['prenom3']
        prenom4 = request.form['prenom4']

        # Créer un dictionnaire pour les nouveaux événements
        nouvel_evenement1 = {
            'date': date,
            'personne1': prenom1,
        }
        nouvel_evenement2 = {
            'date': date,
            'personne2': prenom2
        }
        nouvel_evenement3 = {
            'date': date,
            'personne3': prenom3
        }
        nouvel_evenement4 = {
            'date': date,
            'personne3': prenom4
        }

        # Ajouter les nouveaux événements à la liste des événements
        events.append(nouvel_evenement1)
        events.append(nouvel_evenement2)
        events.append(nouvel_evenement3)
        events.append(nouvel_evenement4)


    converted_calendrier = []

    # Convert dates in calendrier to 'Y-m-d' format
    for entry in calendrier:
        parsed_date = datetime.strptime(entry['date'], '%d-%m-%Y')
        formatted_date = parsed_date.strftime('%Y-%m-%d')

        # Create a new dictionary with the converted date and other values
        converted_entry = {
            'date': formatted_date,
            'personne1': entry['personne1'],
            'personne2': entry['personne2'],
            'personne3': entry['personne3'],
            'personne4': entry['personne4']
        }

        # Add the converted entry to the new list
        converted_calendrier.append(converted_entry)

    cursor.close()
    conn.close()

    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
        return render_template('calendrier.html', events=events, users=users, nouvel_evenement=nouvel_evenement, calendrier=converted_calendrier)
    else:
        return render_template('connexion.html')    
    


@app.route('/ajouter_evenement', methods=['POST'])
def ajouter_evenement():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()

    # Récupérer les valeurs soumises dans le formulaire
    date_str = request.form['date']
    prenom1 = request.form['prenom1']
    prenom2 = request.form['prenom2']
    prenom3 = request.form['prenom3']
    prenom4 = request.form['prenom4']

    # Convertir la chaîne de date en objet de date
    date_obj = datetime.strptime(date_str, "%d-%m-%Y")

    # Déterminer le jour de la semaine de la date d'origine
    jour_semaine_origine = date_obj.weekday()

    # Calculer la différence entre le jour de la semaine d'origine (lundi) et le jour spécifié
    difference_jours = jour_semaine_origine - 0  # 0 correspond au lundi

    # Ajouter la différence de jours à la date d'origine
    date_debut_semaine = date_obj - timedelta(days=difference_jours)

    # Itérer sur les 7 jours de la semaine
    for i in range(7):
        # Ajouter i jours à la date de début de semaine
        current_date = date_debut_semaine + timedelta(days=i)

        # Convertir la date en format "d-m-Y" pour l'ajout
        formatted_date = current_date.strftime("%d-%m-%Y")

        # Insérer l'événement dans la table "calendrier"
        cursor.execute("INSERT INTO calendrier (date, personne1, personne2, personne3, personne4) VALUES (%s, %s, %s, %s, %s)",
                       (formatted_date, prenom1, prenom2, prenom3, prenom4))

    conn.commit()
    cursor.close()
    conn.close()

    # Rediriger vers la page du calendrier
    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
        return redirect('/calendrier')
    else:
        return render_template('connexion.html')    
    
@app.route('/ajoutTicket/<int:user_id>', methods=['GET', 'POST'])
def addTicket(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()

    libelle_mail = request.form['libelleMail']
    numero_ticket = request.form['numeroTicket']
    date_intervention = request.form['dateIntervention']
    heure_debut = request.form['heureDebut']
    heure_fin = request.form['heureFin']

    cursor.execute("INSERT INTO \"Ticket\" (\"libelleMail\", \"numeroTicket\", \"dateIntervention\", \"heureDebut\", \"heureFin\", \"idUser\", \"verif\") VALUES (%s, %s, %s, %s, %s, %s, %s)",
    (libelle_mail, numero_ticket, date_intervention, heure_debut, heure_fin, user_id, 1))
    conn.commit()



    cursor.execute("SELECT * FROM \"Ticket\" WHERE \"idUser\" = %s ORDER BY \"numeroTicket\"", (user_id,))
    tickets = cursor.fetchall()

    cursor.close()
    conn.close()

    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
        return redirect(url_for('tickets', user_id=user_id))
    else:
        return render_template('connexion.html')    
    

@app.route('/suppTicket/<int:ticket_id>/<int:user_id>', methods=['GET', 'POST'])
def supprimerTicket(ticket_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()

    cursor.execute("DELETE FROM \"Ticket\" WHERE \"id\" = %s", (ticket_id,))
    conn.commit()
    
    cursor.execute("SELECT * FROM \"Ticket\" WHERE \"idUser\" = %s ORDER BY \"numeroTicket\"", (user_id,))
    tickets = cursor.fetchall()

    cursor.close()
    conn.close()
    
    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
        return render_template('tickets.html', tickets=tickets, user_id=user_id)
    else:
        return render_template('connexion.html')   
    

@app.route('/tickets/<int:user_id>', methods=['GET', 'POST'])
def tickets(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()
    cursor.execute("SELECT * FROM \"Ticket\" WHERE \"idUser\" = %s ORDER BY \"numeroTicket\"", (user_id,))
    tickets = cursor.fetchall()

    for ticket in tickets:
        datee = ticket['dateIntervention']

        heureDebut = ticket['heureDebut']
        heureFin = ticket['heureFin']
        tempsTotal = calculate_time(heureDebut, heureFin, datee)

        cursor.execute("""
        UPDATE "Ticket"
        SET "heureDebut" = %s, "heureFin" = %s, "tempsIntervention" = %s
        WHERE "id" = %s
        """, (heureDebut, heureFin, tempsTotal, ticket['id']))
        conn.commit()
        

    cursor.execute("SELECT * FROM \"Ticket\" WHERE \"idUser\" = %s ORDER BY \"numeroTicket\"", (user_id,))
    tickets = cursor.fetchall()

    cursor.close()
    conn.close()

    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
        return render_template('tickets.html', tickets=tickets, user_id=user_id)
    else:
        return render_template('connexion.html')   
    

def est_weekend(date):
    # Convert the date string to a datetime object
    date = datetime.strptime(date, "%d-%m-%Y")

    # The method weekday() returns a number between 0 (Monday) and 6 (Sunday)
    return (date.weekday() == 6 or date.weekday() == 5)

def est_dimanche(date):
    # Convert the date string to a datetime object
    date = datetime.strptime(date, "%d-%m-%Y")

    # The method weekday() returns a number between 0 (Monday) and 6 (Sunday)
    return date.weekday() == 6

def calculate_time(heureDebut, heureFin, dateIntervention):
    heureDebut = heureDebut.split(':')
    heureFin = heureFin.split(':')

    debut_minutes = int(heureDebut[0]) * 60 + int(heureDebut[1])
    fin_minutes = int(heureFin[0]) * 60 + int(heureFin[1])

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"Ferie\" ORDER BY id")
    joursFerie = cursor.fetchall()
    jourCommeDimanche = False

    for jour in joursFerie:
        if jour['date'] == dateIntervention:
            jourCommeDimanche = True
    
    tempsTotal = 0
        
    if est_dimanche(dateIntervention) or jourCommeDimanche:
        if debut_minutes < fin_minutes and debut_minutes >= (6*60) and debut_minutes <= (21*60) and ((fin_minutes - debut_minutes) <= 15):
            tempsTotal = (15)  * 2
        elif debut_minutes < fin_minutes and debut_minutes >= (0) and debut_minutes <= (6*60) and ((fin_minutes - debut_minutes) <= 15):
            tempsTotal = (15) * 2 + 0.1 * (15)
        elif debut_minutes < fin_minutes and debut_minutes >= (21*60) and debut_minutes <= (24*60) and ((fin_minutes - debut_minutes) <= 15):
            tempsTotal = (15) * 2 + 0.1 * (15)
        elif debut_minutes > fin_minutes and (((fin_minutes) + (24*60 - debut_minutes)) <= 15):
            tempsTotal = (15) * 2 + 0.1 * (15)
        elif debut_minutes >= (6 * 60) and fin_minutes <= (21 * 60) and fin_minutes > debut_minutes:
            tempsTotal = (fin_minutes - debut_minutes) * 2
        elif debut_minutes >= (21 * 60) and (fin_minutes <= (6 * 60)) and fin_minutes < debut_minutes:
            tempsTotal = ((24 * 60 - debut_minutes) * 2 + (fin_minutes) * 2) + 0.1 * (fin_minutes) + (0.1 * (24 * 60 - debut_minutes))
        elif debut_minutes >= (21 * 60) and (fin_minutes <= (24 * 60)) and fin_minutes > debut_minutes:
            tempsTotal = ((fin_minutes - debut_minutes)) * 2 + 0.1 * ((fin_minutes - debut_minutes))
        elif debut_minutes <= (6 * 60) and (fin_minutes <= (6 * 60)) and fin_minutes > debut_minutes:
            tempsTotal = ((fin_minutes - debut_minutes)) * 2 + 0.1 * ((fin_minutes - debut_minutes))
        elif debut_minutes <= (21 * 60) and debut_minutes >= (6 * 60) and fin_minutes >= (21 * 60) and fin_minutes <= (24 * 60):
            tempsTotal = ((21*60 - debut_minutes)) * 2 + ((fin_minutes - 21*60)) * 2 + 0.1 * ((fin_minutes - 21*60))
        elif debut_minutes <= (21 * 60) and debut_minutes >= (6 * 60) and fin_minutes >= (0) and fin_minutes <= (6*60):
            tempsTotal = ((21*60 - debut_minutes)) * 2 + 3 * 60 * 2 + 0.1 * 3 * 60 + ((fin_minutes)) * 2 + 0.1 * ((fin_minutes))
        elif debut_minutes >= (21*60) and debut_minutes <= (24*60) and fin_minutes >= (6*60) and fin_minutes <= (21*60):
            tempsTotal = ((24*60 - debut_minutes)) * 2 + 0.1 * ((24*60 - debut_minutes)) + (6 * 60 * 2) + 0.1 * 6 * 60 + ((fin_minutes - 6*60))  * 2
        elif debut_minutes >= (0) and debut_minutes <= (6*60) and fin_minutes >= (6*60) and fin_minutes <= (21*60):
            tempsTotal = ((6*60 - debut_minutes)) * 2 + 0.1 * ((6*60 - debut_minutes)) + ((fin_minutes - 6*60)) * 2
    else:
        if debut_minutes < fin_minutes and debut_minutes >= (6*60) and debut_minutes <= (21*60) and ((fin_minutes - debut_minutes) <= 15):
            tempsTotal = (15)
        elif debut_minutes < fin_minutes and debut_minutes >= (0) and debut_minutes <= (6*60) and ((fin_minutes - debut_minutes) <= 15):
            tempsTotal = (15) * 2
        elif debut_minutes < fin_minutes and debut_minutes >= (21*60) and debut_minutes <= (24*60) and ((fin_minutes - debut_minutes) <= 15):
            tempsTotal = (15) * 2
        elif debut_minutes > fin_minutes and (((fin_minutes) + (24*60 - debut_minutes)) <= 15):
            tempsTotal = (15) * 2
        elif debut_minutes >= (6 * 60) and fin_minutes <= (21 * 60) and fin_minutes > debut_minutes:
            tempsTotal = ((fin_minutes - debut_minutes))
        elif debut_minutes >= (21 * 60) and (fin_minutes <= (6 * 60)) and fin_minutes < debut_minutes:
            tempsTotal = ((24 * 60 - debut_minutes)) * 2 + (fin_minutes) * 2
        elif debut_minutes >= (21 * 60) and (fin_minutes <= (24 * 60)) and fin_minutes > debut_minutes:
            tempsTotal = ((fin_minutes - debut_minutes)) * 2
        elif debut_minutes <= (6 * 60) and (fin_minutes <= (6 * 60)) and fin_minutes > debut_minutes:
            tempsTotal = ((fin_minutes - debut_minutes)) * 2
        elif debut_minutes <= (21 * 60) and debut_minutes >= (6 * 60) and fin_minutes >= (21 * 60) and fin_minutes <= (24 * 60):
            tempsTotal = ((21*60 - debut_minutes)) + ((fin_minutes - 21*60)) * 2
        elif debut_minutes <= (21 * 60) and debut_minutes >= (6 * 60) and fin_minutes >= (0) and fin_minutes <= (6*60):
            tempsTotal = ((21*60 - debut_minutes)) + 3 * 60 * 2 + ((fin_minutes)) * 2
        elif debut_minutes >= (21*60) and debut_minutes <= (24*60) and fin_minutes >= (6*60) and fin_minutes <= (21*60):
            tempsTotal = ((24*60 - debut_minutes)) * 2 + (6 * 60 * 2) + ((fin_minutes - 6*60))
        elif debut_minutes >= (0) and debut_minutes <= (6*60) and fin_minutes >= (6*60) and fin_minutes <= (21*60):
            tempsTotal = ((6*60 - debut_minutes)) * 2 + ((fin_minutes - 6*60))
    
    cursor.close()
    conn.close()

    return tempsTotal

    


def calculate_earnings(heureDebut, heureFin, tauxHoraire, dateIntervention):
    heureDebut = heureDebut.split(':')
    heureFin = heureFin.split(':')

    
    debut_minutes = int(heureDebut[0]) * 60 + int(heureDebut[1])
    fin_minutes = int(heureFin[0]) * 60 + int(heureFin[1])

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"Ferie\" ORDER BY id")
    joursFerie = cursor.fetchall()
    jourCommeDimanche = False

    for jour in joursFerie:
        if jour['date'] == dateIntervention:
            jourCommeDimanche = True
    
    gains = 0

    
    if est_dimanche(dateIntervention) or jourCommeDimanche:
        if debut_minutes < fin_minutes and debut_minutes >= (6*60) and debut_minutes <= (22*60) and ((fin_minutes - debut_minutes) <= 15):
            gains = (15 / 60) * tauxHoraire * 2
        elif debut_minutes < fin_minutes and debut_minutes >= (0) and debut_minutes <= (6*60) and ((fin_minutes - debut_minutes) <= 15):
            gains = (15 / 60) * tauxHoraire * 2 + 0.1 * (15 / 60) * tauxHoraire
        elif debut_minutes < fin_minutes and debut_minutes >= (22*60) and debut_minutes <= (24*60) and ((fin_minutes - debut_minutes) <= 15):
            gains = (15 / 60) * tauxHoraire * 2 + 0.1 * (15 / 60) * tauxHoraire
        elif debut_minutes > fin_minutes and (((fin_minutes) + (24*60 - debut_minutes)) <= 15):
            gains = (15 / 60) * tauxHoraire * 2 + 0.1 * (15 / 60) * tauxHoraire
        elif debut_minutes >= (6 * 60) and fin_minutes <= (22 * 60) and fin_minutes > debut_minutes:
            gains = ((fin_minutes - debut_minutes) / 60) * tauxHoraire * 2
        elif debut_minutes >= (22 * 60) and (fin_minutes <= (6 * 60)) and fin_minutes < debut_minutes:
            gains = (((24 * 60 - debut_minutes) / 60) * tauxHoraire * 2 + (fin_minutes / 60) * tauxHoraire * 2) + (0.1 * (fin_minutes / 60) * tauxHoraire) + (0.1 * ((24 * 60 - debut_minutes) / 60) * tauxHoraire)
        elif debut_minutes >= (22 * 60) and (fin_minutes <= (24 * 60)) and fin_minutes > debut_minutes:
            gains = ((fin_minutes - debut_minutes) / 60) * tauxHoraire * 2 + 0.1 * ((fin_minutes - debut_minutes) / 60) * tauxHoraire
        elif debut_minutes <= (6 * 60) and (fin_minutes <= (6 * 60)) and fin_minutes > debut_minutes:
            gains = ((fin_minutes - debut_minutes) / 60) * tauxHoraire * 2 + 0.1 * ((fin_minutes - debut_minutes) / 60) * tauxHoraire
        elif debut_minutes <= (22 * 60) and debut_minutes >= (6 * 60) and fin_minutes >= (22 * 60) and fin_minutes <= (24 * 60):
            gains = ((22*60 - debut_minutes)/60) * tauxHoraire * 2 + ((fin_minutes - 22*60)/60) * tauxHoraire * 2 + 0.1 * ((fin_minutes - 22*60)/60) * tauxHoraire
        elif debut_minutes <= (22 * 60) and debut_minutes >= (6 * 60) and fin_minutes >= (0) and fin_minutes <= (6*60):
            gains = ((22*60 - debut_minutes)/60) * tauxHoraire * 2 + 2 * tauxHoraire * 2 + 0.1 * 2 * tauxHoraire + ((fin_minutes)/60) * tauxHoraire * 2 + 0.1 * ((fin_minutes)/60) * tauxHoraire
        elif debut_minutes >= (22*60) and debut_minutes <= (24*60) and fin_minutes >= (6*60) and fin_minutes <= (22*60):
            gains = ((24*60 - debut_minutes)/60) * tauxHoraire * 2 + 0.1 * ((24*60 - debut_minutes)/60) * tauxHoraire + (6 * tauxHoraire * 2) + 0.1 * 6 * tauxHoraire + ((fin_minutes - 6*60)/60) * tauxHoraire * 2
        elif debut_minutes >= (0) and debut_minutes <= (6*60) and fin_minutes >= (6*60) and fin_minutes <= (22*60):
            gains = ((6*60 - debut_minutes)/60) * tauxHoraire * 2 + 0.1 * ((6*60 - debut_minutes)/60) * tauxHoraire + ((fin_minutes - 6*60) /60) * tauxHoraire * 2
    else:
        if debut_minutes < fin_minutes and debut_minutes >= (6*60) and debut_minutes <= (22*60) and ((fin_minutes - debut_minutes) <= 15):
            gains = (15 / 60) * tauxHoraire
        elif debut_minutes < fin_minutes and debut_minutes >= (0) and debut_minutes <= (6*60) and ((fin_minutes - debut_minutes) <= 15):
            gains = (15 / 60) * tauxHoraire * 2
        elif debut_minutes < fin_minutes and debut_minutes >= (22*60) and debut_minutes <= (24*60) and ((fin_minutes - debut_minutes) <= 15):
            gains = (15 / 60) * tauxHoraire * 2
        elif debut_minutes > fin_minutes and (((fin_minutes) + (24*60 - debut_minutes)) <= 15):
            gains = (15 / 60) * tauxHoraire * 2
        elif debut_minutes >= (6 * 60) and fin_minutes <= (22 * 60) and fin_minutes > debut_minutes:
            gains = ((fin_minutes - debut_minutes) / 60) * tauxHoraire
        elif debut_minutes >= (22 * 60) and (fin_minutes <= (6 * 60)) and fin_minutes < debut_minutes:
            gains = ((24 * 60 - debut_minutes) / 60) * tauxHoraire * 2 + (fin_minutes / 60) * tauxHoraire * 2
        elif debut_minutes >= (22 * 60) and (fin_minutes <= (24 * 60)) and fin_minutes > debut_minutes:
            gains = ((fin_minutes - debut_minutes) / 60) * tauxHoraire * 2
        elif debut_minutes <= (6 * 60) and (fin_minutes <= (6 * 60)) and fin_minutes > debut_minutes:
            gains = ((fin_minutes - debut_minutes) / 60) * tauxHoraire * 2
        elif debut_minutes <= (22 * 60) and debut_minutes >= (6 * 60) and fin_minutes >= (22 * 60) and fin_minutes <= (24 * 60):
            gains = ((22*60 - debut_minutes)/60) * tauxHoraire + ((fin_minutes - 22*60)/60) * tauxHoraire * 2
        elif debut_minutes <= (22 * 60) and debut_minutes >= (6 * 60) and fin_minutes >= (0) and fin_minutes <= (6*60):
            gains = ((22*60 - debut_minutes)/60) * tauxHoraire + 2 * tauxHoraire * 2 + ((fin_minutes)/60) * tauxHoraire * 2
        elif debut_minutes >= (22*60) and debut_minutes <= (24*60) and fin_minutes >= (6*60) and fin_minutes <= (22*60):
            gains = ((24*60 - debut_minutes)/60) * tauxHoraire * 2 + (6 * tauxHoraire * 2) + ((fin_minutes - 6*60)/60) * tauxHoraire
        elif debut_minutes >= (0) and debut_minutes <= (6*60) and fin_minutes >= (6*60) and fin_minutes <= (22*60):
            gains = ((6*60 - debut_minutes)/60) * tauxHoraire * 2 + ((fin_minutes - 6*60) /60) * tauxHoraire
    
    cursor.close()
    conn.close()
    return gains


@app.route('/editTicket/<int:idTicket>/<int:idUser>', methods=['POST'])
def editTicket(idTicket, idUser):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()
    
    cursor.execute("SELECT \"dateIntervention\" FROM \"Ticket\" WHERE \"id\" = %s", (idTicket,))
    dateIntervention = cursor.fetchall()
    if dateIntervention:
        datee = dateIntervention[0][0]

    

    
    heureDebut = request.form['heureDebut']
    heureFin = request.form['heureFin']
    tempsTotal = calculate_time(heureDebut, heureFin, datee)
    statut = request.form['statut']

    cursor.execute("""
        UPDATE "Ticket"
        SET statut = %s, "heureDebut" = %s, "heureFin" = %s, "tempsIntervention" = %s
        WHERE "id" = %s
    """, (statut, heureDebut, heureFin, tempsTotal, idTicket))
    conn.commit()

    cursor.close()
    conn.close()

    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
        return redirect(url_for('tickets', user_id=idUser))
    else:
        return render_template('connexion.html')
    
@app.route('/edit_modif/<int:user_id>', methods=['POST'])
def edit_modif(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (4497,))
    vrai = cursor.fetchone()
    cursor.execute("SELECT * FROM \"login\" WHERE \"id\" = %s", (2,))
    faux = cursor.fetchone()

    email = request.form['email']
    nom = request.form['nom']
    prenom = request.form['prenom']
    tel = request.form['tel']
    statut = request.form['statut']
    mensuel_brut = request.form['mensuel_brut']

    # Update the user's data in the database
    cursor.execute("""
        UPDATE "User"
        SET "statut" = %s, "mensuelBrut" = %s, "email" = %s, "nom" = %s, "prenom" = %s, "numeroGsm" = %s
        WHERE id = %s
    """, (statut, mensuel_brut, email, nom, prenom, tel, user_id))
    conn.commit()


    # Update the corresponding tickets with the new tauxHoraire
    taux_horaire = round(float(mensuel_brut) / 151.67, 2)
    cursor.execute("""
        UPDATE \"User\"
        SET "tauxHoraire" = %s
        WHERE id = %s
    """, (taux_horaire, user_id))
    conn.commit()

    cursor.execute("SELECT \"heureDebut\", \"heureFin\", \"dateIntervention\", \"tempsIntervention\" FROM \"Ticket\" WHERE \"idUser\" = %s ORDER BY \"numeroTicket\"", (user_id,))
    tickets = cursor.fetchall()

    total_earnings = 0
    tempsInterventionTotal = 0

    for ticket in tickets:
        heure_debut = ticket['heureDebut']
        heure_fin = ticket['heureFin']
        dateIntervention = ticket['dateIntervention']
        tempsInterventionPartiel = ticket['tempsIntervention']
        earnings = calculate_earnings(heure_debut, heure_fin, taux_horaire, dateIntervention)
        total_earnings += earnings
        if tempsInterventionPartiel is not None:
            tempsInterventionTotal += tempsInterventionPartiel



    # Arrondir les gains totaux à deux décimales
    total_earnings = round(total_earnings, 2)
    tempsInterventionTotal = round(tempsInterventionTotal, 2)

    # Mettre à jour la base de données avec les gains totaux
    cursor.execute("""
        UPDATE \"User\"
        SET total = %s, "tempsIntervention" = %s
        WHERE id = %s
    """, (total_earnings, tempsInterventionTotal, user_id))
    conn.commit()

    cursor.close()
    conn.close()

    if (vrai['admin'] == faux['admin']) and (vrai['mdp'] == faux['mdp']):
        return redirect('/modif')  # Redirect to the list of users after modification
    else:
        return render_template('connexion.html')

@app.route('/edit_user/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    statut = request.form['statut']
    mensuel_brut = request.form['mensuel_brut']

    # Update the user's data in the database
    cursor.execute("""
        UPDATE "User"
        SET "statut" = %s, "mensuelBrut" = %s
        WHERE id = %s
    """, (statut, mensuel_brut, user_id))
    conn.commit()


    # Update the corresponding tickets with the new tauxHoraire
    taux_horaire = round(float(mensuel_brut) / 151.67, 2)
    cursor.execute("""
        UPDATE \"User\"
        SET "tauxHoraire" = %s
        WHERE id = %s
    """, (taux_horaire, user_id))
    conn.commit()

    cursor.execute("SELECT \"heureDebut\", \"heureFin\", \"dateIntervention\", \"tempsIntervention\" FROM \"Ticket\" WHERE \"idUser\" = %s ORDER BY \"numeroTicket\"", (user_id,))
    tickets = cursor.fetchall()

    total_earnings = 0
    tempsInterventionTotal = 0

    for ticket in tickets:
        heure_debut = ticket['heureDebut']
        heure_fin = ticket['heureFin']
        dateIntervention = ticket['dateIntervention']
        tempsInterventionPartiel = ticket['tempsIntervention']
        earnings = calculate_earnings(heure_debut, heure_fin, taux_horaire, dateIntervention)
        total_earnings += earnings
        if tempsInterventionPartiel is not None:
            tempsInterventionTotal += tempsInterventionPartiel



    # Arrondir les gains totaux à deux décimales
    total_earnings = round(total_earnings, 2)
    tempsInterventionTotal = round(tempsInterventionTotal, 2)

    # Mettre à jour la base de données avec les gains totaux
    cursor.execute("""
        UPDATE \"User\"
        SET total = %s, "tempsIntervention" = %s
        WHERE id = %s
    """, (total_earnings, tempsInterventionTotal, user_id))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/users')  # Redirect to the list of users after modification


    


if __name__ == '__main__':
    app.run(debug=True)
