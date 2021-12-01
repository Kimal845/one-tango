import json
import os
import psycopg2
from urllib.parse import urlparse


# file = open('local.json')
# config = json.load(file)
url = os.environ['DATABASE_URL']
# url = 'localhost'
result = urlparse(url)


async def register(full_name, steam_id, steam_url, steam_id64, discord_id, open_profile=True):
    conn = psycopg2.connect(dbname=result.path[1:],
                            user=result.username,
                            password=result.password,
                            host=result.hostname)
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO users (full_name, steam_id, steam_url, open, steam_id64, discord_id) VALUES ('{full_name}', {steam_id}, '{steam_url}', {open_profile}, {steam_id64}, {discord_id});")
    conn.commit()
    cursor.close()
    conn.close()


async def get_steam_id(discord_id):
    conn = psycopg2.connect(dbname=result.path[1:],
                            user=result.username,
                            password=result.password,
                            host=result.hostname)
    cursor = conn.cursor()
    cursor.execute(f"SELECT steam_id FROM users WHERE discord_id='{discord_id}'")
    fetch = cursor.fetchone()
    cursor.close()
    conn.close()
    return fetch

