from django.shortcuts import render
from django.views.generic import CreateView, ListView
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from .models import Session

import pandas
import datetime

# I think there's a thread problem with importing pyplot here
# Maybe if you specify matplotlib.use('Agg') it would be okay
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import pytz 
import models

# Hack, see below
tz = pytz.timezone('US/Eastern')

def weight_plot(request):
    cohorts = [
        ['KM65', 'KF75', 'KM83', 'KM84', 'KM85', 'KM86',],
        ['KM87', 'KM88', 'KF89', 'KF90',],
        ['KM91', 'KF94', 'KF95', 'KM97'],
        ]

    f = Figure(figsize=(12, 4 * len(cohorts)), dpi=80)
    axa = [f.add_subplot(len(cohorts), 1, n_cohort + 1) 
        for n_cohort in range(len(cohorts))]

    #~ f, axa = plt.subplots(len(cohorts), 1, figsize=(12, 4 * len(cohorts)), dpi=80)
    f.subplots_adjust(top=.95, bottom=.1, hspace=.4)
    f.set_facecolor('w')

    rec_l = []
    for session in Session.objects.all():
        rec_l.append({
            'mouse': session.mouse.name,
            'weight': session.user_data_weight,
            'date': session.date_time_start.astimezone(tz).date(),
            })
    df = pandas.DataFrame.from_records(rec_l).dropna()
    piv = df.pivot_table(index='date', columns='mouse', values='weight')
    labels = map(str, piv.index)
    
    for cohort, ax in zip(cohorts, axa):
        cohort = [mouse for mouse in cohort if mouse in piv.columns]
        if len(cohort) == 0:
            continue
        ax.plot(piv[cohort].values, marker='s', ls='-')
        ax.set_xticks(range(len(piv)))
        labels = piv.index.format(formatter = lambda x: x.strftime('%m-%d'))
        ax.set_xticklabels(labels, rotation=45, size='medium')
        ax.legend(cohort, loc='lower left', fontsize='medium')
        ax.set_xlim((len(piv) - 30 - 0.5, len(piv) - .5))        

    canvas = FigureCanvas(f)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

def rewards_plot(request):
    boxes = Box.objects.all()
    f = Figure()
    axes = [f.add_subplot(len(boxes), 1, n+1) for n in range(len(boxes))]

    for box, ax in zip(boxes, axes):
        ax.set_title(box.name)
        ax.set_ylabel('Water Volume (uL)')

        

        # for box, ax
        # for session in Session.objects.filter(box=box, date_time_start__lte=datetime.today)

    canvas + FigureCanvas(f)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response
    


