# Script to put new saved sessions into runmouse django

import django
import runner.models
import MCwatch.behavior
import os
import json
import datetime
from django.utils import timezone
from ArduFSM.plot import count_hits_by_type_from_trials_info
import ArduFSM

from django.core.management.base import NoArgsCommand




def string2float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None

def split_once(path):
    return os.path.split(path)[0]




class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # get new records
        PATHS = MCwatch.behavior.db.get_paths()
        bdf = MCwatch.behavior.db.search_for_behavior_files(
            behavior_dir=PATHS['behavior_dir'],
            clean=True)
        perfdf = MCwatch.behavior.db.get_perf_metrics()


        for idx, logfile in bdf['filename'].iteritems():
            # If it's already in the database, then skip
            session_name = bdf.loc[idx, 'session']
            if len(runner.models.Session.objects.filter(name=session_name)) > 0:
                continue
            
            # Get the sandbox directory from the logfile
            script_dir = split_once(split_once(logfile))
            sandbox_dir = split_once(script_dir)
            autosketch_path = os.path.join(sandbox_dir, 'Autosketch')
            
            # Forgot to save board in parameters so have to extract from path
            sandbox_name = os.path.split(sandbox_dir)[1]
            path_board_name = sandbox_name.split('-')[-3]
            path_mouse_name = sandbox_name.split('-')[-4]
            
            # Parse parameters
            with file(os.path.join(script_dir, 'parameters.json')) as fp:
                parameters = json.load(fp)
            
            # Parse results
            try:
                with file(os.path.join(script_dir, 'logfiles', 'results')) as fp:
                    results = json.load(fp)   
            except (IOError, ValueError):
                # no results
                print "warning: cannot load results json in %s" % script_dir
                results = {}

            # Manually put in some stuff for perfdf if not stored
            if 'left_perf' not in results:
                data_available = True
                try:
                    tm = MCwatch.behavior.db.get_trial_matrix(session_name)
                except IOError:
                    data_available = False
                
                if data_available:
                    # Left and right perf
                    typ2perf = count_hits_by_type_from_trials_info(tm, 'rewside')
                    try:
                        results['left_perf'] = typ2perf['left'][0] / float(
                            typ2perf['left'][1])
                        results['right_perf'] = typ2perf['right'][0] / float(
                            typ2perf['right'][1])
                    except (KeyError, ZeroDivisionError):
                        results['left_perf'] = None
                        results['right_perf'] = None
                    
                    # Put bias summary
                    ntm = ArduFSM.TrialMatrix.numericate_trial_matrix(tm)
                    anova_res = ArduFSM.TrialMatrix.run_anova(ntm)
                    results['bias_summary'] = anova_res
                    
                    # Reward string
                    if 'l_valve_mean' not in results:
                        lines = ArduFSM.TrialSpeak.read_lines_from_file(logfile)
                        splines = ArduFSM.TrialSpeak.split_by_trial(lines)
                        rewdict = ArduFSM.plot.count_rewards(splines)
                        nlrew = (rewdict['left auto'].sum() + 
                            rewdict['left manual'].sum() + rewdict['left direct'].sum())
                        nrrew = (rewdict['right auto'].sum() + 
                            rewdict['right manual'].sum() + rewdict['right direct'].sum())
                        
                        if 'l_volume' in results:
                            results['l_valve_mean'] = float(results['l_volume']) / nlrew
                        if 'r_volume' in results:
                            results['r_valve_mean'] = float(results['r_volume']) / nrrew

            # Find the matching Box
            box_name = parameters.get('box', None)
            if box_name is None:
                box = None
            else:
                box = runner.models.Box.objects.get(name=box_name)

            # Find the matching Board
            board_name = parameters.get('board', None)
            if board_name is None:
                board = None
            else:
                board = runner.models.Board.objects.get(name=board_name)
            
            # Find the matching Mouse
            mouse_name = parameters.get('mouse')
            if mouse_name is None:
                mouse = None
            else:
                mouse = runner.models.Mouse.objects.get(name=mouse_name)
            
            # Create the session
            print "adding session %s to the database" % bdf.loc[idx, 'session']
            session = runner.models.Session(
                name=bdf.loc[idx, 'session'],
                mouse=mouse,
                logfile=bdf.loc[idx, 'filename'],
                board=board,
                box=box,
                sandbox=sandbox_name,
                autosketch_path=autosketch_path,
                python_param_scheduler_name=parameters.get('scheduler'),
                python_param_stimulus_set=parameters.get('stimulus_set'),
                script_path=script_dir,
                date_time_start=timezone.make_aware(
                    bdf.loc[idx, 'dt_start'], timezone.get_current_timezone()),
                date_time_stop=timezone.make_aware(
                    bdf.loc[idx, 'dt_end'], timezone.get_current_timezone()),
                user_data_water_pipe_position_stop=string2float(
                    results.get('final_pipe')),
                user_data_left_water_consumption=string2float(
                    results.get('l_volume')),
                user_data_right_water_consumption=string2float(
                    results.get('r_volume')),
                user_data_weight=string2float(
                    results.get('mouse_mass')),
                user_data_left_valve_mean=string2float(
                    results.get('l_valve_mean')),
                user_data_right_valve_mean=string2float(
                    results.get('r_valve_mean')),            
                user_data_left_perf=string2float(
                    results.get('left_perf')),
                user_data_right_perf=string2float(
                    results.get('right_perf')),              
                user_data_bias_summary=results.get('bias_summary'),       
            )
            session.save()