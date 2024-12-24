import requests
from bs4 import BeautifulSoup
from telegram import Bot
import time
import json
import os
import asyncio

username = '' ## Username UniCaen
password = '' ## Mot de passe CAS
telegram_bot_token = "" ## Token de BOT Télégram
chat_id = '' ## Chat à ID à récupérer via l'API (https://api.telegram.org/bot[telegram_bot_token]/getUpdates)

#Aucune protection anti-bot merci l'univ <3

#Récupère le JSON de webnotes en se connectant au CAS de l'univ (récupération du cookie de session)

def get_data(username:str, password:str)->'json':
    Rexv = requests.get('https://cas.unicaen.fr/login?service=https%3A%2F%2Fwebnotes.unicaen.fr%2Fservices%2FdoAuth.php%3Fhref%3Dhttps%253A%252F%252Fwebnotes.unicaen.fr%252F')
    exv = BeautifulSoup(Rexv.text, 'html.parser')
    ExecutionValue = exv.find('input', {'name': 'execution'}).get('value')
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

# Trie le json brut renvoyé par webnotes en récupérant les notes de chaque ressource et SAE.
# {"Ressource":[[evaluation, note],[evaluation, note]], "SAE":[[evaluation, note],[evaluation, note]]}

def sort_data(data: dict) -> dict:
    notes = {}
    for ressources in data['relevé']['ressources']:
        notes[ressources] = []
        for evaluations in data['relevé']['ressources'][ressources]['evaluations']:
            notes[ressources].append([evaluations['description'], evaluations['note']['value']])
    for saes in data['relevé']['saes']:
        notes[saes] = []
        for evaluations in data['relevé']['saes'][saes]['evaluations']:
            notes[saes].append([evaluations['description'], evaluations['note']['value']])
    return notes

# Compare les nouvelles notes avec les anciennes et renvoie :
#  - Rien si rien n'à changé ou si une note à été supprimé.
#  - [ressource, [evaluation, note]] si une nouvelle note est présente ou si une note à été modifié.

def compare_data(current_data) -> dict:
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

async def notification(note: list):
    if note is not None:
        bot = Bot(token=telegram_bot_token)
        await bot.send_message(chat_id=chat_id, text=f'Nouvelle note : {note[0]}\n{note[1][0]} = {note[1][1]}')
        return
    else:
        return

async def main():
    bot = Bot(token=telegram_bot_token)
    await bot.send_message(chat_id=chat_id, text="Le script a démarré.")
    x = 0
    with open("data.json", "w"):
        pass
    while True:
        try:
            await notification(compare_data(sort_data(get_data(username, password))))
        except Exception as e:
            print(f"Erreur lors de l'envoi de la notification : {e}")
        print(x)
        x += 1
        time.sleep(120)

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Erreur dans le script principal : {e}")
            time.sleep(10)  # Attendre 10 secondes avant de redémarrer
