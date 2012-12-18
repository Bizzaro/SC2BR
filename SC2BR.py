#requires 32-bit python 2.7. works on 64-bit OS.

import wx
import wx.grid
import csv
import os
import time
import urllib2
import pygame
import atexit
import pythoncom, pyHook


FREQ = 44100    # same as audio CD
BITSIZE = -16   # unsigned 16 bit
CHANNELS = 1    # 1 == mono, 2 == stereo
BUFFER = 1024   # audi buffer size in no. of samples
FRAMERATE = 30  # how often to check if playback has finished


pygame.mixer.pre_init(16000,-16,2,2048)
pygame.init()

class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="SC2 Build Reader")

        def OnKeyboardEvent(event):
            if event.KeyID == 123:
                self.onPlay(True)
                # return True to pass the event to other handlers
            return True

        # create a hook manager
        hm = pyHook.HookManager()
        # watch for all mouse events
        hm.KeyDown = OnKeyboardEvent
        # set the hook
        hm.HookKeyboard()
        # wait forever
        #pythoncom.PumpMessages()

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        #TOOLBAR---------------------------------------------------------------------------------------------------------------
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((16,16))

        new_icon = wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR, (16,16))
        self.newTool = self.toolbar.AddSimpleTool(wx.ID_ANY, new_icon, "New", "Create a new build")
        self.Bind(wx.EVT_MENU, self.onNew, self.newTool)

        save_icon = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, (16,16))
        self.saveTool = self.toolbar.AddSimpleTool(wx.ID_ANY, save_icon, "Save", "Saves the current build")
        self.Bind(wx.EVT_MENU, self.onSave, self.saveTool)

        open_icon = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, (16,16))
        self.openTool = self.toolbar.AddSimpleTool(wx.ID_ANY, open_icon, "Open", "Opens a saved build")
        self.Bind(wx.EVT_MENU, self.onOpen, self.openTool)

        clear_icon = wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_TOOLBAR, (16,16))
        self.clearTool = self.toolbar.AddSimpleTool(wx.ID_ANY, clear_icon, "Clear", "Clears current build")
        self.Bind(wx.EVT_MENU, self.onClear, self.clearTool)

        self.toolbar.AddSeparator()

        play_icon = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR, (16,16))
        self.playTool = self.toolbar.AddSimpleTool(wx.ID_ANY, play_icon, "Play", "Plays current build")
        self.Bind(wx.EVT_MENU, self.onPlay, self.playTool)
        #self.Bind(wx.EVT_CHAR_HOOK,self.onPlay)

        #stop_icon = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_TOOLBAR, (16,16))
        #self.stopTool = self.toolbar.AddSimpleTool(wx.ID_ANY, stop_icon, "Stop", "Stops current build")
        #self.Bind(wx.EVT_MENU, self.onStop, self.stopTool)

        self.toolbar.Realize()

        #STATUSBAR-------------------------------------------------------------------------------------------------------------
        self.statusbar = self.CreateStatusBar()

        #GRID------------------------------------------------------------------------------------------------------------------
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(30,3)
        self.grid.SetRowLabelSize(30)
        self.grid.SetColLabelSize(20)
        self.grid.SetDefaultColSize(200)
        self.grid.SetColSize(0,50)
        self.grid.SetColSize(1,50)
        self.grid.DisableDragRowSize()
        self.grid.DisableDragColSize()
        self.grid.DisableDragGridSize()
        self.grid.SetColLabelValue(0,'Minute')
        self.grid.SetColLabelValue(1,'Second')
        self.grid.SetColLabelValue(2,'Event')
        self.grid.Validate()
        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.onCellChange)

        self.sizer.Add(self.grid, 0, wx.ALL, 0)
        self.grid.SetSizer(self.sizer)
        self.sizer.Fit(self)


        # Creates a list containing 5 lists initialized to 0
        self.importMatrix = []
        self.matrix = [['' for x in xrange(3)] for x in xrange(30)]
        self.timeMatrix = [['' for x in xrange(2)] for x in xrange(30)]
        self.error = 0
        self.openedFile = None
        self.dirname = None
        self.newFile = None
    #DEFINITIONS-----------------------------------------------------------------------------------------------------------
    def onNew(self, evt):
        self.openedFile = None
        self.matrix = [[0 for x in xrange(3)] for x in xrange(30)]
        self.grid.ClearGrid()
        rows = range(30)
        cols = range(2)
        for row in rows:
            for col in cols:
                self.grid.SetCellBackgroundColour(row,col,wx.WHITE)

    def onSave(self, evt):
        if self.openedFile is None: #newfile
            dlg = wx.FileDialog(
                self, message="Save file as ...",
                wildcard="CSV files (*.csv)|*.csv",
                defaultFile='', style=wx.SAVE
            )
            if dlg.ShowModal() == wx.ID_OK:
                self.newFile = dlg.GetPath()
                self.openedFile = dlg.GetPath()
            dlg.Destroy()

            csvfile = open(self.newFile,"wb")
            outFile = csv.writer(csvfile, delimiter=',')
            for row in range(30):
                outFile.writerow(self.matrix[row])
            csvfile.close()
            self.statusbar.SetStatusText('File Saved!')
        else: #saving over existing opened file
            csvfile = open(self.openedFile,"wb")
            outFile = csv.writer(csvfile, delimiter=',')
            for row in range(30):
                outFile.writerow(self.matrix[row])
            csvfile.close()
            self.statusbar.SetStatusText('File saved!')

    def onOpen(self, evt):

        dialog = wx.FileDialog(None,'Choose a file',os.getcwd(),wildcard="CSV files (*.csv)|*.csv", defaultFile="",style=wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.openedFile = dialog.GetPath()
        dialog.Destroy()
        fileName = os.path.splitext(os.path.basename(self.openedFile))[0]
        TestFrame.SetTitle(self,'SC2 Build Reader: %s' % fileName)

        csvReader = csv.reader(open(self.openedFile, 'rb'), delimiter=',', quotechar='|')

        for row in csvReader:
            self.importMatrix.append(row)

        rows = range(30)
        cols = range(3)
        for row in rows:
            for col in cols:
                self.grid.SetCellValue(row,col,self.importMatrix[row][col])

        self.importMatrix = []

    def onPlay(self,evt):

        #pygame.mixer.pre_init(16000,-16,2,2048)
        #pygame.init()

        rows = range(30)
        for row in rows:
            try:
                self.timeMatrix[row][0] = float(.7*(int(self.grid.GetCellValue(row,0))*60 + int(self.grid.GetCellValue(row,1))))
                self.timeMatrix[row][1] = str(self.grid.GetCellValue(row,2))
            except ValueError:
                self.timeMatrix[row][0] = ''

        #print(self.timeMatrix)

        try:
            time.sleep(float(self.timeMatrix[0][0]))
            text = self.timeMatrix[0][1]


            if len(text) >= 100:
                text = text[:100]

            google_translate_url = 'http://translate.google.com/translate_tts'
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0)')]


            response = opener.open(google_translate_url+'?q='+text.replace(' ','%20')+'&tl=en')
            with open(str('0')+'speech_google.mp3','wb') as ofp:
                ofp.write(response.read())
            clip = os.path.abspath(str('0')+'speech_google.mp3')

            #pygame.init()
            pygame.mixer.music.load(clip)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except ValueError:
            pass


        rows = range(1,30)
        for row in rows:
            try:
                time.sleep(float(self.timeMatrix[row][0])- float(self.timeMatrix[row-1][0]))
                text = self.timeMatrix[row][1]

                if len(text) >= 100:
                    text = text[:100]

                google_translate_url = 'http://translate.google.com/translate_tts'
                opener = urllib2.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0)')]


                response = opener.open(google_translate_url+'?q='+text.replace(' ','%20')+'&tl=en')
                with open(str(row)+'speech_google.mp3','wb') as ofp:
                    ofp.write(response.read())
                clip = os.path.abspath(str(row)+'speech_google.mp3')

                #pygame.init()
                pygame.mixer.music.load(clip)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            except ValueError:
                pass

    def onClear(self, evt):
        self.grid.ClearGrid()
        self.matrix = [[0 for x in xrange(3)] for x in xrange(30)]
        rows = range(30)
        cols = range(2)
        for row in rows:
            for col in cols:
                self.grid.SetCellBackgroundColour(row,col,wx.WHITE)


    def onCellChange(self, evt):
        x = evt.GetRow()
        y = evt.GetCol()
        value = self.grid.GetCellValue(x,y)


        if y < 2 and value != '':
            try:
                value = int(value)
                self.matrix[x][y] = int(value)
                if self.error > 0:
                    self.error -= 1
                self.grid.SetCellBackgroundColour(x,y,wx.WHITE)
            except ValueError:
                self.error += 1
                self.grid.SetCellValue(x,y,'')
                self.grid.SetCellBackgroundColour(x,y,wx.RED)
        else:
            self.matrix[x][y] = value

        if self.error != 0:
            self.statusbar.SetStatusText('Must enter a number value in red cells above!')
        else:
            self.statusbar.SetStatusText('')

            #def onKeyPress(self,evt):
            #    if evt.GetKeyCode() == wx.WXK_F12:
            #        self.onPlay(self)
            #    else:
            #        evt.Skip()

def onQuit():
    pygame.mixer.quit()
    filelist = [ f for f in os.listdir(".") if f.endswith(".mp3") ]
    for f in filelist:
        os.remove(f)

atexit.register(onQuit)

if __name__ == '__main__':
    app = wx.App()
    frame = TestFrame()
    frame.Show()
    app.MainLoop()
