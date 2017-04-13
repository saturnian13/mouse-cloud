"""
Need to get button pushing working after rearrange
Can you pass the button itself to the dispatcher and acquire its
position in the table somehow
Or, reconnect all buttons after a rearrange

"""

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

from django.core.management.base import NoArgsCommand


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
    print mouse, board, box
    ArduFSM.Runner.start_runner_cli.main(mouse=mouse, board=board, box=box,
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
        """Poll sessions that have run and update row colors"""
        now = datetime.datetime.now()
        date_string = now.strftime('%Y-%m-%d')
        for nrow in range(self.daily_plan_table.rowCount()):
            # Get the mouse in this row
            mouse_name_item = self.daily_plan_table.item(nrow, 0)
            if mouse_name_item is None:
                continue
            mouse_name = mouse_name_item.text()
            
            # Check if sandbox exists
            sandboxes = glob.glob(os.path.join(sandbox_root, 
                '%s-*-%s-*' % (date_string, mouse_name)))
            saved_sandboxes = glob.glob(os.path.join(sandbox_root, 
                '%s-*-%s-*-saved' % (date_string, mouse_name)))                
        
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
    
    def set_table_data(self):
        # Date of most recent session
        # Hack because the datetimes are coming back as aware but in UTC?
        # Are they being stored incorrectly in UTC?
        # Or is django just not retrieving them in the current timezone?
        target_date = runner.models.Session.objects.order_by(
            '-date_time_start')[0].date_time_start.astimezone(tz).date()
        self.target_date_display.setText(target_date.strftime('%Y-%m-%d'))
        
        # Get all mice that are in training
        mice_qs = runner.models.Mouse.objects.filter(in_training=True)
        
        # Get previous session from each mouse
        previous_sessions = []
        new_mice = []
        for mouse in mice_qs.all():
            # Find previous sessions
            mouse_prev_sess_qs = runner.models.Session.objects.filter(
                mouse=mouse).order_by('date_time_start')
            
            # Store the most recent, or if None, add to new_mice
            if mouse_prev_sess_qs.count() > 0:
                previous_sessions.append(mouse_prev_sess_qs.last())
            else:
                new_mice.append(mouse)
        
        # Sort the sessions by time
        previous_sessions = sorted(previous_sessions, 
            key=lambda s: s.date_time_start)
        
        # Get the choices for box and board
        box_l = sorted([box.name for box in runner.models.Box.objects.all()])
        board_l = sorted([board.name for board in runner.models.Board.objects.all()])
        
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

        self.daily_plan_table.setRowCount(len(previous_sessions) + 1)
        for nrow, session in enumerate(previous_sessions):
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
        self.daily_plan_table.setCurrentCell(row, 6)
        call_external(
            mouse=str(self.daily_plan_table.item(row, 0).text()),
            board=str(self.daily_plan_table.cellWidget(row, 3).currentText()),
            box=str(self.daily_plan_table.cellWidget(row, 2).currentText()),
            #~ recent_date=str(self.target_date_display.getText()),
            recent_weight=str(self.daily_plan_table.item(row, 1).text()),
            recent_pipe=str(self.daily_plan_table.item(row, 4).text()),
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

    def move_down(self):
        # http://stackoverflow.com/questions/9166087/move-row-up-and-down-in-pyqt4
        row = self.daily_plan_table.currentRow()
        if row < self.daily_plan_table.rowCount() - 1:
            self.move_row(row, row + 2)
   
    def move_up(self):    
        row = self.daily_plan_table.currentRow()        
        if row > 0:
            self.move_row(row + 1, row - 1)


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        app = QtGui.QApplication(sys.argv)
        window = MyApp()
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    ## Get the most recent stuff from runner
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
