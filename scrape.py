# This needs to be run in django shell
# Copy a mouse from the master database to mouse-cloud
# Not finished yet ... Need to work out the new_genotype logic

import pandas
import sqlalchemy
import runner.models
import os
import json

# Copied from colony.models
def new_genotype(mouse):
    """Return a genotype string by concatenating linked MouseGene objects
    
    If wild_type:
        returns 'pure WT'
    Elif the mouse has no mousegenes, or only -/- mousegenes:
        returns 'negative'
    Otherwise:
        returns a string of the format 
            "GENE1(ZYGOSITY1); GENE2(ZYGOSITY2)..."
        Genes with zygosity -/- are not included in this string.
    """
    # If it's wild type, it shouldn't have any genes
    if not self.mousegene_set.exists() and self.wild_type:
        return 'pure WT'
    
    # Get all MouseGenes other than -/-
    res_l = []
    for mg in self.mousegene_set.all():
        if mg.zygosity == MouseGene.zygosity_nn:
            continue
        res_l.append('%s(%s)' % (mg.gene_name, mg.zygosity))
    
    if len(res_l) == 0:
        # It has no mousegenes, or only -/- mouse genes
        # Render as 'negative'. Avoid confusion with 'WT'
        # Also don't include the 'pure' because 'pure negative'
        # is confusing.            
        return 'negative'
    else:
        # Join remaining mousegenes
        return '; '.join(res_l)


# Which mouse to get and what info to assign
husbandry_name = '3068-5'
headplate_color = ''
training_name = ''

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
1/0

# Check whether this mouse is already in the database
if len(colony.models.ChrisMouse.objects.filter(name=mouse['name'])) > 0:
    raise ValueError("Mouse with that name already exists")

# Create a new mouse with values copied from the old one
new_mouse = runner.models.Mouse(
    name=training_name,
    husbandry_name=mouse.name,
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
new_mouse.genotype = 'TBD'

1/0
new_mouse.save()