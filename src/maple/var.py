import pandas as pd

mob = pd.read_csv('src/maple/artale_mob.csv')
mob_list = mob['name_tw'].to_list()