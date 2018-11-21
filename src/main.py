import sys
try:
    sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
except Exception as e:
    print("No need to remove ROS stuff from path")

import argparse

parser = argparse.ArgumentParser(description='Hazard video labelling tool')
parser.add_argument('--filepath', metavar='file(s)', type=str, nargs='+', default=None,
help='filepath(s) of videos to be analysed (provide absolute paths)')
parser.add_argument('--folder', metavar='folder', type=str, nargs=1, default=None,
help='path to folder containing videos (provide absolute path)')
parser.add_argument('--dest', metavar='destination', type=str, nargs=1, default='.',
help='path to desired output destination (default: where this script is)')

args = parser.parse_args()

FILEPATH = args.filepath
FOLDER = args.folder
DEST = args.dest


from pyforms.basewidget import BaseWidget
from pyforms.controls   import ControlFile
from pyforms.controls   import ControlText
from pyforms.controls   import ControlSlider
from pyforms.controls   import ControlPlayer
from pyforms.controls   import ControlButton

class VideoWindow(BaseWidget):

    def __init__(self, *args, **kwargs):
        super().__init__('Hazard Labelling')

        self._args = {  "filepath": FILEPATH,
                        "folder": FOLDER,
                        "dest": DEST
                        }

        self.set_margin(10)

        #Definition of the forms fields
        self._videofile  = ControlFile('Video')
        self._hazardbutton = ControlButton('Hazard')
        self._player     = ControlPlayer('Player')

        #Define function calls on button presses
        self._videofile.changed_event = self.__videoFileSelectionEvent
        self._hazardbutton.value = self.__labelHazard

        #Define events
        self._player.process_frame_event = self.__process_frame
        self._player.click_event = self.__clickEvent

        #Define the organization of the Form Controls
        self._formset = [
            ('_videofile'),
            '_player',
            '_hazardbutton'
            ]

        if self._args["folder"] is None:
            if self._args["filepath"] is not None:
                self.__videoFileSelect(self._args["filepath"][0])

    def __videoFileSelect(self, filepath):
        self._videofile.value = str(filepath)
        self._player.value = self._videofile.value
        self._player.refresh()
        self._player.update_frame()

    def __videoFileSelectionEvent(self):
        """
        When the videofile is selected instantiate the video in the player
        """
        self._player.value = self._videofile.value

    def __process_frame(self, frame):
        """
        Do some processing to the frame and return the result frame
        """
        return frame

    def __clickEvent(self, click_event, x, y):
        self.__labelHazard()

    def __labelHazard(self):
        try:
            print("Hazard flagged! | Frame: {} Timestamp: {}".format(self._player.video_index,
                            round(self._player.video_index/self._player.fps, 3)))
        except Exception as e:
            try:
                self._player.refresh()
                print("Hazard flagged! | Frame: {} Timestamp: {}".format(self._player.video_index,
                                round(self._player.video_index/self._player.fps, 3)))
            except Exception as e:
                print("Unable to label, exiting...")
                sys.exit(0)



if __name__ == '__main__':

    from pyforms import start_app

    start_app(VideoWindow)
