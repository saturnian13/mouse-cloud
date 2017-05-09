# This needs to be run in django shell
# Copy a mouse from the master database to mouse-cloud

import pandas
import sqlalchemy
import runner.models
import os
import json


# Which mouse to get and what info to assign
husbandry_name = '3108-9'
headplate_color = 'SS'
training_name = 'KM127'
training_number = 127

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

# Join the mousegene_table on gene_type for sorting
mousegene_table = mousegene_table.join(gene_table[['gene_type']], 
    on='gene_name_id')

# breeding_cage is a primary key for litter
litter_table = litter_table.set_index('breeding_cage_id')

# Identify the row that corresponds to the target mouse
mouse = mouse_table[mouse_table.name == husbandry_name].iloc[0]

# Get the DOB from the litter or directly from the mouse
if not pandas.isnull(mouse.litter_id):
    new_mouse_dob = litter_table.loc[int(mouse.litter_id), 'dob'].date()
elif not pandas.isnull(mouse.manual_dob):
    # Not sure if the '.date()' method is necessary here
    new_mouse_dob = mouse.manual_dob.date()
else:
    print "warning: cannot get dob"

# Get the genotype
# This recapitulates the logic from colony.Mouse
mousegenes = mousegene_table[mousegene_table.mouse_name_id == mouse.id]
mousegenes = mousegenes.sort_values('gene_type')
if len(mousegenes) == 0 and mouse.wild_type:
    new_mouse_genotype = 'pure WT'
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
        new_mouse_genotype = 'negative'
    else:
        new_mouse_genotype = '; '.join(res_l)

# Collate all things to set
# dict from django field name to correct value
params = {
    'name': training_name,
    'number': training_number,
    'sex': mouse.sex,
    'headplate_color': headplate_color,
    'husbandry_name': mouse['name'],
    'dob': new_mouse_dob,
    'genotype': new_mouse_genotype,
    'stimulus_set': 'trial_types_CCL_1srvpos',
    'max_rewards_per_trial': 999,
    'scheduler': 'ForcedAlternationLickTrain',
    'protocol_name': 'LickTrain',
    'script_name': 'LickTrain.py',
}
    

# Check whether this mouse is already in the database
qs = runner.models.Mouse.objects.filter(husbandry_name=mouse['name'])
if len(qs) > 0:
    print "mouse already exists; error checking"
    existing_mouse = qs.first()

    changes_made = False
    for django_field_name, value in params.items():
        # Check whether value set correctly
        existing_value = existing_mouse.__getattribute__(
            django_field_name)
        
        if existing_value != value:
            resp = raw_input("warning: %s is %s not %s; set? [y/N]" % (django_field_name,
                str(existing_value), str(value)))
            
            if resp.upper() == 'Y':
                existing_mouse.__setattr__(django_field_name, value)
                changes_made = True
    
    if changes_made:
        existing_mouse.save()
        # Could set here using __setattr__

else:
    # Create a new mouse with values copied from the old one
    new_mouse = runner.models.Mouse(
        name=training_name,
        number=training_number,
        husbandry_name=mouse['name'],
        sex=mouse.sex,
        headplate_color=headplate_color,
    )

    # Set in new object
    new_mouse.dob = new_mouse_dob
    new_mouse.genotype = new_mouse_genotype

    # Training parameters
    new_mouse.stimulus_set = 'trial_types_CCL_1srvpos'
    new_mouse.max_rewards_per_trial = 999
    new_mouse.scheduler = 'ForcedAlternationLickTrain'
    new_mouse.protocol_name = 'LickTrain'
    new_mouse.script_name = 'LickTrain.py'

    new_mouse.save()