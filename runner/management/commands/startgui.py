"""
Need to get button pushing working after rearrange
Can you pass the button itself to the dispatcher and acquire its
position in the table somehow
Or, reconnect all buttons after a rearrange

"""

import threading
import csv
import ArduFSM.Runner.Sandbox
import time

import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtGui import QTableWidgetItem, QSpinBox, QComboBox, QPushButton
import os
import runner.models
import datetime
import functools
import ArduFSM.Runner.start_runner_cli
import pytz

from django.core.management.base import NoArgsCommand

os.chdir(os.path.dirname(os.path.realpath(__file__)))


# Hack, see below
tz = pytz.timezone('US/Eastern')


# Load the Qt Creator stuff and use it to generate class definitions
qtCreatorFile = os.path.join(os.path.split(__file__)[0], 
    "MouseRunner/mainwindow.ui")
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

# Helper functions
def create_combo_box(choice_l, index=None, choice=None):
    qcb = QComboBox()
    qcb.addItems(choice_l)
    if index:
        qcb.setCurrentIndex(index)
    elif choice:
        qcb.setCurrentIndex(choice_l.index(choice))
    return qcb

class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        #Load notes
        self.read_notes()
        

        self.todays_date_display.setText(
            datetime.date.today().strftime('%Y-%m-%d'))

        self.selectedDate = datetime.date.today()

        # Populate the table with data
        self.initial_set_table_data()

        self.loadDateButton.clicked.connect(self.load_date)

        self.addRowButton.clicked.connect(self.addRow)
    
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

        #Notes saving button
        self.saveNotesButton.clicked.connect(self.save_notes)

  
    def load_date(self):
        date, ok = DateDialog.getDate(self.selectedDate)
        date = date.toPyDate()

        if ok:
            self.daily_plan_table.clearContents()
            self.set_table_data(date)
            self.selectedDate = date

    def initial_set_table_data(self):
        # Date of most recent session
        # Hack because the datetimes are coming back as aware but in UTC?
        # Are they being stored incorrectly in UTC?
        # Or is django just not retrieving them in the current timezone?
        target_date = runner.models.Session.objects.order_by(
            '-date_time_start')[0].date_time_start.astimezone(tz).date()

        self.set_table_data(target_date)
 

    def set_table_data(self, date):
        self.target_date_display.setText(date.strftime('%Y-%m-%d'))
        
        # Get all sessions on that date
        previous_sessions = runner.models.Session.objects.filter(
            date_time_start__date=date).order_by('date_time_start')        
        
        # Fill out the new daily plan to look just like the old one
        box_l = sorted([box.name for box in runner.models.Box.objects.all()])
        mouse_l = sorted([mouse.name for mouse in runner.models.Mouse.objects.all()])
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

        #self.daily_plan_table.setRowCount(len(previous_sessions) + 1)
        self.daily_plan_table.setRowCount(len(previous_sessions))
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
            self.daily_plan_table.setItem(nrow, 2, QTableWidgetItem(''))

            # Board, combo box
            qcb = create_combo_box(board_l, choice=session.board.name)
            self.daily_plan_table.setCellWidget(nrow, 3, qcb)
            self.daily_plan_table.setItem(nrow, 3, QTableWidgetItem(''))
            
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
            self.daily_plan_table.setItem(nrow, 6, QTableWidgetItem(''))
            
            # New perf, read only
            item = QTableWidgetItem('-')
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.daily_plan_table.setItem(nrow, 7, item)
            
            # New pipe, text box
            item = QTableWidgetItem('-')
            self.daily_plan_table.setItem(nrow, 8, item)

            item = QTableWidgetItem('')
            self.daily_plan_table.setItem(nrow, 9, item)
            
            # Remove, button
            rmvButton = QPushButton('Remove')
            self.daily_plan_table.setCellWidget(nrow, 10, rmvButton)
            self.daily_plan_table.setItem(nrow, 10, QTableWidgetItem(''))
            #Necessary to keep track of changing index
            index = QPersistentModelIndex(self.daily_plan_table.model().index(nrow, 10))

            rmvButton.clicked.connect(functools.partial(self.removeRow, index))

    def removeRow(self, index):
        self.daily_plan_table.removeRow(index.row())
        #Replace vertical number labels
        self.daily_plan_table.setVerticalHeaderLabels([str(i+1) for i in
            range(self.daily_plan_table.rowCount())])

    def addRow(self):
        index = self.daily_plan_table.rowCount()
        self.daily_plan_table.insertRow(index)

        box_l = sorted([box.name for box in runner.models.Box.objects.all()])
        mouse_l = sorted([mouse.name for mouse in runner.models.Mouse.objects.all()])
        board_l = sorted([board.name for board in runner.models.Board.objects.all()])
         # Box, combo box
        qcb = create_combo_box(box_l)
        self.daily_plan_table.setCellWidget(index, 2, qcb)
        self.daily_plan_table.setItem(index, 2, QTableWidgetItem(''))

        # Board, combo box
        qcb = create_combo_box(board_l)
        self.daily_plan_table.setCellWidget(index, 3, qcb)
        self.daily_plan_table.setItem(index, 3, QTableWidgetItem(''))

        # Previous pipe, read only
        text = ''
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
        self.daily_plan_table.setItem(index, 4, item)
        
        # Previous perf, read only
        text = ''
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
        self.daily_plan_table.setItem(index, 5, item)

        # Start, button
        qb = QPushButton('Start')
        #~ qb.setCheckable(True)
        qb.clicked.connect(functools.partial(self.start_session2, qb))
        self.daily_plan_table.setCellWidget(index, 6, qb)
        
        # New perf, read only
        item = QTableWidgetItem('-')
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
        self.daily_plan_table.setItem(index, 7, item)
        
        # New pipe, text box
        item = QTableWidgetItem('-')
        self.daily_plan_table.setItem(index, 8, item)
        
        item = QTableWidgetItem('')
        self.daily_plan_table.setItem(index, 9, item)
        # Remove, button
        rmvButton = QPushButton('Remove')
        self.daily_plan_table.setCellWidget(index, 10, rmvButton)
        self.daily_plan_table.setItem(index, 10, QTableWidgetItem(''))
        #Necessary to keep track of changing index
        persindex = QPersistentModelIndex(self.daily_plan_table.model().index(index, 10))

        rmvButton.clicked.connect(functools.partial(self.removeRow, persindex))


    def setRowColor(self, row, color):
        for col in range(self.daily_plan_table.columnCount()):
            self.daily_plan_table.item(row, col).setBackground(QBrush(QColor(color)))


    def start_session(self, row):
        """Collect data from row and pass to start session"""
        #self.daily_plan_table.setCurrentCell(row, 6)

        mouse=str(self.daily_plan_table.item(row, 0).text())
        board=str(self.daily_plan_table.cellWidget(row, 3).currentText())
        box=str(self.daily_plan_table.cellWidget(row, 2).currentText())


        #Use threading so process doesn't interrupt rest of gui
        proc = threading.Thread(target=self.call_external, args=(mouse, board, box, row))
        proc.start()

#        call_external(
#            mouse=str(self.daily_plan_table.item(row, 0).text()),
#            board=str(self.daily_plan_table.cellWidget(row, 3).currentText()),
#            box=str(self.daily_plan_table.cellWidget(row, 2).currentText()),
#        )


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


    def call_external(self, mouse, board, box, row):
      print mouse, board, box

    # Create a place to keep sandboxes
      sandbox_root = os.path.expanduser('~/sandbox_root')
      if not os.path.exists(sandbox_root):
          os.mkdir(sandbox_root)

      user_input = {'mouse': mouse, 'board': board, 'box': box}
      sandbox_paths = ArduFSM.Runner.Sandbox.create_sandbox(user_input, sandbox_root)

      #Green indicates process is running
      self.setRowColor(row, 'green')

      #Track successful compilation
      success = True
      try:
          ArduFSM.Runner.start_runner_cli.main(mouse=mouse, board=board, box=box, sandbox_paths=sandbox_paths)
      except :
          #Yellow means arduino code didn't compile?
          self.setRowColor(row, 'yellow')
          success = False
          raise 
      finally:
          if success:
              sandbox_path = sandbox_paths['sandbox']
              saved_filename = sandbox_path + '-saved'

              #Look for saved version of sandbox every 4 seconds
              while not os.path.exists(saved_filename):
                  time.sleep(4)

              #Red indicates process completion
              self.setRowColor(row, 'red')

              print "Session recorded in {} completed".format(sandbox_path)


    
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
    
    def save_notes(self):
        today = datetime.date.today().strftime('%Y-%m-%d')
        notesfile = open("./notes/notes-%s" % (today), "w")
        text = self.notesWindow.toPlainText()
        notesfile.write(text)

        notesfile.close()


        self.write_table_to_csv()

    def read_notes(self):
        today = datetime.date.today().strftime('%Y-%m-%d')
        path = "./notes/notes-%s" % (today)
        if os.path.exists(path):
            self.notesWindow.setPlainText(open(path, 'r').read())

    def write_table_to_csv(self):
        
        today = datetime.date.today().strftime('%Y-%m-%d')
        path = "./history/history-%s.csv" % (today)

        restricted_columns = [6, 10]
        with open(path, 'w') as stream:
            writer = csv.writer(stream)
            
            header = []
            for col in range(self.daily_plan_table.columnCount()):
                if col not in restricted_columns:
                    colHeader = self.daily_plan_table.horizontalHeaderItem(col)
                    header.append(colHeader.text())
            
            writer.writerow(header)


            for row in range(self.daily_plan_table.rowCount()):
                rowdata = []
                for col in range(self.daily_plan_table.columnCount()):
                    if col not in restricted_columns:

                        widget = self.daily_plan_table.cellWidget(row, col)
                        if widget:
                            text = widget.currentText()
                        else:
                            item = self.daily_plan_table.item(row, col)
                            text = item.text()

                        rowdata.append(text)

                writer.writerow(rowdata)
    




class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        app = QtGui.QApplication(sys.argv)
        window = MyApp()
        window.show()
        sys.exit(app.exec_())



class DateDialog(QDialog):
    def __init__(self, startDate, parent = None):
        super(DateDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        # nice widget for editing the date
        self.dateEdit = QDateEdit(self)
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDate(startDate)
        self.dateEdit.setMaximumDate(QDate.currentDate())
        layout.addWidget(self.dateEdit)

        # OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        

    # get current date and time from the dialog
    def getSelectedDate(self):
        return self.dateEdit.date()

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getDate(startDate, parent = None):
        dialog = DateDialog(startDate, parent)
        result = dialog.exec_()
        date = dialog.getSelectedDate()
        return (date, result == QDialog.Accepted)


if __name__ == "__main__":
    ## Get the most recent stuff from runner
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
