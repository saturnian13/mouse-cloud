"""
Need to get button pushing working after rearrange
Can you pass the button itself to the dispatcher and acquire its
position in the table somehow
Or, reconnect all buttons after a rearrange

"""

# If True, do not poll arduinos before uploading or in the background
# For whatever reason this is extremely slow when there are network problems
# A network connection is likely still required to extract training params
MINIMIZE_NETWORKING = False

import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import QTableWidgetItem, QSpinBox, QComboBox, QPushButton
import os
import runner.models
import datetime
import functools
import ArduFSM.Runner.start_runner_cli
import pytz
import glob
import subprocess
import numpy as np

from django.core.management.base import BaseCommand

def readlines_and_strip(filename):
    res = []
    with file(filename) as fi:
        lb_lines = fi.readlines()

    for line in lb_lines:
        sline = line.strip()
        if sline != '':
            res.append(sline)
    
    return res


ROW_HEIGHT = 23

# These are the boxes to display and the order to display them in the runner
# Also affects the boxes that are shown in the "attached boxes" renderer
try:
    LOCALE_BOXES = readlines_and_strip('LOCALE_BOXES')
except IOError:
    LOCALE_BOXES = sorted(runner.models.Box.objects.values_list('name', flat=True))

# Colors of the boxes
try:
    LOCALE_COLORS = readlines_and_strip('LOCALE_COLORS')
except IOError:
    LOCALE_COLORS = []
if len(LOCALE_COLORS) < len(LOCALE_BOXES):
    LOCALE_COLORS += ['white'] * (len(LOCALE_BOXES) - len(LOCALE_COLORS))
LOCALE_BOX2COLOR = dict([(k, v) for k, v in zip(LOCALE_BOXES, LOCALE_COLORS)])

def probe_arduino_user(arduino):
    """Checks if any programs are using /dev/ttyACM*
    
    This can be very slow if there are broken network mounts, for some
    reason.
    
    Returns: result, pid_string
        result: a string
            'in use' : the arduino is in use
            'not in use' : the arduino exists but is not in use
            'does not exist' : no such file
            'unknown error 1' : return code 1, some unhandled error
            'unknown error' : any other unhandled error
        pid_string: a string
            If result == 'in use', this is a space separated list of pids
            Otherwise this will be an empty string
    """
    # Shortcut if the file doesn't exist
    if not os.path.exists(arduino):
        return 'does not exist', ''
    
    # Subprocess to probe arduino
    proc = subprocess.Popen(['fuser', arduino],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()
    returncode = proc.returncode
    
    # Parse results
    pid_string = ''
    if returncode == 0:
        # It exists and it is in use
        # In this case stdout is a space-separated list of pids
        result = 'in use'
        pid_string = stdout
    elif returncode == 1:
        if stdout == '' and stderr == '':
            # File exists and is not in use
            result = 'not in use'
        elif stdout == '' and stderr == (
            'Specified filename %s does not exist.\n' % arduino):
            result = 'does not exist'
        else:
            result = 'unknown error 1'
    else:
        result = 'unknown error'
    
    return result, pid_string

# Hack, see below
tz = pytz.timezone('US/Eastern')


# Load the Qt Creator stuff and use it to generate class definitions
qtCreatorFile = os.path.join(os.path.split(__file__)[0], 
    "MouseRunner/mainwindow.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

# This is used for polling for sandboxes that have started
sandbox_root = os.path.expanduser('~/sandbox_root')

# Helper functions
def create_combo_box(choice_l, index=None, choice=None):
    qcb = QComboBox()
    qcb.addItems(choice_l)
    if index:
        qcb.setCurrentIndex(index)
    elif choice:
        qcb.setCurrentIndex(choice_l.index(choice))
    return qcb

def call_external(mouse, board, box, **other_python_parameters):
    # Make sure the arduino is available
    box_obj = runner.models.Box.objects.filter(name=box).first()
    arduino = box_obj.serial_port
    
    # Get experimenter from mouse object
    experimenter = runner.models.Mouse.objects.filter(
        name=mouse).first().get_experimenter_display()
    
    if not MINIMIZE_NETWORKING:
        # Check before uploading
        result, pid_string = probe_arduino_user(arduino)
    
        if result == 'in use':
            print "cannot upload to box %s; in use by these PIDs: %s" % (
                box, pid_string)
            return

        elif result != 'not in use':
            print "cannot upload to box %s: %s" % (box, result)
            return
    
    print mouse, board, box, experimenter
    ArduFSM.Runner.start_runner_cli.main(mouse=mouse, board=board, box=box,
        experimenter=experimenter,
        **other_python_parameters)

class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.todays_date_display.setText(
            datetime.date.today().strftime('%Y-%m-%d'))

        # Populate the table with data
        self.set_table_data()
    
        # Create Move Up and Move Down tools and hook them to methods
        # http://stackoverflow.com/questions/9166087/move-row-up-and-down-in-pyqt4
        self.move_up_action = QtGui.QAction("Up", self)
        self.connect(self.move_up_action, QtCore.SIGNAL('triggered()'), 
            self.move_up)

        self.move_down_action = QtGui.QAction("Down", self)
        self.connect(self.move_down_action, QtCore.SIGNAL('triggered()'), 
            self.move_down)

        # Move up and move down actions in the tool bar
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(self.move_up_action)
        self.toolbar.addAction(self.move_down_action)
        
        # Timer to refresh data
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.poll_sessions)
        self.timer.start(6000)

    def poll_sessions(self):
        """Poll sessions that have run and update row colors
        
        We don't have a list of sandboxes that were created, so just look
        for anything with today's date.
        """
        now = datetime.datetime.now()
        date_string = now.strftime('%Y-%m-%d')
        
        for nrow in range(self.daily_plan_table.rowCount()):
            # Get the mouse in this row
            mouse_name_item = self.daily_plan_table.item(nrow, 0)
            if mouse_name_item is None:
                continue
            mouse_name = mouse_name_item.text()
            
            # Check if sandbox exists
            # Use EYM format here
            sandboxes = glob.glob(os.path.join(sandbox_root, 
                '*', str(now.year), '%02d' % now.month, # EYM
                '%s-*-%s-*' % (date_string, mouse_name)))
            saved_sandboxes = glob.glob(os.path.join(sandbox_root, 
                '*', str(now.year), '%02d' % now.month, # EYM
                '%s-*-%s-*-saved' % (date_string, mouse_name)))  
            
            # Ignore if it was before 4AM
            def is_after_4am(sandbox_name):
                """Returns True if the sandbox was after 4am.
                
                Returns False if before 4am or if parse error.
                """
                dirname = os.path.split(sandbox_name)[1]
                split = dirname.split('-')
                try:
                    hour_int = int(split[3])
                except (IndexError, ValueError):
                    # Parse error
                    return False
                
                if hour_int >= 4:
                    return True
                else:
                    return False
            
            sandboxes = filter(is_after_4am, sandboxes)
            saved_sandboxes = filter(is_after_4am, saved_sandboxes)
        
            # Get the pushbutton
            qb = self.daily_plan_table.cellWidget(nrow, 6)
            if qb is not None:
                # Set green if done, red if started
                if len(saved_sandboxes) > 0:
                    # Saved
                    qb.setStyleSheet("background-color: green")
                elif len(sandboxes) > 0:
                    # Started but not saved
                    qb.setStyleSheet("background-color: red")
                else:
                    # Not started
                    pass
        
        # Poll attached boxes
        attached_arduinos = []
        attached_cameras = []
        zobj = zip(self.relevant_box_names, self.relevant_box_arduinos,
            self.relevant_box_cameras)
            
        for box_name, arduino, camera in zobj:
            if os.path.exists(arduino):
                attached_arduinos.append(arduino)

            if os.path.exists(camera):
                attached_cameras.append(camera)
        
        # Format into something like "ACM0 (B0 or B1)"
        attached_arduino_strings = []
        for arduino in np.unique(attached_arduinos):
            matching_box_names = [self.relevant_box_names[n] 
                for n in range(len(self.relevant_box_arduinos))
                if self.relevant_box_arduinos[n] == arduino 
            ]
            
            if MINIMIZE_NETWORKING:
                arduino_status = 'unk'                
            else:
                arduino_status, pid_string = probe_arduino_user(arduino)

            attached_arduino_strings.append('%s (%s; %s)' % (
                arduino[-4:], arduino_status, '/'.join(matching_box_names)))

        # Format into something like "video0 (B0 or B1)"
        attached_camera_strings = []
        for camera in np.unique(attached_cameras):
            matching_box_names = [self.relevant_box_names[n] 
                for n in range(len(self.relevant_box_cameras))
                if self.relevant_box_cameras[n] == camera 
            ]
            attached_camera_strings.append('%s (%s)' % (
                camera[-6:], '/'.join(matching_box_names)))
        
        # Also poll any attached arduinos that do NOT correspond to known boxes
        for ardunum in range(10):
            ardupath = '/dev/ttyACM%d' % ardunum
            if ardupath not in self.relevant_box_arduinos:
                if os.path.exists(ardupath):
                    attached_arduino_strings.append(ardupath)
        
        self.attached_boxes_display.setText(
            '\n'.join(attached_arduino_strings))
        self.attached_cameras_display.setText(
            '\n'.join(attached_camera_strings))
    
    def set_table_data(self):
        # Date of most recent session
        # Hack because the datetimes are coming back as aware but in UTC?
        # Are they being stored incorrectly in UTC?
        # Or is django just not retrieving them in the current timezone?
        target_date = runner.models.Session.objects.order_by(
            '-date_time_start')[0].date_time_start.astimezone(tz).date()
        self.target_date_display.setText(target_date.strftime('%Y-%m-%d'))
        
        # Only include sessions from at least this recent
        # This should be longer than the max vacation time
        recency_cutoff = target_date - datetime.timedelta(days=21)
        
        # Get all mice that are in training
        mice_qs = runner.models.Mouse.objects.filter(in_training=True)
        
        # Get previous session from each mouse
        previous_sessions = []
        previous_sessions_sort_keys = []
        new_mice = []
        for mouse in mice_qs.all():
            # Find previous sessions from this mouse from all boxes,
            # sorted by date and excluding ancient ones
            mouse_prev_sess_qs = runner.models.Session.objects.filter(
                mouse=mouse,
                date_time_start__date__gte=recency_cutoff,).order_by(
                'date_time_start')
            
            # Store the most recent, or if None, add to new_mice
            if mouse_prev_sess_qs.count() > 0:
                # The most recent
                sess = mouse_prev_sess_qs.last()
                
                # Skip if the last session was not in LOCALE_BOXES, that is, 
                # if it was trained on some other setup
                if sess.box.name not in LOCALE_BOXES:
                    continue
                
                # Store sess
                previous_sessions.append(sess)
                
                # Store these sort keys to enable sorting
                # Index into LOCALE_BOXES
                previous_sessions_board_idx = LOCALE_BOXES.index(sess.box.name)
                
                # date time start
                dtstart = sess.date_time_start
                
                # sort keys
                previous_sessions_sort_keys.append(
                    (previous_sessions_board_idx, dtstart))
            else:
                new_mice.append(mouse)
        
        # Incantantion to sort previous_sessions by sort keys
        previous_sessions = [x for junk, x in sorted(zip(
            previous_sessions_sort_keys, previous_sessions))]
        
        # Get the choices for box and board
        box_l = LOCALE_BOXES
        board_l = sorted(
            runner.models.Board.objects.all().values_list('name', flat=True))
        
        # Get box arduinos and cameras for polling
        self.relevant_box_names = []
        self.relevant_box_arduinos = []
        self.relevant_box_cameras = []
        for box_name in box_l:
            box = runner.models.Box.objects.filter(name=box_name).first()
            self.relevant_box_names.append(box_name)
            self.relevant_box_arduinos.append(box.serial_port)
            self.relevant_box_cameras.append(box.video_device)
        
        # Set every row with the same widgets
        # 0 - Mouse, read only
        # 1 - Weight, text box
        # 2 - Box, combo box
        # 3 - Board, combo box
        # 4 - Previous pipe, read only
        # 5 - Previous perf, read only
        # 6 - Start, button
        # 7 - Performance, read only
        # 8 - Pipe stop, read only

        self.daily_plan_table.setRowCount(len(previous_sessions))
        for nrow, session in enumerate(previous_sessions):
            # Set the row height
            self.daily_plan_table.setRowHeight(nrow, ROW_HEIGHT)
            
            # Mouse name, read only
            item = QTableWidgetItem(session.mouse.name)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.daily_plan_table.setItem(nrow, 0, item)                
            
            # Weight, text box
            item = QTableWidgetItem(str(session.user_data_weight))
            self.daily_plan_table.setItem(nrow, 1, item)   
            
            # Box, combo box
            qcb = create_combo_box(box_l, choice=session.box.name)
            self.daily_plan_table.setCellWidget(nrow, 2, qcb)

            # Board, combo box
            qcb = create_combo_box(board_l, choice=session.board.name)
            self.daily_plan_table.setCellWidget(nrow, 3, qcb)
            
            # Previous pipe, read only
            try:
                text = '%0.2f' % session.user_data_water_pipe_position_stop
            except TypeError:
                text = ''
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.daily_plan_table.setItem(nrow, 4, item)
            
            # Previous perf, read only
            try:
                text = '%0.f; %0.f' % (
                    100 * session.user_data_left_perf,
                    100 * session.user_data_right_perf,
                    )
            except TypeError:
                text = ''            
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.daily_plan_table.setItem(nrow, 5, item)
            
            # Start, button
            qb = QPushButton('Start')
            #~ qb.setCheckable(True)
            qb.clicked.connect(functools.partial(self.start_session2, qb))
            self.daily_plan_table.setCellWidget(nrow, 6, qb)
            
            # New perf, read only
            item = QTableWidgetItem('-')
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.daily_plan_table.setItem(nrow, 7, item)
            
            # New pipe, text box
            item = QTableWidgetItem('-')
            self.daily_plan_table.setItem(nrow, 8, item)

    def start_session(self, row):
        """Collect data from row and pass to start session"""
        # Highlight clicked cell
        self.daily_plan_table.setCurrentCell(row, 6)
        
        # Get color from box
        box_name = str(self.daily_plan_table.cellWidget(row, 2).currentText())
        fig_color = LOCALE_BOX2COLOR[box_name]
        
        # Call
        call_external(
            mouse=str(self.daily_plan_table.item(row, 0).text()),
            board=str(self.daily_plan_table.cellWidget(row, 3).currentText()),
            box=str(self.daily_plan_table.cellWidget(row, 2).currentText()),
            #~ recent_date=str(self.target_date_display.getText()),
            recent_weight=str(self.daily_plan_table.item(row, 1).text()),
            recent_pipe=str(self.daily_plan_table.item(row, 4).text()),
            background_color=fig_color,
        )

    def start_session2(self, row_qb):
        """Start the session associated with the push button for this row.
        
        """
        # Find which row the push button is in
        session_row = -1
        for nrow in range(self.daily_plan_table.rowCount()):
            if self.daily_plan_table.cellWidget(nrow, 6) is row_qb:
                session_row = nrow
                break
        if session_row == -1:
            raise ValueError("cannot find row for pushbutton")
        
        # Extract the mouse, board, box from this row
        self.start_session(session_row)
    
    def move_row(self, old_row, new_row):
        """Move data from old_row to new_row
        
        First inserts a new row at position new_row.
        Then copies all data.
        Then deletes old_row.
        
        TODO: don't create or remove rows, just set the items in order
        to swap them
        """
        # Keep track of the current column
        current_column = self.daily_plan_table.currentColumn()

        # Determine what the row index will be after the move is complete
        if new_row > old_row:
            final_row = new_row - 1
        elif new_row < old_row:
            final_row = new_row
        else:
            raise ValueError("cannot move a row to itself")

        # Insert a new row
        self.daily_plan_table.insertRow(new_row)
        self.daily_plan_table.setRowHeight(new_row, ROW_HEIGHT)
            
        # Copy the contents
        for ncol in range(self.daily_plan_table.columnCount()):
            # Depends on the data type
            if ncol in [2, 3]:
                # Combo box widgets
                widget = self.daily_plan_table.cellWidget(old_row, ncol)
                self.daily_plan_table.setCellWidget(new_row, ncol, widget)
            elif ncol == 6:
                # QPushbutton
                qb = self.daily_plan_table.cellWidget(old_row, ncol)
                self.daily_plan_table.setCellWidget(new_row, ncol, qb)
            else:
                # Items
                item = self.daily_plan_table.takeItem(old_row, ncol)
                self.daily_plan_table.setItem(new_row, ncol, item)

        # Set current cell to same column in new_row
        self.daily_plan_table.setCurrentCell(new_row, current_column)
        
        # Delete the old row
        self.daily_plan_table.removeRow(old_row)        

        # Fix the numbering of the rows
        self.daily_plan_table.setVerticalHeaderLabels(
            [str(n + 1) for n in range(self.daily_plan_table.rowCount())])

    def move_down(self):
        # http://stackoverflow.com/questions/9166087/move-row-up-and-down-in-pyqt4
        row = self.daily_plan_table.currentRow()
        if row < self.daily_plan_table.rowCount() - 1:
            self.move_row(row, row + 2)
   
    def move_up(self):    
        row = self.daily_plan_table.currentRow()        
        if row > 0:
            self.move_row(row + 1, row - 1)


class Command(BaseCommand):
    def handle(self, **options):
        app = QtGui.QApplication(sys.argv)
        window = MyApp()
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    ## Get the most recent stuff from runner
    app = QtGui.QApplication(sys.argv)
    
    # Set style to avoid Qt bugs
    # http://stackoverflow.com/questions/14606396/gtk-critical-ia-gtk-widget-style-get-assertion-gtk-is-widget-widget-fa
    app.set_style('Fusion')
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
