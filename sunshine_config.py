import json
import jsonschema
from jsonschema import validate
import os
import requests
import vdf

# Because the config for sunshine is stored in the user directory by default we need to get that path and set is as a variable
# We could also make this an argument for the folder location of the config file if we want it to be somewhere else for 
# sunshine

user_dir = os.getenv('HOME')

# initialize dictionary for steam games

games = {}

# load in the existing json config for Sunshine Apps

sunshine_apps = json.load(open(f'{user_dir}/.config/sunshine/apps.json'))

# Load in the vdf file from Steam and convert it to a dictionary
# Currently only looking in a single location, and could be expanded to add more Steam Library locations
# Defaulting to Flatpak version of Steam

vdf_load = vdf.load(open(f'{user_dir}/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/libraryfolders.vdf'))
vdf_text = vdf.VDFDict(vdf_load)

# go through the list of AppIds that we get from steam and get the game name from Steam

for app_id in vdf_text['libraryfolders']['0']['apps']:
  r = requests.get(f'https://store.steampowered.com/api/appdetails?appids={app_id}')
  # Only games return a success here, so we can get rid of anything that fails because it's a tool that we don't want
  if r.json()[f'{app_id}']['success']:
    games[f'{app_id}'] = r.json()[f'{app_id}']['data']['name']
    
# Sunshine uses the name as the main element
# We compare the elements that already exist in Sunshine against what we have from Steam
# We do a substring comparison first, to handle manually added games that are similar
# If the names aren't identical, it is updated in Sunshine to match Steam
# We compare the total number of items in our game list and if we reach the end without
# getting a match, we add the game to the bottom of the config

for key in games:
  no_match = 0
  for app in sunshine_apps['apps']:
    if app['name'] in games[key]:
      if app['name'] != games[key]:
        app['name'] = games[key]
        print("game updated",app['name'])
    else:
      no_match = no_match + 1
  if no_match == len(sunshine_apps['apps']):
    print(f"game added {games[key]}")
    sunshine_apps['apps'].append({'name': games[key],
                                  "output": f"sunshine_logs/{games[key]}.txt", 
                                  "cmd": "", 
                                  "image-path": "", 
                                  "detached": [ 
                                     f"flatpak-spawn --host -setsid flatpak run com.valvesoftware.Steam steam://rungameid/{key}"
                                  ]})
# Might be able to make use of `next` to achieve something similar with less work
# next(item for item in sunshine_apps['apps'] if item['name'] == "poop"

# validate json config file before writing

valid_schema = json.load(open(f"{user_dir}/generated_schema.json"))

def validateconfig(jsondata, valid_schema):
  try:
    validate(instance=jsondata, schema=valid_schema)
  except:
    return False
  return True

validjson = validateconfig(sunshine_apps)

if validjson:
  apps_json = open(f"{user_dir}/.config/sunshine/apps.json", "w")
  json.dump(sunshine_apps, apps_json, indent = 6)
  apps_json.close()
else:
  print("config is invalid")
