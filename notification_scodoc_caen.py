import requests
from bs4 import BeautifulSoup
from pushbullet import Pushbullet
import time
import json
import os

"""username = os.getenv("SCODOC_USER")
password = os.getenv("SCODOC_PASS")
token = os.getenv("SCODOC_TOKEN")"""

username = ''
password = ''
token = ""

#Aucune protection anti-bot merci l'univ <3

#Récupère le JSON de webnotes en se connectant au CAS de l'univ (récupération du cookie de session)
def get_data(username:str, password:str)->'json':
    #Récupération de l'execution value.
    Rexv = requests.get('https://cas.unicaen.fr/login?service=https%3A%2F%2Fwebnotes.unicaen.fr%2Fservices%2FdoAuth.php%3Fhref%3Dhttps%253A%252F%252Fwebnotes.unicaen.fr%252F')
    exv = BeautifulSoup(Rexv.text, 'html.parser')
    ExecutionValue = exv.find('input', {'name': 'execution'}).get('value')
    #Création de la session pour l'authentification au CAS.
    Auth = requests.session()
    data = {
        'username': username,
        'password': password,
        'execution': ExecutionValue,
        '_eventId': 'submit',
        'geolocation': '',
    }
    response = Auth.post('https://cas.unicaen.fr/login?service=https%3A%2F%2Fwebnotes.unicaen.fr%2Fservices%2FdoAuth.php%3Fhref%3Dhttps%253A%252F%252Fwebnotes.unicaen.fr%252F', data=data)
    params = {
        'q': 'dataPremièreConnexion',
    }
    response = Auth.post('https://webnotes.unicaen.fr/services/data.php', params=params)
    data = response.json()
    return(data)

#Trie le json brut renvoyé par webnotes en récupérant les notes de chaque ressource et SAE.
#{"Ressource":[[evaluation, note],[evaluation, note]], "SAE":[[evaluation, note],[evaluation, note]]}
def sort_data(data)->dict:
    notes = {}
    for ressources in data['relevé']['ressources']:
        notes[ressources] = []
        for evaluations in data['relevé']['ressources'][ressources]['evaluations']:
            notes[ressources].append([evaluations['description'], evaluations['note']['value']])
            pass
    for saes in data['relevé']['saes']:
        notes[saes] = []
        for evaluations in data['relevé']['saes'][saes]['evaluations']:
            notes[saes].append([evaluations['description'], evaluations['note']['value']])
            pass
    return notes

#Compare les nouvelles notes avec les anciennes et renvoie :
# Rien si rien n'à changé ou si une note à été supprimé.
# [ressource, [evaluation, note]] si une nouvelle note est présente ou si une note à été modifié.
def compare_data(current_data)->dict:
    with open('data.json', 'r') as file:
        try:
            previous_data = json.loads(file.read().encode('utf-8'))
        except:
            previous_data = None
    with open('data.json', 'w') as file:
        file.write(json.dumps(current_data, sort_keys=True, indent=4))

    if previous_data == None:
        previous_data = current_data
    if previous_data == current_data:
        return None
    else:
        for ressources in current_data:
            for notes in current_data[ressources]:
                if notes not in previous_data[ressources]:
                    return [ressources, notes]

def notification(note:list):
    if note != None:
        Pushbullet(token).push_note(f'Nouvelle note : {note[0]}',f'{note[1][0]} = {note[1][1]}')
        return
    else:
        return

if __name__ == "__main__":
    x=0
    with open("data.json","w"):
        pass
    while True:
        notification((compare_data(sort_data(get_data(username, password)))))
        print(x)
        x+=1
        time.sleep(120)
    
    
