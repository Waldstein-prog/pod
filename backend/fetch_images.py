"""Eenmalig: download de 57 Palia potato-pod afbeeldingen en schrijf pods.json.

Bron: https://www.paliatracker.com/furniture-tracker/potato-pods
De originele webp-bestanden staan op /items/decor/<bestand>.
"""
import json
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PODS_DIR = os.path.join(HERE, "static", "pods")
PODS_JSON = os.path.join(HERE, "pods.json")
BASE_URL = "https://www.paliatracker.com/items/decor/"

# (naam, categorie, bestand)
PODS = [
    ("George the Fancypod", "Fancypod", "decor-potatopod-47-fancy-rococo.webp"),
    ("Elizabeth the Fancypod", "Fancypod", "decor-potatopod-48-fancy-versailles.webp"),
    ("Darcy the Fancypod", "Fancypod", "decor-potatopod-49-fancy-renaissance.webp"),
    ("Lacey the Fancypod", "Fancypod", "decor-potatopod-50-fancy-doily.webp"),
    ("Dorian the Fancypod", "Fancypod", "decor-potatopod-51-fancy-crystal.webp"),
    ("Rebecca the Fancypod", "Fancypod", "decor-potatopod-52-fancy-amber.webp"),
    ("Charlotte the Fancypod", "Fancypod", "decor-potatopod-53-fancy-macron.webp"),
    ("Basil the Fancypod", "Fancypod", "decor-potatopod-54-fancy-socialite.webp"),
    ("Victor the Fancypod", "Fancypod", "decor-potatopod-55-fancy-jade.webp"),
    ("Danvers the Fancypod", "Fancypod", "decor-potatopod-56-fancy-silver.webp"),
    ("Newton the Smartypod", "Smartypod", "decor-potatopod-38-winter-ruby.webp"),
    ("Volta the Smartypod", "Smartypod", "decor-potatopod-39-winter-shocker.webp"),
    ("Kelvin the Smartypod", "Smartypod", "decor-potatopod-40-winter-icepick.webp"),
    ("Mendella the Smartypod", "Smartypod", "decor-potatopod-41-winter-starroot.webp"),
    ("Oz the Smartypod", "Smartypod", "decor-potatopod-42-winter-emerald.webp"),
    ("Rosalind the Smartypod", "Smartypod", "decor-potatopod-43-winter-icerose.webp"),
    ("Lavo the Smartypod", "Smartypod", "decor-potatopod-44-winter-flametangle.webp"),
    ("Darwin the Smartypod", "Smartypod", "decor-potatopod-45-winter-holidaylights.webp"),
    ("Beatrix the Smartypod", "Smartypod", "decor-potatopod-46-winter-snowshroom.webp"),
    ("Prissy the Shinypod", "Shinypod", "decor-potatopod-28-fancy-shine.webp"),
    ("Cyrus the Shinypod", "Shinypod", "decor-potatopod-29-fancy-citrine.webp"),
    ("Goldie the Shinypod", "Shinypod", "decor-potatopod-30-fancy-golden.webp"),
    ("Maggie the Shinypod", "Shinypod", "decor-potatopod-31-fancy-magicsucculent.webp"),
    ("Eliot the Shinypod", "Shinypod", "decor-potatopod-32-fancy-echo.webp"),
    ("Rainer the Shinypod", "Shinypod", "decor-potatopod-33-fancy-blaster.webp"),
    ("Zenni the Shinypod", "Shinypod", "decor-potatopod-34-fancy-hydroponics.webp"),
    ("Lazlo the Shinypod", "Shinypod", "decor-potatopod-35-fancy-holographic.webp"),
    ("Cappie the Shinypod", "Shinypod", "decor-potatopod-36-fancy-strangeshroom.webp"),
    ("Patch the Shinypod", "Shinypod", "decor-potatopod-37-fancy-pumpkin.webp"),
    ("Leif the Rockerpod", "Rockerpod", "decor-potatopod-01-dark-tree.webp"),
    ("Gerard the Rockerpod", "Rockerpod", "decor-potatopod-02-dark-emo.webp"),
    ("Momo the Rockerpod", "Rockerpod", "decor-potatopod-03-dark-vexy.webp"),
    ("Axel the Rockerpod", "Rockerpod", "decor-potatopod-04-dark-rocker-01.webp"),
    ("Gene the Rockerpod", "Rockerpod", "decor-potatopod-04-dark-rocker-02.webp"),
    ("Hendrix the Rockerpod", "Rockerpod", "decor-potatopod-04-dark-rocker-03.webp"),
    ("Jovi the Rockerpod", "Rockerpod", "decor-potatopod-04-dark-rocker-04.webp"),
    ("Junior the Potato Pod", "Potato Pod", "decor-potatopod-07-normal-seedling.webp"),
    ("Whirly the Potato Pod", "Potato Pod", "decor-potatopod-08-normal-sprout.webp"),
    ("Mo the Potato Pod", "Potato Pod", "decor-potatopod-09-normal-succulent.webp"),
    ("Shaggy the Potato Pod", "Potato Pod", "decor-potatopod-10-normal-glowy-moss.webp"),
    ("Prickly the Potato Pod", "Potato Pod", "decor-potatopod-11-normal-cactus.webp"),
    ("Priscilla the Prettypod", "Prettypod", "decor-potatopod-12-flowering-peony.webp"),
    ("Dorian the Prettypod", "Prettypod", "decor-potatopod-13-flowering-daisy.webp"),
    ("Dandy the Prettypod", "Prettypod", "decor-potatopod-14-flowering-dandelion.webp"),
    ("Cosmo the Prettypod", "Prettypod", "decor-potatopod-15-flowering-cosmos.webp"),
    ("Kelpie the Merpod", "Merpod", "decor-potatopod-16-water-kelp.webp"),
    ("Ariel the Merpod", "Merpod", "decor-potatopod-17-water-jelly.webp"),
    ("Nori the Merpod", "Merpod", "decor-potatopod-18-water-seaweed.webp"),
    ("Jelly the Merpod", "Merpod", "decor-potatopod-19-water-biojelly.webp"),
    ("Ardbert the Bonsai Pod", "Bonsai Pod", "decor-potatopod-20-bonsai-moyogi.webp"),
    ("Ashe the Bonsai Pod", "Bonsai Pod", "decor-potatopod-21-bonsai-chokkan.webp"),
    ("Autumn the Bonsai Pod", "Bonsai Pod", "decor-potatopod-22-bonsai-deciduous.webp"),
    ("Myrtle the Bonsai Pod", "Bonsai Pod", "decor-potatopod-23-bonsai-crape-myrtle.webp"),
    ("Hopper the Mushpod", "Mushpod", "decor-potatopod-24-mushroom-agaric.webp"),
    ("Sunny the Mushpod", "Mushpod", "decor-potatopod-25-mushroom-parasol.webp"),
    ("Bluebell the Mushpod", "Mushpod", "decor-potatopod-26-mushroom-indigo.webp"),
    ("Port the Mushpod", "Mushpod", "decor-potatopod-27-mushroom-portabello.webp"),
]


def write_pods_json():
    data = [{"naam": n, "categorie": c, "image_bestand": f} for n, c, f in PODS]
    with open(PODS_JSON, "w") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(f"pods.json geschreven: {len(data)} pods")


def download_images():
    os.makedirs(PODS_DIR, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (pod-shop fetch)"}
    ok, skip, fail = 0, 0, 0
    for _, _, bestand in PODS:
        dest = os.path.join(PODS_DIR, bestand)
        if os.path.exists(dest):
            skip += 1
            continue
        url = BASE_URL + bestand
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            with open(dest, "wb") as fh:
                fh.write(r.content)
            ok += 1
            print(f"  ok   {bestand}")
            time.sleep(0.2)
        except Exception as e:
            fail += 1
            print(f"  FAIL {bestand}: {e}", file=sys.stderr)
    print(f"Afbeeldingen: {ok} gedownload, {skip} bestond al, {fail} mislukt")
    return fail == 0


if __name__ == "__main__":
    write_pods_json()
    if not download_images():
        sys.exit(1)
