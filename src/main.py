import sys, os
try:
    sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
except Exception as e:
    print("No need to remove ROS stuff from path")

import argparse

parser = argparse.ArgumentParser(description='Hazard video labelling tool')
parser.add_argument('--filepath', metavar='file(s)', type=str, nargs='+', default=None,
help='filepath(s) of videos to be analysed (provide absolute paths)')
parser.add_argument('--folder', metavar='folder', type=str, default=None,
help='path to folder containing videos (provide absolute path)')
parser.add_argument('--dest', metavar='destination', type=str, nargs=1, default='.',
help='path to desired output destination (default: where this script is)')

args = parser.parse_args()

FILEPATH = args.filepath
FOLDER = args.folder
DEST = args.dest

ACCEPTABLE_EXT = ['mp4', 'MP4', 'mov', 'MOV', 'wmv', 'avi', 'WMV', 'AVI', 'mpeg', \
                    'mkv', 'mpg', 'm4v']

from pyforms.basewidget import BaseWidget
from pyforms.controls   import ControlFile
from pyforms.controls   import ControlText
from pyforms.controls   import ControlSlider
from pyforms.controls   import ControlPlayer
from pyforms.controls   import ControlButton
from pyforms.controls   import ControlEventTimeline
from pyforms.controls   import ControlDockWidget
from pyforms.controls   import ControlProgress


from AnyQt import QtCore

class VideoWindow(BaseWidget):

    def __init__(self, *args, **kwargs):
        super().__init__('Hazard Labelling')

        self._args = {  "filepath": FILEPATH,
                        "folder": FOLDER,
                        "dest": DEST
                        }

        self.set_margin(10)

        #Definition of the forms fields
        self._videofile = ControlFile('Video')
        self._hazardbutton = ControlButton('Hazard')
        self._next = ControlButton('Next Video')
        self._save_data = ControlButton('Save labels')
        self._player = ControlPlayer('Player')
        self._timeline = ControlEventTimeline('Timeline')
        self._panel = ControlDockWidget(label='Timeline', side='bottom', margin=10)
        self._status = ControlText('Status')
        self._file_list = []

        if self._args["folder"] is None:
            if self._args["filepath"] is not None:
                self._file_list = self._args["filepath"]
        elif self._args["folder"] is not None:
            if os.path.isdir(self._args["folder"]):
                self.__updateStatus("Source folder found at: {}".format(self._args["folder"]))
                print("Scanning folder and all subfolders... {}".format(self._args["folder"]))
                count = 0
                for (dirpath, dirnames, filenames) in os.walk(self._args["folder"]):
                    path = []
                    for f in filenames:
                        if f.rsplit('.')[-1] in ACCEPTABLE_EXT:
                            count += 1
                            path.append(dirpath + "/" + f)
                    self._file_list.extend(path)
                    if count % 100 == 0:
                        print("Found {} files...".format(count))
                print("Scan complete, found {} acceptable files".format(count))
        self._video_count = len(self._file_list)
        self._progress = ControlProgress(label="Video %p of " + str(self._video_count), defaultValue=1, min=1, max=self._video_count)

        self._hazard_counter = 0
        self._current_video = 0

        #Define function calls on button presses
        self._videofile.changed_event = self.__videoFileSelectionEvent
        self._hazardbutton.value = self.__labelHazard
        self._next.value = self.__nextVideo
        self._save_data.value = self.__saveData
        self._panel.value = self._timeline
        self._progress.value = self._current_video + 1

        #Define events
        self._player.process_frame_event = self.__processFrame
        self._player.click_event = self.__clickEvent
        self._player.key_release_event = self.__tagEvent

        #Define the organization of the Form Controls
        self._formset = [
            '_player',
            # '_hazardbutton',
            '_panel',
            ('_videofile', '_next'),
            ('_status', '_save_data'),
            '_progress'
            ]

        self._video_loaded = False

        try:
            self.__videoFileSelect(self._file_list[self._current_video])
        except Exception as e:
            self.__updateStatus("Select video...")

        self._hazard_default_duration = 0

    def __videoFileSelect(self, filepath):
        try:
            self._videofile.value = str(filepath)
            self._player.value = self._videofile.value
            self._player.refresh()
            self._player.update_frame()
            # Hazard set to occur for 60 frames upon flagging
            self._hazard_default_duration = int(self._player.fps * 2)
            self._video_loaded = True
        except Exception as e:
            self.__updateStatus("Unable to select video")

    def __videoFileSelectionEvent(self):
        """
        When the videofile is selected instantiate the video in the player
        """
        try:
            self._player.value = self._videofile.value
            # Hazard set to occur for 60 frames upon flagging
            self._hazard_default_duration = int(self._player.fps * 2)
            self._video_loaded = True
        except Exception as e:
            self.__updateStatus("No video selected")

    def __nextVideo(self):
        if self._current_video >= (self._video_count - 1):
            self.__updateStatus("No more videos")
        else:
            self._current_video += 1
            self.__reset()
            self.__videoFileSelect(self._file_list[self._current_video])
            self._progress.value = self._current_video + 1

    def __reset(self):
        self._player.stop()
        self.__saveData()
        print("saving on reset")
        self._timeline.clean()
        self.__updateStatus("")

    def __processFrame(self, frame):
        """
        Do some processing to the frame and return the result frame
        """
        return frame

    def __clickEvent(self, click_event, x, y):
        self.__labelHazard()

    def __tagEvent(self, event):
        """
        Label hazard using Enter key
        """
        key = event.key()

        # QtCore.Qt.Key_Enter gives wrong value (at least on test PC) for Enter key
        # Desired == 16777221, actual == 16777220

        key_id = 16777220

        if event.key() == key_id:
            self.__labelHazard()

    def __addFlag(self, value):
        self._timeline.add_period(value)

    def __labelHazard(self):
        if self._video_loaded:
            if self._player.video_index > (self._player.max - self._hazard_default_duration):
                flag_duration = round(self._player.max - self._player.video_index)
            else:
                flag_duration = self._hazard_default_duration
            try:
                self._hazard_counter += 1
                self.__updateStatus("Hazard flagged! | Frame: {} Timestamp: {}".format(self._player.video_index,
                                round(self._player.video_index/self._player.fps, 3)))
                self.__addFlag((self._player.video_index, self._player.video_index + flag_duration, str(self._hazard_counter)))
            except Exception as e:
                try:
                    self._player.refresh()
                    self.__updateStatus("Hazard flagged! | Frame: {} Timestamp: {}".format(self._player.video_index,
                                    round(self._player.video_index/self._player.fps, 3)))
                except Exception as e:
                    self.__updateStatus("Unable to label, exiting...")
                    sys.exit(0)

    def __saveData(self):
        self._timeline.export_csv_file(self._videofile.value + "_hazard.csv")
        self.__updateStatus("Saving {} to {}".format(self._videofile.value + "_hazard.csv", self._args["dest"]))

    def __updateStatus(self, msg):
        self._status.value = str(msg)


if __name__ == '__main__':

    from pyforms import start_app
    from PyQt5.QtWidgets import QApplication

    app_unused = QApplication([])
    screen_resolution = app_unused.desktop().screenGeometry()
    width, height = screen_resolution.width(), screen_resolution.height()

    start_app(VideoWindow, geometry=(width/4, height/4, width/2, height/2))
