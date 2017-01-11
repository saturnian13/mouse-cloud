from django.shortcuts import render
from django.views.generic import CreateView, ListView
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from .models import Session
from .models import Box, Mouse
import datetime
import pandas
from datetime import date, timedelta
import numpy as np


# I think there's a thread problem with importing pyplot here
# Maybe if you specify matplotlib.use('Agg') it would be okay
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import date2num
import pytz 
import models

# Interpret all times as Eastern
tz = pytz.timezone('America/New_York')

def weight_plot(request):
    ## Get cohorts (so we can detect missing data later)
    qs = Mouse.objects.filter(in_training=True)
    cohort_df = pandas.DataFrame.from_records(list(qs.values_list(
        'name', 'training_cohort')), columns=['mouse', 'cohort'])
    
    # Replace all missing cohorts with -1
    cohort_df.loc[cohort_df.cohort.isnull(), 'cohort'] = -1
    
    # Group the mice
    cohort2mouse_names = dict([(cohort, list(ser.values)) 
        for cohort, ser in cohort_df.groupby('cohort')['mouse']])

    ## Extract weights
    columns = ['date_time_start', 'mouse__name', 'user_data_weight', 
        'mouse__training_cohort']
    thresh_date = datetime.date.today() - datetime.timedelta(days=45)
    qs = Session.objects.filter(
        mouse__in_training=True, date_time_start__date__gte=thresh_date)
    weight_df = pandas.DataFrame.from_records(list(qs.values_list(*columns)),
        columns=columns)
    weight_df['date'] = weight_df['date_time_start'].apply(
        lambda dt: dt.astimezone(tz).date())

    # Replace missing cohorts in the actual data
    weight_df.loc[
        weight_df['mouse__training_cohort'].isnull(), 
        'mouse__training_cohort'] = -1

    # Pivot
    # In case there are multiple sessions, take the mean
    piv = weight_df.pivot_table(index='date', 
        columns=('mouse__training_cohort', 'mouse__name'),
        values='user_data_weight')

    ## Make figure
    cohort_labels = sorted(cohort2mouse_names.keys())
    f = Figure(figsize=(12, 4 * len(cohort_labels)), dpi=80)
    axa = [
        f.add_subplot(len(cohort_labels), 1, n_cohort + 1) 
        for n_cohort in range(len(cohort_labels))
    ]
    #~ f, axa = plt.subplots(len(cohorts), 1, figsize=(12, 4 * len(cohorts)), dpi=80)
    f.subplots_adjust(top=.95, bottom=.1, hspace=.4)
    f.set_facecolor('w')
    
    # Plot each
    for cohort_label, ax in zip(cohort_labels, axa):
        # Get weights for this cohort or display error
        try:
            cohort_weights = piv[cohort_label]
        except KeyError:
            ax.set_title('missing data from: %s' % ' '.join(
                cohort2mouse_names[cohort_label]))
            continue
        
        # Plot
        ax.plot(cohort_weights.values, marker='s', ls='-')
        ax.set_ylim((14, 30))
        
        # Xticks are the formatted date
        ax.set_xticks(range(len(cohort_weights)))
        labels = cohort_weights.index.format(
            formatter = lambda x: x.strftime('%m-%d'))
        ax.set_xticklabels(labels, rotation=45, size='medium')
        ax.set_xlim((-.5, len(cohort_weights) - .5))
        
        # Legend is the mouse names
        ax.legend(list(cohort_weights.columns), loc='lower left', 
            fontsize='medium')
        
        # Title any missing mice
        missing_mice = [mouse for mouse in cohort2mouse_names[cohort_label]
            if mouse not in cohort_weights.columns]
        if len(missing_mice) > 0:
            ax.set_title('missing mice: %r' % missing_mice)

    canvas = FigureCanvas(f)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response

def rewards_plot(request):
    """Plots the reward size for each box over days"""
    # Get all the boxes
    boxes = Box.objects.all()
    
    # Create a matplotlib figure to plot into
    f = Figure(figsize=(12, 20), dpi=80)
    f.set_tight_layout(True)
    f.set_facecolor('w')

    # Horizontal bars will be plotted here to show the normal bounds
    min_water_limit = 4
    max_water_limit = 6

    # Values outside this range are ignored because they are usually
    # mistakes
    ignore_lower_thresh = .0005
    ignore_upper_thresh = .1
    

    # Iterate over boxes
    for i, box in enumerate(boxes):
        # Get all sessions within the past 30 days that the box owns
        box_sessions = Session.objects.filter(box=box, 
            date_time_start__gte = date.today() - timedelta(days=30))
        
        # Only display it if there are any sessions
        if len(box_sessions) > 0:
            # Extract the calculated reward durations
            sessions_by_date = pandas.DataFrame.from_records(
                box_sessions.values())[[
                "date_time_start", "user_data_left_valve_mean", 
                "user_data_right_valve_mean"]].dropna()
            
            # Convert to date object
            sessions_by_date.loc[:, "date_start"] = [
                dt.date() for dt in sessions_by_date["date_time_start"]]
            
            # Drop the ones outside the range
            colnames = [
                'user_data_left_valve_mean', 
                'user_data_right_valve_mean']
            sessions_by_date = sessions_by_date[
                (sessions_by_date[colnames].min(1) > ignore_lower_thresh) &
                (sessions_by_date[colnames].max(1) < ignore_upper_thresh)
            ]
            
            # Average the water consumption values by date
            volumes = sessions_by_date.groupby('date_start').aggregate(np.mean)

            # Convert to uL
            left_volume = volumes["user_data_left_valve_mean"].values * 1000
            right_volume = volumes["user_data_right_valve_mean"].values *1000

            # Add axis and plot the volumes
            ax = f.add_subplot(len(boxes), 1, i+1)
            ax.plot(left_volume, '-o', color='b')
            ax.plot(right_volume, '-s', color='g')
            
            # Ticklabels for the dates
            ax.set_xticks(range(len(volumes)))
            labels = volumes.index.format(
                formatter = lambda x: x.strftime('%m-%d'))
            ax.set_xticklabels(labels, rotation=45, size='medium')

            # Show normal water range
            ax.axhline(min_water_limit, color='r', linestyle='--')
            ax.axhline(max_water_limit, color='r', linestyle='--')
            
            # Consistent ylims
            ax.set_ylim((2, 8))

            # Labels
            ax.set_ylabel('Volume released (uL)')
            title = "{} (Blue = Left Pipe, Green = Right Pipe)".format(box.name)
            ax.set_title(title)

    # Print to png
    canvas = FigureCanvas(f)
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response



