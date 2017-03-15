# This needs to be run in django shell
# Copy a mouse from the master database to mouse-cloud

import pandas
import sqlalchemy
import runner.models
import os
import json


# Which mouse to get and what info to assign
husbandry_name = '3082-7'
headplate_color = 'BG'
training_name = 'KF113'

# Connect to the master database
master_credentials_path = os.path.expanduser(
    '~/dev/HeroMouseColony/HeroMouseColony/local_cache')
with file(master_credentials_path) as fi:
    master_credentials_json = json.load(fi)
master_credentials = master_credentials_json['heroku']['database_url']
conn = sqlalchemy.create_engine(master_credentials)

# Read the tables using pandas
mouse_table = pandas.read_sql_table('colony_mouse', conn)
mousegene_table = pandas.read_sql_table('colony_mousegene', conn).set_index('id')
gene_table = pandas.read_sql_table('colony_gene', conn).set_index('id')
litter_table = pandas.read_sql_table('colony_litter', conn)

# breeding_cage is a primary key for litter
litter_table = litter_table.set_index('breeding_cage_id')

# Identify the row that corresponds to the target mouse
mouse = mouse_table[mouse_table.name == husbandry_name].iloc[0]

# Check whether this mouse is already in the database
if len(runner.models.Mouse.objects.filter(husbandry_name=mouse['name'])) > 0:
    raise ValueError("Mouse with that name already exists")

# Create a new mouse with values copied from the old one
new_mouse = runner.models.Mouse(
    name=training_name,
    husbandry_name=mouse['name'],
    sex=mouse.sex,
    headplate_color=headplate_color,
)

# Get the DOB from the litter or directly from the mouse
if not pandas.isnull(mouse.litter_id):
    new_mouse.dob = litter_table.loc[int(mouse.litter_id), 'dob']
elif not pandas.isnull(mouse.manual_dob):
    new_mouse.dob = mouse.manual_dob
else:
    print "warning: cannot get dob"

# Set the genotype
# This recapitulates the logic from colony.Mouse
mousegenes = mousegene_table[mousegene_table.mouse_name_id == mouse.id]
if len(mousegenes) == 0 and mouse.wild_type:
    genotype = 'pure WT'
else:
    # Iterate over mousegenes
    res_l = []
    for idx, row in mousegenes.iterrows():
        # Skip -/-
        if row['zygosity'] == '-/-':
            continue
        
        # Form gene name and zygosity
        res = '%s(%s)' % (
            gene_table.loc[row['gene_name_id'], 'name'], 
            row['zygosity'])
        res_l.append(res)
    
    if len(res_l) == 0:
        genotype = 'negative'
    else:
        genotype = '; '.join(res_l)

# Set in new object
new_mouse.genotype = genotype

# Training parameters
new_mouse.stimulus_set = 'trial_types_CCL_1srvpos'
new_mouse.max_rewards_per_trial = 999
new_mouse.scheduler = 'ForcedAlternationLickTrain'
new_mouse.protocol_name = 'LickTrain'
new_mouse.script_name = 'LickTrain.py'

new_mouse.save()