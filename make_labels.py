# New version
# Run like this:
# python ~/dev/mouse-cloud/manage.py shell


import numpy as np
import labels
from reportlab.graphics import shapes
import runner.models

specs = labels.Specification(215.9, 279.4, 2, 15, 87.3, 16.9, corner_radius=2,
    row_gap=0, column_gap=13.3)

def draw_label(label, width, height, obj):
    print obj
    try:
        fillColor = obj['fillColor']
    except KeyError:
        fillColor = 'black'
    
    kwargs = {'fontName': 'Helvetica', 'fontSize': 10, 'textAnchor': 'middle',
        'fillColor': fillColor}

    if obj['typ'] == 'water restriction':
        kwargs = {'fontName': 'Helvetica', 'fontSize': 10, 'textAnchor': 'middle',
            'fillColor': fillColor}        
        
        ## Header
        label.add(shapes.String(
            width * .5,
            height - 10,
            "WATER RESTRICTED -- Cage %s" % obj['cage_name'],
            **kwargs))

        label.add(shapes.String(
            width * .5,
            height - 20,
            "LAB: BRUNO / AAAO5201. UNI: CCR2137",
            **kwargs))
        
        label.add(shapes.Line(
            width * .02, height-22, width * .98, height-22,
            strokeColor=fillColor))
        
        
        ## Each mouse
        xy_l = [(.2, -32), (.5, -32), (.8, -32), (.2, -42), (.5, -42), (.8, -42)]
        
        for mouse, headplate, xy in zip(obj['mice'], obj['headplates'], xy_l):
            label.add(shapes.String(
                width * xy[0],
                height + xy[1],
                '%s - %s' % (mouse, headplate),
                **kwargs))
    
    elif obj['typ'] == 'cage':
        kwargs = {'fontName': 'Helvetica', 'fontSize': 10, 'textAnchor': 'start',
            'fillColor': fillColor}        

        ## Header
        label.add(shapes.String(
            width * .5, height - 10, "Cage: %s" % obj['cage_name'],
            fontName='Helvetica', fontSize=10, fillColor=fillColor,
            textAnchor='middle'))
        
        ## Each mouse
        xy_l = [(.1, -20), (.6, -20), (.1, -30), (.6, -30), (.1, -40)]
        
        for mouse, full_name, genotype, headplate, xy in zip(
            obj['mice'], obj['full_names'], obj['genotypes'], 
            obj['headplates'], xy_l):
    
            label.add(shapes.String(
                width * xy[0],
                height + xy[1],
                '%s - %s - %s' % (mouse, headplate, full_name),
                **kwargs))


#~ # Determine which cages to include
#~ cage_name_l = []
#~ skip_cage_l = ['Green', 'Blue']
#~ for cage in colony.models.ChrisCage.objects.all():
    #~ if cage.chrismouse_set.count() == 0:
        #~ continue
    #~ if cage.name in skip_cage_l:
        #~ continue
    #~ cage_name_l.append(cage.name)
#~ cage_name_l = ['Purple2', 'Purple3', 'Pink',]

# Directly specify the cages we need
water_restriction_cage_name_l = ['CR18',]
cage_card_cage_name_l = ['CR18',]
cage_name_l = water_restriction_cage_name_l + cage_card_cage_name_l
cage_name_l = list(np.unique(cage_name_l))
    
# Get the colony specs
colony_specs = {}
for cage_name in cage_name_l:
    # Init the specs for this cage
    colony_specs[cage_name] = {}
    colony_specs[cage_name]['mice'] = []
    colony_specs[cage_name]['headplates'] = []
    colony_specs[cage_name]['genotypes'] = []
    colony_specs[cage_name]['full_names'] = []
    colony_specs[cage_name]['cage_name'] = cage_name

    # Find the cage
    cage = runner.models.BehaviorCage.objects.filter(name=cage_name).first()
    
    # Set the color
    colony_specs[cage_name]['fillColor'] = cage.label_color.lower()
    if colony_specs[cage_name]['fillColor'] == 'pink':
        colony_specs[cage_name]['fillColor'] = 'magenta'
    
    # Iterate over mice
    for mouse in cage.mouse_set.all():
        colony_specs[cage_name]['mice'].append(mouse.name)
        colony_specs[cage_name]['headplates'].append(mouse.headplate_color)
        colony_specs[cage_name]['genotypes'].append(mouse.genotype)
        colony_specs[cage_name]['full_names'].append(mouse.husbandry_name)

# Make a sheet
sheet = labels.Sheet(specs, draw_label, border=False)

# Define the used labels
used_labels = []
for row in range(1, 4): # second number is the 1-based row to start on
    for col in range(1, 3):
        used_labels.append((row, col))
sheet.partial_page(1, used_labels)

# Add label for each cage
for cage_name, cage_specs in colony_specs.items():
    if cage_name in water_restriction_cage_name_l:
        # Copy specs over
        cage_specs2 = cage_specs.copy()
        cage_specs2['typ'] = 'water restriction'
        
        # Add the label
        sheet.add_label(cage_specs2)
    
    if cage_name in cage_card_cage_name_l:
        # Copy specs over
        cage_specs2 = cage_specs.copy()
        cage_specs2['typ'] = 'cage'
        
        # Add the label
        sheet.add_label(cage_specs2)        

sheet.save("basic2.pdf")
