import requests
from dotenv import load_dotenv
import os

load_dotenv()

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def get_unsplash_image(query):
    access_key = UNSPLASH_ACCESS_KEY
    url = f"https://api.unsplash.com/search/photos?query={query}&client_id={access_key}"
    response = requests.get(url)
    data = response.json()
    print(f"Imagem retornada: {data}")
    if data["results"]:
        return data["results"][0]["urls"]["regular"]
    return "https://picsum.photos/200"
