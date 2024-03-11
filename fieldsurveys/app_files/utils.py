import json

import gspread
import requests
import us
import wikipediaapi
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet
from geopy.geocoders import Nominatim

# instantiate a Nominatim geocoder
geolocator = Nominatim(user_agent="temp_shiny_app")


def get_species_image(genus, species, image_number, family=None, order=None):
    """
    Retrieves the image URL for a given species.

    Args:
        genus (str): The genus of the species.
        species (str): The species name.
        image_number (int): The number of the image to retrieve. The first image is 0, the second is 1, etc.

    Returns:
        str: The URL of the species image, or a default image URL if no image is found.
    """
    base_url = "https://api.inaturalist.org/v1/taxa/autocomplete"
    query = (
        order
        if order is not None
        else family if family is not None else f"{genus} {species}"
    )
    params = {
        "q": query,
        "limit": 1,  # Limit to the first result
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["results"] and data["results"][0]["id"]:
            taxon_id = data["results"][0]["id"]
            photo_url = f"https://api.inaturalist.org/v1/taxa/{taxon_id}?locale=en"
            photo_response = requests.get(photo_url)
            if photo_response.status_code == 200:
                photo_data = photo_response.json()
                if (
                    photo_data["results"]
                    and photo_data["results"][0]["taxon_photos"]
                    and len(photo_data["results"][0]["taxon_photos"]) > 1
                ):
                    if (
                        "large_url"
                        in photo_data["results"][0]["taxon_photos"][1]["photo"]
                    ):
                        image_url = photo_data["results"][0]["taxon_photos"][
                            image_number
                        ]["photo"]["large_url"]
                        return image_url

    return "https://i.ibb.co/m6YDp69/sorry.jpg"


# use this if you want to use the openweathermap API
def get_current_temperature(survey_config, latitude, longitude):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": survey_config["openweathermap_api_id"],
        "units": "imperial",  # You can change this to 'metric' for Celcius
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 200:
            temperature = data["main"]["temp"]
            return f"{temperature} °F"
        else:
            print(f"Error: {data['message']}")
            return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def get_summary_for_specimen(genus, species):
    wiki_wiki = wikipediaapi.Wikipedia("Survey App Ecology (merlin@example.com)", "en")
    page_py = wiki_wiki.page(f"{genus} {species}")

    if page_py.exists():
        return page_py.summary
    else:
        return "No notes found"


def fetch_specimen_classification(genus, species, common_name):
    """
    Fetches the classification information for a given specimen based on its genus, species, or common name.

    Args:
        genus (str): The genus of the specimen.
        species (str): The species of the specimen.
        common_name (str): The common name of the specimen.

    Returns:
        dict: A dictionary containing the classification information of the specimen, including the family, order, and class.

    """
    results = {
        "genus": genus if genus else "unknown",
        "species": species if species else "unknown",
        "family": "unknown",
        "order": "unknown",
        "class": "unknown",
    }

    if genus and genus not in ["None", "Unknown", "unknown", "other"]:
        if species and species not in ["None", "Unknown", "unknown", "other"]:
            species_scientific_name = f"{genus} {species}"
            url = f"https://api.inaturalist.org/v1/taxa?q={species_scientific_name}"
        else:
            url = f"https://api.inaturalist.org/v1/taxa?q={genus}"

    elif common_name and common_name.lower() in ["none", "unknown"]:
        return results
    elif "unknown" in common_name.lower():
        common_name = common_name.lower().replace("unknown", "").strip()
        url = f"https://api.inaturalist.org/v1/taxa?q={common_name}"
    else:
        return results

    response = requests.get(url)
    if response.json()["results"][0]:
        data = response.json()["results"][0]
        url1 = f"https://api.inaturalist.org/v1/observations?verifiable=true&taxon_id={data['id']}"

        response = requests.get(url1)
        data = response.json()
        ranks = data["results"][0]["identifications"][0]["taxon"]["ancestors"]

        for rank in ranks:
            if rank["rank"] == "family":
                results["family"] = rank["name"]
            if rank["rank"] == "order":
                results["order"] = rank["name"]
            if rank["rank"] == "class":
                results["class"] = rank["name"]
    return results


# this approach helps get weather without an API key
def get_weather_underground_temperature(latitude, longitude):
    location = geolocator.reverse(latitude + "," + longitude)
    address = location.raw["address"]
    country_code = address.get("country_code", "")
    city = (
        address.get("city", address.get("village", address.get("hamlet", "")))
        .lower()
        .replace(" ", "-")
    )
    if country_code == "us":
        state = us.states.lookup(address.get("state", "")).abbr.lower()
        url = f"https://www.wunderground.com/weather/{country_code}/{state}/{city}"
    else:
        state = address.get("state", "").lower()
        url = f"https://www.wunderground.com/weather/{country_code}/{city}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")

    weather = soup.find(class_="current-temp")
    weather_text = weather.text
    return weather_text


def decrypt_file(encrypted_file_path, key):
    with open(encrypted_file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()

    cipher_suite = Fernet(key)
    decrypted_data = cipher_suite.decrypt(encrypted_data)

    return decrypted_data


def get_sheets(survey_config, keyfile_path):
    google_worksheets = []
    sh = get_workbook(survey_config, keyfile_path)
    for sheet in sh.worksheets():
        google_worksheets.append(sheet.title)
    return google_worksheets


def get_workbook(survey_config, keyfile_path):
    with open(keyfile_path, "r") as file:
        credentials = json.load(file)
    gc = gspread.service_account_from_dict(credentials)
    sh = gc.open(survey_config["google_workbook_name"])
    return sh
