# coding=utf-8
# __author__ = 'Mario Romera Fernández'

import os
import wave
import operator
import datetime
from subprocess import Popen, PIPE
import getpass
import numpy as np
from dejavuCAPTOR import Dejavu
from dejavuCAPTOR.recognize import AudioRecognizer
import wx
import wx.lib.inspection
import wx.media
import wx.lib.buttons as buttons
import MySQLdb
import wx.lib.agw.gradientbutton as GB
import wx.lib.agw.aquabutton as AB
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot
from matplotlib import ticker
import wx.lib.agw.pybusyinfo as PBI
from pocketsphinx import *
import detector_bloques
import VistaSpot
from dynamicListComboBox import DynamicListComboBox
from anuncioDialog import AnuncioDialog

# VARIABLES GLOBALES
# Cursores para BBDD
# cur -> cursor a la BBDD MySQL (fingerprints, ocurrencias, etc)
# curAS400 -> cursor a la BBDD AS400

UMBRAL = int(3864 / 2) * 0.05  # sacado de proceso_stream
dirName = os.path.dirname(os.path.abspath(__file__))
bitmapDir = os.path.join(dirName, 'bitmaps')
emisora_cinta = 0

db = None
if getpass.getuser() == "Mario":
    rutaanuncios = "C:/CaptorRadio/anuncios"

    db = MySQLdb.connect(host="192.168.2.170",
                         user="root",
                         passwd="infoadex",
                         db="captor",
                         use_unicode=True,
                         charset="utf8",
                         init_command='SET NAMES UTF8')
    config = {
        "database": {
            "host": "192.168.2.170",
            "user": "root",
            "passwd": "infoadex",
            "db": "captor",
            "use_unicode": True,
            "charset": 'utf8',
            "init_command": 'SET NAMES UTF8'
        },
        "database_type": "mysql"
    }
    djv = Dejavu(config)

elif getpass.getuser() == "plr":
    rutaanuncios = 'C:\Users\plr\\'
    config = {
        "database": {
            "host": "localhost",
            "user": "root",
            "passwd": "12345",
            "db": "captor",
        },
        "database_type": "mysql"
    }
    djv = Dejavu(config)
    hmdir = 'D:\i+d\Captor\\reconvoz\\voxforge-es-0.2\model_parameters/voxforge_es_sphinx.cd_ptm_3000'
    lmdir = 'D:\i+d\Captor\\reconvoz\\voxforge-es-0.2\etc\\voxforge_es_sphinx.transcription.test.lm'
    dictd = 'D:\i+d\Captor\\reconvoz\\voxforge-es-0.2\etc\\voxforge_es_sphinx.dic'

    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd="12345",
                         db="captor")

else:
    print "usuario != Mario % plr"
    db = MySQLdb.connect(host="192.168.2.55",
                         user="root",
                         passwd="InfoAdexEdasnet12345",
                         db="captor",
                         use_unicode=True,
                         charset="utf8",
                         init_command='SET NAMES UTF8')
    config = {
        "database": {
            "host": "192.168.2.55",
            "user": "root",
            "passwd": "InfoAdexEdasnet12345",
            "db": "captor",
            "use_unicode": True,
            "charset": 'utf8',
            "init_command": 'SET NAMES UTF8'
        },
        "database_type": "mysql"
    }
    djv = Dejavu(config)

cursor = db.cursor(MySQLdb.cursors.DictCursor)
cur = db.cursor()
bloques_ordenados = []
datos_anuncios = []
usuario = None

print db.get_host_info()


# cnxn = pyodbc.connect('DSN=AS400;SYSTEM=192.168.1.101;UID=INFOADEX;PWD=INFOADEX')
# cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=servidor;DATABASE=InfoAdex;UID=mario;PWD=edasnet')
# curAS400 = cnxn.cursor()
######################################################################################################################

class MediaPanel(wx.Panel):
    """" clase llamada por MediaFrame (padre)"""

    def __init__(self, parent):  # , grafica):
        """Constructor"""
        wx.Panel.__init__(self, parent, style=wx.WANTS_CHARS)

        # Para el menu de archivos y el modelo a usar por defecto
        sp = wx.StandardPaths.Get()
        self.currentFolder = sp.GetDocumentsDir()
        self.currentFile = ''
        self.s = None
        self.graf = GraficaPanel(self)
        self.menuanuncios = VistaSpot.PanelAnuncios(self)
        # contador de tiempo inicial
        self.marcador = '00:00:00'
        self.inicio_grabacion = datetime.datetime(2000, 1, 1, 0, 0)

        # parent y creacion de menu y apariencia
        self.frame = parent
        self.SetBackgroundColour("PALE GREEN")
        self.currentVolume = 50
        self.busy = None
        self.createMenu()
        self.layoutControls()

        self.Bind(wx.EVT_SIZE, self.onSize)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer)
        self.timer.Start(100)

        self.Bind(wx.EVT_CHAR_HOOK, self.onArrowKey)
        self.anuncioseleccionado = {'inicio': '', 'final': '', 'bloque': '', 'marca': '', 'modelo': ''}
        self.cinta = dict()

    def layoutControls(self):
        """
        Creacion de dispositivos de la aplicacion
        """

        try:
            self.mediaPlayer = wx.media.MediaCtrl(self, style=wx.RAISED_BORDER)
        except NotImplementedError:
            self.Destroy()
            raise

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.barra_1h_hora_sizer = wx.BoxSizer(wx.VERTICAL)
        self.barra_1h_hora_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.barra_1h_hora_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.barra_1h_hora_sizer.Add(self.barra_1h_hora_sizer1, 0, wx.EXPAND)
        self.barra_1h_hora_sizer.Add(self.barra_1h_hora_sizer2, 0, wx.EXPAND)
        self.audioSizer = self.buildAudioBar()

        mainSizer.AddSpacer(10)
        mainSizer.Add(self.audioSizer, -1, wx.CENTER, 1)
        mainSizer.AddSpacer(15)
        mainSizer.Add(self.barra_1h_hora_sizer, 0, wx.RIGHT | wx.LEFT | wx.TOP | wx.EXPAND, 1)
        mainSizer.AddSpacer(30)
        mainSizer.Add(self.menuanuncios, -1, wx.EXPAND, 1)
        mainSizer.Add(self.graf, -1, wx.EXPAND, 1)
        self.SetSizerAndFit(mainSizer)

        self.Layout()

    def extraer_tiempo_grabacion(self, archivo):
        """
        :rtype : datetime.datetime
        :param archivo: nombre del archivo
        :return: datetime.datetime
        """
        try:
            nombre = os.path.splitext(os.path.basename(archivo))[0]
            anho = int(nombre[0:4])
            mes = int(nombre[4:6])
            dia = int(nombre[6:8])
            hora = int(nombre[8:10])
            minuto = int(nombre[10:12])
            segundo = int(nombre[12:14])
            milisegundo = 0
            return datetime.datetime(anho, mes, dia, hora, minuto, segundo, milisegundo)
        except:
            pass
            return -1

    def build_1h_bar(self):
        """
        Construye las barras de 1 hora
        """

        cont = self.inicio_grabacion

        self.lista1 = []
        self.lista2 = []
        bloque = False

        print 'bloques'
        print bloques_ordenados
        if bloques_ordenados:
            if int((bloques_ordenados[0][1][0] - cont).total_seconds()) == 0:
                bloque = True

            for i in bloques_ordenados:
                # control de que es un bloque
                print cont
                if cont < self.inicio_grabacion + datetime.timedelta(seconds=1800):

                    self.lista1.append((cont, int((i[1][0] - cont).total_seconds()), bloque))
                    bloque = not bloque
                    if i[1][0] < self.inicio_grabacion + datetime.timedelta(seconds=1800):
                        self.lista1.append((i[1][0], int((i[1][1] - i[1][0]).total_seconds()), bloque))
                    else:
                        self.lista2.append((i[1][0], int((i[1][1] - i[1][0]).total_seconds()), bloque))
                    bloque = not bloque
                else:
                    self.lista2.append((cont, int((i[1][0] - cont).total_seconds()), bloque))
                    bloque = not bloque
                    self.lista2.append((i[1][0], int((i[1][1] - i[1][0]).total_seconds()), bloque))
                    bloque = not bloque
                cont = cont + (i[1][1] - cont)

            if (self.inicio_grabacion + datetime.timedelta(seconds=3599) - cont).total_seconds() > 1:
                self.lista2.append((bloques_ordenados[-1][1][1], int(
                    (self.inicio_grabacion + datetime.timedelta(seconds=3599) - cont).total_seconds()), bloque))

        else:

            self.lista1.append((cont, 3600, False))
        print "lista1:{}".format(self.lista1)
        print "lista2:{}".format(self.lista2)

        for child in self.barra_1h_hora_sizer.GetChildren():
            child.DeleteWindows()

        indexfinal = 0
        # con botones
        for index, i in enumerate(self.lista1):

            btn = wx.Button(self, label=i[0].strftime("%H:%M:%S"), size=(i[1] / 1800, wx.Button_GetDefaultSize()[1]),
                            name=str(indexfinal))
            if i[2]:
                btn.SetBackgroundColour('green')
            else:
                btn.SetBackgroundColour('blue')
            self.barra_1h_hora_sizer1.Add(btn, i[1])
            btn.Bind(wx.EVT_BUTTON, self.onBloque)
            indexfinal = index + 1

        if self.lista2:
            for index, i in enumerate(self.lista2):

                btn = wx.Button(self, label=i[0].strftime("%H:%M:%S"),
                                size=(i[1] / 1800, wx.Button_GetDefaultSize()[1]), name=str(indexfinal))
                if i[2]:
                    btn.SetBackgroundColour('green')
                else:
                    btn.SetBackgroundColour('blue')
                self.barra_1h_hora_sizer2.Add(btn, i[1])
                btn.Bind(wx.EVT_BUTTON, self.onBloque)
                indexfinal += 1

        self.Layout()
        self.frame.Fit()

    def buildAudioBar(self):
        """
        Construye los controladores de audio
        """
        audioBarSizer = wx.BoxSizer(wx.HORIZONTAL)

        # contador
        self.trackCounter = wx.StaticText(self, label=self.marcador)
        font1 = wx.Font(22, wx.DECORATIVE, wx.ITALIC, wx.NORMAL)
        self.trackCounter.SetFont(font1)
        audioBarSizer.Add(self.trackCounter, 0, wx.LEFT | wx.CENTER, 20)

        # create play/pause toggle button
        img = wx.Bitmap(os.path.join(bitmapDir, "player_play.png"))
        self.playPauseBtn = buttons.GenBitmapToggleButton(self, bitmap=img, name="play")
        self.playPauseBtn.Enable(False)

        img = wx.Bitmap(os.path.join(bitmapDir, "player_pause.png"))
        self.playPauseBtn.SetBitmapSelected(img)
        # self.playPauseBtn.SetInitialSize()

        self.playPauseBtn.Bind(wx.EVT_BUTTON, self.onPlay)
        # self.playPauseBtn.Bind(wx.EVT_KEY_DOWN, self.onPlayKey)
        audioBarSizer.Add(self.playPauseBtn, 0, wx.LEFT | wx.CENTER, 35)

        btnData = [{'bitmap': 'player_prev2.png', 'handler': self.onPrev2,
                    'name': 'prev2'}, {'bitmap': 'player_prev.png', 'handler': self.onPrev,
                                       'name': 'prev'}, {'bitmap': 'player_stop.png',
                                                         'handler': self.onStop, 'name': 'stop'},
                   {'bitmap': 'player_next.png',
                    'handler': self.onNext, 'name': 'next'}, {'bitmap': 'player_next2.png',
                                                              'handler': self.onNext2, 'name': 'next2'}]
        for btn in btnData:
            self.buildBtn(btn, audioBarSizer)

        # volumen de audio
        self.volumeCtrl = wx.Slider(self, style=wx.SL_HORIZONTAL, name='VOL')
        self.volumeCtrl.SetRange(0, 100)
        self.volumeCtrl.SetValue(self.currentVolume)
        self.volumeCtrl.Bind(wx.EVT_SLIDER, self.onSetVolume)
        audioBarSizer.Add(self.volumeCtrl, 0, wx.LEFT | wx.CENTER, 10)

        # Boton menciones
        self.menciones = GB.GradientButton(self, label="MENCIONES")
        self.menciones.SetInitialSize()
        self.menciones.Bind(wx.EVT_BUTTON, self.onMenciones)
        audioBarSizer.Add(self.menciones, 0, wx.LEFT | wx.CENTER, 10)

        # Boton ingresar anuncio nuevo
        self.anuncionuevo = AB.AquaButton(self, label="NUEVO ANUNCIO")
        self.anuncionuevo.SetInitialSize()
        self.anuncionuevo.SetForegroundColour("blue")
        self.anuncionuevo.Bind(wx.EVT_BUTTON, self.onNuevo)
        audioBarSizer.Add(self.anuncionuevo, 0, wx.LEFT | wx.CENTER, 10)

        return audioBarSizer

    def buildBtn(self, btnDict, sizer):
        """"""
        bmp = btnDict['bitmap']
        handler = btnDict['handler']

        img = wx.Bitmap(os.path.join(bitmapDir, bmp))
        btn = buttons.GenBitmapButton(self, bitmap=img, name=btnDict['name'])
        btn.SetInitialSize()
        btn.Bind(wx.EVT_BUTTON, handler)
        sizer.Add(btn, 0, wx.LEFT | wx.CENTER, 3)

    def createMenu(self):
        """
        Crea el menu
        """
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        open_file_menu_item = fileMenu.Append(wx.NewId(), "&Abrir", "Abre un archivo")
        open_file_menu_item2 = fileMenu.Append(wx.NewId(), "&Finalizar hora", "Guarda toda la información")
        exitMenuItem = fileMenu.Append(wx.NewId(), "Salir", "Sale de la aplicacion")
        menubar.Append(fileMenu, '&Archivo')
        self.frame.Bind(wx.EVT_MENU, self.onBrowse, open_file_menu_item)
        self.frame.Bind(wx.EVT_MENU, self.onFinalizar, open_file_menu_item2)
        self.frame.Bind(wx.EVT_MENU, self.onClose, exitMenuItem)
        self.frame.SetMenuBar(menubar)

    def onArrowKey(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_LEFT:
            print 'left'
            self.graf.flecha_izquierda()
        elif keycode == wx.WXK_RIGHT:
            print 'right'
            self.graf.flecha_derecha()
        else:
            event.Skip()

    def loadMusic(self, musicFile):
        """"
        Extrae tiempos, senyal y detecta bloques
        """

        global bloques_ordenados
        global datos_anuncios

        if not self.mediaPlayer.Load(musicFile):
            wx.MessageBox("No se puede abrir %s: Formato erroneo?" % musicFile,
                          "ERROR",
                          wx.ICON_ERROR | wx.OK)
        else:
            if self.s:
                self.s.close()
            if datos_anuncios:
                print 'Cerramos anterior fichero'
                datos_anuncios = []
            if bloques_ordenados:
                bloques_ordenados = []

            self.playPauseBtn.Enable(True)
            for child in self.barra_1h_hora_sizer.GetChildren():
                child.DeleteWindows()

            rutacinta, nomcinta = os.path.split(self.currentFile)
            print "self.currentFile {}".format(self.currentFile)
            print "nomcinta {}".format(nomcinta)
            cursor.execute("SELECT * FROM cintas WHERE nombre_cinta = %s", (nomcinta,))
            db.commit()
            try:
                self.cinta = cursor.fetchone()
                global emisora_cinta
                emisora_cinta = self.cinta["emisora_cinta"]
                print "emisora: {}".format(emisora_cinta)
                print "self.cinta {} type(self.cinta) {}".format(self.cinta, type(self.cinta))

            except:
                msg = "Archivo no almacenado como cinta en base de datos"
                self.showMessageDlg(msg, "Error", wx.OK | wx.ICON_INFORMATION)
                return

            if self.cinta['estado_cinta'] == 'F':
                msg = "Cinta ya finalizada, ¿seguro que desea continuar?"
                self.showMessageDlg(msg, "Error", wx.OK | wx.ICON_INFORMATION)
                return

            message = "Analizando el archivo %s en busca de bloques" % str(self.currentFile)
            self.busy = PBI.PyBusyInfo(message, parent=None, title="Procesando")

            self.inicio_grabacion = self.extraer_tiempo_grabacion(self.currentFile)

            mi = str(self.inicio_grabacion.hour) + ':' + str(self.inicio_grabacion.minute) + ':' + str(
                self.inicio_grabacion.second).zfill(2)

            self.trackCounter.SetLabel(mi)
            self.s = wave.open(self.currentFile, 'r')
            self.fs = self.s.getframerate()
            print "self.fs {}".format(self.fs)
            self.duracion_archivo = int(np.round(self.s.getnframes() / float(self.fs)))
            self.graf.graficado(self.currentFile, self.inicio_grabacion)
            print 'detecta'
            self.DetectaBloques()
            print 'datosanuncios para menuanuncios'
            datos_anuncios, bloquecambiado = VistaSpot.recuperadatos(bloques_ordenados, self.currentFile,
                                                                     self.inicio_grabacion)
            print 'datos'
            for i in datos_anuncios:
                print i
                for j in i.anuncios:
                    print j.inicio

            if bloquecambiado:
                print 'bloques modificados por ocurrencias'
                bloques_ordenados = bloquecambiado
                self.build_1h_bar()
            self.menuanuncios.SetDatos(datos_anuncios)

    def onBloque(self, event):
        """
        Funcion que posiciona el reproductor y la grafica en el bloque presionado
        :param event:
        :return:
        """

        button = event.GetEventObject()
        listas = self.lista1 + self.lista2
        print listas
        bloqueboton = int(button.GetName())

        duracion = listas[bloqueboton][1]
        comienzo_ensecs = (listas[bloqueboton][0] - self.inicio_grabacion).total_seconds()
        print comienzo_ensecs
        print listas[bloqueboton][0]
        print listas[bloqueboton][0] + datetime.timedelta(seconds=duracion)
        self.mediaPlayer.Seek(comienzo_ensecs * 1000)
        self.graf.cambiar_ejes(comienzo_ensecs, comienzo_ensecs + duracion)

    def onSize(self, event):

        self.Refresh()
        event.Skip()

    def onBrowse(self, event):
        """
        Dialogo de busqueda de audio
        """
        wildcard = "WAV (*.wav)|*.wav|" \
                   "MP3 (*.mp3)|*.mp3"

        dlg = wx.FileDialog(
            self, message="Elija un archivo",
            defaultDir=self.currentFolder,
            defaultFile=self.currentFile,
            wildcard=wildcard,
            style=wx.OPEN | wx.CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.currentFolder = os.path.dirname(path)
            self.currentFile = path
            self.loadMusic(path)
        dlg.Destroy()

    def DetectaBloques(self):

        global bloques_ordenados

        if not self.currentFile:
            msg = "Debes abrir un audio en el menu 'Archivo' "
            self.showMessageDlg(msg, "Error", wx.OK | wx.ICON_INFORMATION)
            return

        emisora = 1

        try:
            cursor.execute("SELECT nombre_modelo FROM modelos WHERE cadena_modelo = %s", (emisora,))
            currentModel = cursor.fetchone()["nombre_modelo"]
            print "currentModel {}".format(currentModel)
            bloques = detector_bloques.bloques_porvector(self.currentFile, rutamodelo=currentModel)
            bloques_ordenados = sorted(bloques.items(), key=operator.itemgetter(0))
        except:
            print "no hay modelo"
            pass
        del self.busy
        try:
            bloques_ordenados = sorted(bloques.items(), key=operator.itemgetter(0))
        except:
            bloques_ordenados = []
        self.build_1h_bar()

    def onNuevo(self, event):

        if not self.currentFile:
            msg = "Debes abrir un audio en el menu 'Archivo' "
            self.showMessageDlg(msg, "Error", wx.OK | wx.ICON_INFORMATION)
            return
        # self.fs=44100
        # self.s='jar'
        # self.inicio_grabacion=datetime.datetime.now()
        seleccion = SeleccionDialog(self, self.s, self.fs, self.inicio_grabacion)
        seleccion.SetPosition((500, 300))

        self.graf.marcable()
        seleccion.Show()

    def onMenciones(self, event):

        if not self.currentFile:
            msg = "Debes abrir un audio en el menu 'Archivo' "
            self.showMessageDlg(msg, "Error", wx.OK | wx.ICON_INFORMATION)
            return

        ventana = MencionesDialog(self.currentFile, self.inicio_grabacion)

        ventana.ShowModal()

    def onNext(self, event):
        """
        Avanzamos un valor fijo, incluso en pausa
        """

        # offset siempre en milisegundos

        offset = self.mediaPlayer.Tell()
        try:

            self.mediaPlayer.Seek(offset + 5000)
            self.graf.navegacion()
        except:
            # AQUI por lo visto nunca entra
            self.mediaPlayer.Seek(self.mediaPlayer.Length())

    def onNext2(self, event):
        """
        Avanzamos un valor fijo, incluso en pausa
        """

        # offset siempre en milisegundos

        offset = self.mediaPlayer.Tell()
        try:
            self.mediaPlayer.Seek(offset + 10000)
            self.graf.navegacion()
        except:
            self.mediaPlayer.Seek(self.mediaPlayer.Length())

    def onPause(self):
        """
        Pauses the music
        """
        self.mediaPlayer.Pause()
        # self.graf.pausar()

    def onPlay(self, event):
        """
        Plays the music
        """

        if not event.GetIsDown():
            self.onPause()
            return

        if not self.mediaPlayer.Play():
            wx.MessageBox("No se puede reproducir : Formato invalido",
                          "ERROR",
                          wx.ICON_ERROR | wx.OK)
        else:

            self.Layout()

        event.Skip()

    def onPrev2(self, event):
        """
        Retrocedemos un valor fijo, incluso en pausa
        """
        # offset siempre en milisegundos

        offset = self.mediaPlayer.Tell()
        try:

            self.mediaPlayer.Seek(offset - 10000)
            self.graf.navegacion()
        except:
            self.mediaPlayer.Seek(0)

    def onPrev(self, event):
        """
        Retrocedemos un valor fijo, incluso en pausa
        """
        # offset siempre en milisegundos

        offset = self.mediaPlayer.Tell()
        try:

            # con la funcion atras solo queremos comprobar que si estamos al principio, vuelva a empezar
            self.mediaPlayer.Seek(offset - 5000)
            self.graf.navegacion()
        except:
            self.mediaPlayer.Seek(0)

    def onSetVolume(self, event):
        """
        Sets the volume of the music player
        """
        self.currentVolume = self.volumeCtrl.GetValue()

        self.mediaPlayer.SetVolume(float(self.currentVolume) / 100)

    def onStop(self, event):
        """
        Stops the music and resets the play button
        """

        self.mediaPlayer.Stop()
        self.playPauseBtn.SetToggle(False)
        self.graf.parar()

    def onFinalizar(self, event):

        print 'fin'

        global datos_anuncios

        self.mediaPlayer.Stop()
        self.playPauseBtn.SetToggle(False)

        target = ''
        cuenta = 0
        final_anterior = None
        for i in datos_anuncios:
            i.anuncios.sort(key=lambda x: x.inicio)
            print i.anuncios
            for j in i.anuncios:

                if cuenta == 0:
                    target += '0' * (
                        datetime.datetime.strptime(j.inicio, "%d/%m/%Y %H:%M:%S") - self.inicio_grabacion).seconds
                    print len(target)
                    target += '1' * (
                        datetime.datetime.strptime(j.final, "%d/%m/%Y %H:%M:%S") -
                        datetime.datetime.strptime(j.inicio, "%d/%m/%Y %H:%M:%S")).seconds
                    final_anterior = datetime.datetime.strptime(j.final, "%d/%m/%Y %H:%M:%S")
                    print final_anterior
                else:

                    print final_anterior
                    print j.inicio
                    print j.final
                    if datetime.datetime.strptime(j.inicio, "%d/%m/%Y %H:%M:%S") < final_anterior:
                        target += '1' * (
                            datetime.datetime.strptime(j.final, "%d/%m/%Y %H:%M:%S") - datetime.datetime.strptime(
                                j.inicio,
                                "%d/%m/%Y %H:%M:%S")).seconds
                    else:
                        target += '0' * (
                            datetime.datetime.strptime(j.inicio, "%d/%m/%Y %H:%M:%S") - final_anterior).seconds
                        target += '1' * (
                            datetime.datetime.strptime(j.final, "%d/%m/%Y %H:%M:%S") - datetime.datetime.strptime(
                                j.inicio,
                                "%d/%m/%Y %H:%M:%S")).seconds
                    final_anterior = datetime.datetime.strptime(j.final, "%d/%m/%Y %H:%M:%S")

                cuenta = cuenta + 1

        if self.duracion_archivo - len(target) > 0:
            target += '0' * (self.duracion_archivo - len(target))

        if len(target) < 3000 or len(target) > 5000:
            print 'targets fallidos, algo raro pasa'
        # target = target + "\n" + "="*80 + "\n" + str(lista_anuncios)
        posant = 0
        ltarget = list(target)
        for posicion, valor in enumerate(ltarget):

            if int(valor) and 0 < (posicion - posant) < 3:
                ltarget[posant:posicion] = '1'
                posant = posicion
            if int(valor):
                posant = posicion

        starget = "".join(ltarget)
        tf = open(str(self.currentFile) + '.txt', 'w+')
        tf.seek(0)
        tf.write(starget)
        tf.truncate()
        tf.close()
        self.mediaPlayer.Stop()
        self.playPauseBtn.SetToggle(False)
        self.Close()

    def onTimer(self, event):
        """
        Keeps the player slider updated
        """

        try:
            offset = self.mediaPlayer.Tell()
        except:
            return

        offset = int(offset)

        secsPlayed = str((self.inicio_grabacion + datetime.timedelta(seconds=offset / 1000)).time())

        if offset == -1:

            self.trackCounter.SetLabel(self.marcador)

        else:

            self.trackCounter.SetLabel(secsPlayed)

    def showMessageDlg(self, msg, title, style):
        """"""
        dlg = wx.MessageDialog(parent=None, message=msg,
                               caption=title, style=style)
        dlg.ShowModal()
        dlg.Destroy()

    def onClose(self, event):

        self.mediaPlayer.Stop()
        self.playPauseBtn.SetToggle(False)
        self.Close()


class MediaFrame(wx.Frame):
    """Clase padre """

    # ----------------------------------------------------------------------
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Prototipo Captor")

        global usuario
        MediaPanel(self)
        self.Maximize()


class SeleccionDialog(wx.Dialog):
    def __init__(self, parent, archivo, tasa, archivoinicio):
        """Constructor"""
        wx.Dialog.__init__(self, None, title="Seleccion de anuncio", size=(1000, 1000))

        self.parent = parent
        self.comprobado = False
        self.seg = None
        self.horainicio = 0
        self.horafinal = 0
        self.ai = archivoinicio
        self.nombreanuncio = ''
        self.textomencion = ''
        self.audio = archivo
        self.fs = tasa
        self.seleccionmainSizer = wx.BoxSizer(wx.VERTICAL)
        self.seleccion_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.seleccion_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.seleccion_sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.seleccion_sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.seleccion_sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        self.seleccion_sizer6 = wx.BoxSizer(wx.HORIZONTAL)
        self.seleccion_sizer7 = wx.BoxSizer(wx.HORIZONTAL)
        self.seleccion_sizer8 = wx.BoxSizer(wx.HORIZONTAL)
        self.seleccion_sizer9 = wx.BoxSizer(wx.HORIZONTAL)
        self.seleccion_sizer10 = wx.BoxSizer(wx.HORIZONTAL)
        self.bcomprobar = wx.Button(self, label="Comprobar")
        self.bcomprobar.Bind(wx.EVT_BUTTON, self.OnButton)
        self.BuildEntradas(u'COMIENZO', self.seleccion_sizer1, nombre='comienzo')
        self.BuildEntradas(u'FINAL', self.seleccion_sizer1, nombre='final')
        self.Bind(wx.EVT_CLOSE, self.onCloseWindow)
        self.seleccion_sizer10.Add(self.bcomprobar, 0, wx.CENTER, 75)
        self.seleccionmainSizer.Add(self.seleccion_sizer1, 1, wx.LEFT | wx.CENTER, 0)
        self.seleccionmainSizer.Add(self.seleccion_sizer10, 1, wx.LEFT | wx.CENTER, 0)
        self.SetSizerAndFit(self.seleccionmainSizer)
        self.Layout()

    def onCloseWindow(self, event):

        self.parent.graf.borrar_marcas()
        self.parent.graf.nomarcable()
        self.Destroy()

    def extraer_tiempo_grabacion(self, archivo):
        """
        :rtype : datetime.datetime
        :param archivo: nombre del archivo
        :return: datetime.datetime
        """
        try:
            nombre = os.path.splitext(os.path.basename(archivo))[0]
            anho = int(nombre[0:4])
            mes = int(nombre[4:6])
            dia = int(nombre[6:8])
            hora = int(nombre[8:10])
            minuto = int(nombre[10:12])
            segundo = int(nombre[12:14])
            milisegundo = 0
            return datetime.datetime(anho, mes, dia, hora, minuto, segundo, milisegundo)
        except:
            pass
            return -1

    def OnButton(self, e):

        lb, la = self.parent.graf.mirarlimites()
        print 'boton comprobar'

        txtCtrls = [widget for widget in self.GetChildren() if isinstance(widget, wx.TextCtrl)]
        for ctrl in txtCtrls:
            if ctrl.GetName() == 'comienzo':

                print 'lb', lb
                if lb:
                    ctrl.SetValue(lb.time().strftime("%H:%M:%S"))

                try:
                    self.horainicio = ctrl.GetValue()
                except:

                    msg = "Debes marcar un inicio o bien presionando shift " \
                          "y click izquierdo (barra verde) o por teclado con formato HH:MM:SS "
                    self.showMessageDlg(msg, "Error", wx.OK | wx.ICON_INFORMATION)
                    return
            if ctrl.GetName() == 'final':

                if la:
                    ctrl.SetValue(la.time().strftime("%H:%M:%S"))
                try:
                    self.horafinal = ctrl.GetValue()
                except:
                    msg = "Debes marcar un inicio o bien presionando shift " \
                          "y click derecho (barra roja) o por teclado con formato HH:MM:SS "
                    self.showMessageDlg(msg, "Error", wx.OK | wx.ICON_INFORMATION)
                    return

        comienzo_archivo = datetime.timedelta(hours=self.ai.hour, minutes=self.ai.minute, seconds=self.ai.second)
        print comienzo_archivo
        try:
            comienzo_anuncio = datetime.timedelta(hours=int(self.horainicio.split(':')[0]),
                                                  minutes=int(self.horainicio.split(':')[1]),
                                                  seconds=int(self.horainicio.split(':')[2]))
            final_anuncio = datetime.timedelta(hours=int(self.horafinal.split(':')[0]),
                                               minutes=int(self.horafinal.split(':')[1]),
                                               seconds=int(self.horafinal.split(':')[2]))

        except:
            msg = "Debes marcar un inicio o bien presionando shift " \
                  "y click derecho (barra roja) o por teclado con formato HH:MM:SS "
            self.showMessageDlg(msg, "Error", wx.OK | wx.ICON_INFORMATION)
            return

        comienzo_relativo = comienzo_anuncio - comienzo_archivo
        final_relativo = final_anuncio - comienzo_archivo
        print final_anuncio
        print comienzo_anuncio
        print comienzo_relativo
        print final_relativo
        print 'tam anuncio'
        taman = (final_anuncio - comienzo_anuncio).total_seconds()
        print taman
        print "tam anuncio {}".format((final_anuncio - comienzo_anuncio).seconds)
        if taman <= 0 or not self.horainicio or not self.horafinal:

            wx.MessageBox("Error en los limites de anuncio",
                          "ERROR",
                          wx.ICON_ERROR | wx.OK)
        else:

            self.parent.graf.cambiar_ejes(comienzo_relativo.total_seconds(), final_relativo.total_seconds())
            self.parent.graf.borrar_marcas()

            self.audio.setpos(comienzo_relativo.seconds * self.fs)

            segmento = self.audio.readframes((final_anuncio - comienzo_anuncio).seconds * self.fs)

            self.seg = np.fromstring(segmento, np.int16)
            print "len self.seg {} tam {}".format(len(self.seg), len(self.seg) / self.fs)
            print "antes recognize"
            estaanuncio = djv.recognize(AudioRecognizer, self.seg)
            print "despues recognize"
            print 'confianza'
            if estaanuncio is None:
                estaanuncio = dict()
                estaanuncio["confidence"] = 0
            if estaanuncio["confidence"] > UMBRAL * 2:
                confidence = estaanuncio["confidence"]
                print 'anuncio ya esta'
                cursor.execute("SELECT * FROM songs WHERE song_id = %s", (estaanuncio["song_id"],))
                estaanuncio = cursor.fetchone()
                print estaanuncio
                cur.execute(
                    "INSERT INTO ocurrencias (fecha_anuncio, id_anuncio, emisora_anuncio, duracion_anuncio, "
                    "nombre_cinta, confidence, codigo_medio, grupo, cadena, emision, anho, mes, dia, hora, "
                    "minuto, segundo, codigo_marca_modelo, nombre_marca, nombre_modelo, compartido, forma_publicidad, "
                    "total_inserciones_bloque, numero_insercion_dentro_bloque, codigo_programa, "
                    "codigo_marketing_directo, codigo_operador, codigo_version, descripcion) VALUES (%s, %s, %s, %s, "
                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (datetime.datetime.now(), estaanuncio["song_id"], emisora_cinta, estaanuncio["len"],
                     os.path.splitext(os.path.basename(self.parent.currentFile))[0], confidence, 'RD',
                     estaanuncio["grupo"], estaanuncio["cadena"], estaanuncio["emision"],
                     self.extraer_tiempo_grabacion(self.parent.currentFile).year,
                     self.extraer_tiempo_grabacion(self.parent.currentFile).month,
                     self.extraer_tiempo_grabacion(self.parent.currentFile).day, int(self.horainicio.split(':')[0]),
                     int(self.horainicio.split(':')[1]),
                     int(self.horainicio.split(':')[2]), estaanuncio["codigo_marca_modelo"],
                     estaanuncio["nombre_marca"], estaanuncio["nombre_modelo"],
                     estaanuncio["compartido"], "", "", "", "", "", "", estaanuncio["song_id"],
                     estaanuncio["texto_mencion"]))
                db.commit()
                print "ocurrencia guardada"
                self.comprobado = False
                wx.MessageBox(
                    "El anuncio que intenta guardar ya ha sido almacenado como %s. Insertando la ocurrencia." %
                    estaanuncio["song_name"],
                    "EXCLAMATION",
                    wx.ICON_EXCLAMATION | wx.OK)
                self.Close()
            else:

                self.comprobado = True

                self.parent.graf.nomarcable()

                # except Exception, e:
                #     # wx.MessageBox("Error  en la comprobacion del segmento",
                #     #   "ERROR",
                #     #   wx.ICON_ERROR | wx.OK)
                #     print Exception, e
                #     self.comprobado = True

        if self.comprobado:
            self.Destroy()
            anund = AnuncioDialog(self.parent.currentFile, self.fs, self.seg, taman, self.ai, comienzo_anuncio,
                                  final_anuncio, self.parent.menuanuncios, bloques_ordenados, datos_anuncios,
                                  emisora_cinta, estaanuncio["confidence"], segmento)
            anund.SetPosition((0, 0))
            anund.Show()

    def BuildCombo(self, campoentrada, sizerentrada, nombre='entrada', ):

        campo = wx.StaticText(self, label=campoentrada)
        fuente = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        campo.SetFont(fuente)
        valor = DynamicListComboBox(self, "", [])
        sizerentrada.Add(campo, 0, wx.ALL | wx.CENTER, 5)
        sizerentrada.Add(valor, 0, wx.ALL | wx.CENTER, 5)

    def BuildEntradas(self, campoentrada, sizerentrada, nombre='entrada', tamanho=(140, -1)):

        campo = wx.StaticText(self, label=campoentrada)
        fuente = wx.Font(16, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        campo.SetFont(fuente)
        valor = wx.TextCtrl(self, name=nombre, size=tamanho)
        sizerentrada.Add(campo, 0, wx.ALL | wx.CENTER, 5)
        sizerentrada.Add(valor, 0, wx.ALL | wx.CENTER, 5)

    def showMessageDlg(self, msg, title, style):
        """"""
        dlg = wx.MessageDialog(parent=None, message=msg,
                               caption=title, style=style)
        dlg.ShowModal()
        dlg.Destroy()


class GraficaPanel(wx.Panel):
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)

        self.parent = parent

        self.marcar = False
        self.figure = Figure(facecolor='darkslategray')
        self.axes = self.figure.add_subplot(111, rasterized=True)
        # self.axes.set_rasterization_zorder(1)
        self.axes.get_yaxis().set_visible(False)
        # self.figure.text(0.5, 0.02, 'tiempo', ha='center', va='center')
        self.samples = []
        self.ejetiempo = []
        self.dinamicas = None
        self.canvas = FigureCanvas(self, 0, self.figure)
        self.figure.tight_layout()
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.canvas, 0, wx.EXPAND | wx.ALL)
        self.SetSizer(mainSizer)

    def graficado(self, archivo, inicio_grabacion):

        self.axes.clear()
        if self.dinamicas:
            print 'paramos'
            self.dinamicas.parar_timer()
            self.dinamicas = None

        self.ig = inicio_grabacion

        s = wave.open(archivo, 'r')
        canales = s.getnchannels()
        self.fs = s.getframerate()
        self.duracion_archivo = int(np.round(s.getnframes() / float(self.fs)))

        segmento = s.readframes(s.getnframes())
        if canales > 1:
            print 'CANALES', canales
            segmento = segmento[0::canales]
        s.close()
        print "len(segmento) {}".format(len(segmento))

        print 'DURACION', self.duracion_archivo
        # diezmado=2#(self.fs/16000)*2
        diezmado = 25
        print 'DEZ', diezmado
        segmento = segmento[0::diezmado]
        data = np.fromstring(segmento, np.int16)
        print "len(data) {}".format(len(data))
        self.fs = self.fs / diezmado
        print 'fs', self.fs
        self.samples = data.astype('float32') / 32767.0
        self.samples = self.samples / max(self.samples)
        self.ejetiempo = np.linspace(0, self.duracion_archivo, num=len(self.samples))

        self.dinamicas = GraficaDinamica(self, self.parent, fig=self.canvas.figure)
        self.dinamicas.show()

    def cambiar_ejes(self, x1, x2):

        if self.dinamicas:
            if self.parent.anuncioseleccionado['inicio']:
                print 'anuncio si!'
                print self.parent.anuncioseleccionado['inicio']
            else:
                print 'anuncio no'
            self.dinamicas.graficar_intervalo(xmin=x1, xmax=x2)
            self.dinamicas.pintar()

    def marcable(self):
        # solucion provisional para marcar limites de anuncios
        self.marcar = True

    def nomarcable(self):
        # solucion provisional para marcar limites de anuncios
        self.marcar = False

    def parar(self):
        if self.dinamicas:
            self.dinamicas.stop_barra()

    def navegacion(self):
        if self.dinamicas:
            self.dinamicas.navegacion_barra()

    def mirarlimites(self):
        if self.dinamicas:
            return self.dinamicas.devolverlimites()

    def borrar_marcas(self):
        if self.dinamicas:
            self.dinamicas.clearMarker()

    def flecha_izquierda(self):
        if self.dinamicas:
            self.dinamicas.izq()

    def flecha_derecha(self):
        if self.dinamicas:
            self.dinamicas.dcha()


class GraficaDinamica:
    def __init__(self, parent, mediapanel, fig=None):

        self.parent = parent

        if fig != None:
            print fig
            self.fig = fig
        else:

            self.fig = pyplot.get_current_fig_manager().canvas.figure

        self.Plot = self.fig.axes[0]
        self.canvas = self.fig.canvas
        self.media = mediapanel
        self.dragFrom = None
        self.timer = None
        self.barrapos = 0
        self.liminf = 0
        self.limsup = 0
        self.markerbajo = None
        self.markeralto = None
        self.barras = []

        self.formatter = ticker.FuncFormatter(self.timeTicks)
        self.limitebajo = 0
        self.limitealto = 0
        self.line = None
        self.played = False
        self.shift_presionado = False

        self.barrabloq = False

        self.desplazalimite = 0.5
        self.demarcadores = 0
        self.cid = []
        # self.formatter = None


        self.cid.append(self.canvas.mpl_connect('button_press_event', self.onClick))
        self.cid.append(self.canvas.mpl_connect('button_release_event', self.onRelease))
        self.cid.append(self.canvas.mpl_connect('scroll_event', self.onScroll))

        self.cid.append(self.canvas.mpl_connect('key_press_event', self.onKey))
        self.cid.append(self.canvas.mpl_connect('key_release_event', self.onKeyRelease))
        self.cid.append(self.canvas.mpl_connect('resize_event', self.onResize))
        print 'DURACION EN G DINAMICA', self.parent.duracion_archivo
        # no ponemos toda la senyal
        self.Plot.set_xlim([0, self.parent.duracion_archivo])

        self.graficar_intervalo()
        self.barra_player()

    def graficar_intervalo(self, xmin=0, xmax=0):

        if not xmin and not xmax:
            xmin, xmax = self.Plot.get_xlim()

        # xmin=np.round(xmin)
        # xmax=np.round(xmax)
        distancia = int(np.round(self.parent.fs * (xmax - xmin)))

        # plotdiez = distancia / 20000
        plotdiez = 25
        if not plotdiez:
            plotdiez = 1

        self.Plot.clear()
        self.Plot.xaxis.set_major_formatter(self.formatter)

        try:

            # plotdiez= int(np.round(distancia))*4
            print 'diezmado', plotdiez
            print len(self.parent.ejetiempo[int(self.parent.fs * xmin):int(self.parent.fs * xmax)][0::plotdiez])
            if not plotdiez or plotdiez < 0:
                print 'muy pekeno'
                plotdiez = 1
            self.Plot.plot(self.parent.ejetiempo[int(self.parent.fs * xmin):int(self.parent.fs * xmax)][0::plotdiez],
                           self.parent.samples[int(self.parent.fs * xmin):int(self.parent.fs * xmax)][0::plotdiez],
                           rasterized=True)
        except:
            print 'en except'
            self.Plot.plot(self.parent.ejetiempo[0::200], self.parent.samples[0::200])

        self.Plot.set_xlim(
            [self.parent.ejetiempo[int(self.parent.fs * xmin):int(self.parent.fs * xmax)][0::plotdiez][0],
             self.parent.ejetiempo[int(self.parent.fs * xmin):int(self.parent.fs * xmax)][0::plotdiez][-1]])
        self.Plot.set_ylim([-1.05, 1.05])
        self.Plot.grid()
        self.liminf = xmin  # self.parent.ejetiempo[int(self.parent.fs*xmin):int(self.parent.fs*xmax)][0::plotdiez][0]
        self.limsup = xmax  # self.parent.ejetiempo[int(self.parent.fs*xmin):int(self.parent.fs*xmax)][0::plotdiez][-1]

        self.background = self.canvas.copy_from_bbox(self.Plot.bbox)
        self.canvas.draw()

    def pintar(self):
        print 'pintar'
        self.canvas.draw()
        if self.markerbajo:
            self.Plot.draw_artist(self.markerbajo)
        if self.markeralto:
            self.Plot.draw_artist(self.markeralto)
        self.background = self.canvas.copy_from_bbox(self.Plot.bbox)

    def clearMarker(self, tipo='todos'):

        if tipo == 'todos':

            if self.markerbajo in self.Plot.lines:
                self.Plot.lines.remove(self.markerbajo)
            if self.markeralto in self.Plot.lines:
                self.Plot.lines.remove(self.markeralto)
            self.markerbajo = None
            self.markeralto = None
            self.limitebajo = 0
            self.limitealto = 0

        elif tipo == 'bajo':
            try:
                self.Plot.lines.remove(self.markerbajo)
                self.limitebajo = 0
                self.markerbajo = None
            except:
                print 'zoom con markers'
                self.limitebajo = 0
                self.markerbajo = None

        elif tipo == 'alto':
            try:
                self.Plot.lines.remove(self.markeralto)
                self.limitealto = 0
                self.markeralto = None
            except:
                print 'zoom con markers'
                self.limitealto = 0
                self.markeralto = None

        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.Plot.bbox)

    def update(self):

        for b in self.barras:

            if b in self.Plot.lines:
                self.Plot.lines.remove(b)
        self.barras = []

        # revert the canvas to the state before any progress line was drawn
        self.canvas.restore_region(self.background)

        # compute the distance that the progress line has made (based on running time)

        if self.media.mediaPlayer.Tell() / 1000.0 != 0.0:
            self.barrapos = (self.media.mediaPlayer.Tell() / 1000.0)
            self.played = True
            if not self.barrabloq:
                if self.barrapos > self.limsup:
                    print 'pasado'
                    avance = self.limsup - self.liminf
                    if self.limsup + avance > self.parent.duracion_archivo:
                        avance = self.parent.duracion_archivo - self.limsup
                    elif avance < 5:
                        avance = 5
                    self.graficar_intervalo(xmin=int(self.barrapos), xmax=self.limsup + avance)
                    self.pintar()
                if self.barrapos < self.liminf:
                    self.graficar_intervalo(xmin=int(self.barrapos), xmax=self.limsup)
                    self.pintar()
            else:
                print 'jar'
                self.barrabloq = False

        else:

            if not self.played:
                for b in self.barras:
                    if b in self.Plot.lines:
                        self.Plot.lines.remove(b)
                self.barras[:] = []

            else:

                self.stop_barra()
                self.played = False
        if self.played:
            self.barras.append(self.line.set_xdata(self.barrapos))

            self.Plot.draw_artist(self.line)

        self.canvas.blit(self.Plot.bbox)

    def show(self):

        pyplot.show(block=False)
        pyplot.show()

    def timeTicks(self, x, pos):
        # print self.parent.ig
        # print 'a'
        # print self.igrab
        d = (self.parent.ig + datetime.timedelta(seconds=x)).time()
        return str(d)

    def barra_player(self):

        if not self.timer:

            self.canvas.draw()

            self.background = self.canvas.copy_from_bbox(self.Plot.bbox)
            self.line = self.Plot.axvline(x=0, linewidth=7, color='k')

            self.barras.append(self.line)
            self.timer = self.canvas.new_timer(interval=100)

            self.timer.add_callback(self.update)  # every 100ms it calls update function
            self.timer.start()
        else:
            print 'replay'
            for b in self.barras:
                if b in self.Plot.lines:
                    self.Plot.lines.remove(b)
            self.barras[:] = []
            self.canvas.draw()
            self.background = self.canvas.copy_from_bbox(self.Plot.bbox)
            self.update()

            self.timer.start()

    def parar_timer(self):
        if self.timer:
            self.timer.stop()
            self.timer = None

    def stop_barra(self):

        self.barrabloq = False
        self.media.mediaPlayer.Stop()
        self.media.playPauseBtn.SetToggle(False)

    def navegacion_barra(self):

        print self.barrapos
        print self.liminf
        self.barrabloq = False

    def onResize(self, event):

        event.canvas.draw()
        if self.markerbajo:
            self.Plot.draw_artist(self.markerbajo)
        if self.markeralto:
            self.Plot.draw_artist(self.markeralto)

        self.background = event.canvas.copy_from_bbox(self.Plot.bbox)

    def onClick(self, event):

        """
        Process a mouse click event. If a mouse is right clicked within a
        subplot, the return value is set to a (subPlotNr, xVal, yVal) tuple and
        the plot is closed. With right-clicking and dragging, the plot can be
        moved.

        Arguments:
        event -- a MouseEvent event
        """

        if event.inaxes:

            if self.shift_presionado and self.parent.marcar:
                print 'shift'
                if event.button == 1:
                    print 'marca'
                    self.clearMarker(tipo='bajo')
                    self.markerbajo = self.Plot.axvline(event.xdata, 0, 1, linestyle='--',
                                                        linewidth=4, color='green')
                    print event.xdata
                    # self.markers.append(marker)
                    self.limitebajo = self.parent.ig + datetime.timedelta(seconds=event.xdata)
                    self.demarcadores = 0


                elif event.button == 3:
                    # boton derecho
                    if self.shift_presionado:
                        self.clearMarker(tipo='alto')
                        self.markeralto = self.Plot.axvline(event.xdata, 0, 1, linestyle='--',
                                                            linewidth=4, color='red')
                        # self.markers.append(marker)
                        self.limitealto = self.parent.ig + datetime.timedelta(seconds=event.xdata)
                        self.demarcadores = 1
            else:
                if event.dblclick and event.button == 1:

                    self.media.mediaPlayer.Seek(event.xdata * 1000)

                    self.barrapos = event.xdata

                elif event.button == 3:
                    self.dragFrom = event.xdata

            self.canvas.draw()

            if self.markerbajo:
                self.Plot.draw_artist(self.markerbajo)
            if self.markeralto:
                self.Plot.draw_artist(self.markeralto)
            self.background = event.canvas.copy_from_bbox(self.Plot.bbox)

    def izq(self):

        if self.limitealto and self.demarcadores:
            print 'alto'
            xdata = (self.limitealto - datetime.timedelta(seconds=self.desplazalimite))  # time()
            print xdata
            print (xdata - self.parent.ig).total_seconds()
            self.clearMarker(tipo='alto')
            self.markeralto = self.Plot.axvline((xdata - self.parent.ig).total_seconds(), 0, 1, linestyle='--',
                                                linewidth=4, color='red')

            self.limitealto = self.parent.ig + datetime.timedelta(seconds=(xdata - self.parent.ig).total_seconds())

        elif self.limitebajo:
            xdata = (self.limitebajo - datetime.timedelta(seconds=self.desplazalimite))  # time()
            print xdata
            print (xdata - self.parent.ig).total_seconds()
            self.clearMarker(tipo='bajo')
            self.markerbajo = self.Plot.axvline((xdata - self.parent.ig).total_seconds(), 0, 1, linestyle='--',
                                                linewidth=4, color='green')

            self.limitebajo = self.parent.ig + datetime.timedelta(seconds=(xdata - self.parent.ig).total_seconds())

        self.canvas.draw()

        if self.markerbajo:
            self.Plot.draw_artist(self.markerbajo)
        if self.markeralto:
            self.Plot.draw_artist(self.markeralto)
        self.background = self.canvas.copy_from_bbox(self.Plot.bbox)

    def dcha(self):

        if self.limitealto and self.demarcadores:
            print 'alto'
            xdata = (self.limitealto + datetime.timedelta(seconds=self.desplazalimite))  # time()
            print xdata
            print (xdata - self.parent.ig).total_seconds()
            self.clearMarker(tipo='alto')
            self.markeralto = self.Plot.axvline((xdata - self.parent.ig).total_seconds(), 0, 1, linestyle='--',
                                                linewidth=4, color='red')

            self.limitealto = self.parent.ig + datetime.timedelta(seconds=(xdata - self.parent.ig).total_seconds())

        elif self.limitebajo:
            xdata = (self.limitebajo + datetime.timedelta(seconds=self.desplazalimite))  # time()
            print xdata
            print (xdata - self.parent.ig).total_seconds()
            self.clearMarker(tipo='bajo')
            self.markerbajo = self.Plot.axvline((xdata - self.parent.ig).total_seconds(), 0, 1, linestyle='--',
                                                linewidth=4, color='green')

            self.limitebajo = self.parent.ig + datetime.timedelta(seconds=(xdata - self.parent.ig).total_seconds())

        self.canvas.draw()

        if self.markerbajo:
            self.Plot.draw_artist(self.markerbajo)
        if self.markeralto:
            self.Plot.draw_artist(self.markeralto)
        self.background = self.canvas.copy_from_bbox(self.Plot.bbox)

    def onKey(self, event):

        """
        Handle a keypress event. The plot is closed without return value on
        enter. Other keys are used to add a comment.

        Arguments:
        event -- a KeyEvent
        """

        if event.key == 'escape':
            self.clearMarker()

        if event.key == ' ':
            print 'espacio presionado'

        if event.key == 'shift':
            self.shift_presionado = True

    def onKeyRelease(self, event):
        if event.key == 'shift':
            self.shift_presionado = False

    def devolverlimites(self):
        # if self.limitebajo and self.limitealto:
        return (self.limitebajo, self.limitealto)

    def onRelease(self, event):

        """
        Handles a mouse release, which causes a move

        Arguments:
        event -- a mouse event
        """

        if self.dragFrom == None or event.button != 3 or self.shift_presionado:
            return
        elif event.inaxes:
            dragTo = event.xdata
            dx = self.dragFrom - dragTo

            xmin, xmax = self.Plot.get_xlim()
            xmin_prov = xmin + dx
            xmax_prov = xmax + dx
            if xmin_prov < 0:
                xmin_prov = 0
                xmax_prov = xmax - xmin
            elif xmax_prov > int(self.parent.duracion_archivo):
                xmin_prov = xmin + (int(self.parent.duracion_archivo) - xmax)
                xmax_prov = int(self.parent.duracion_archivo)

            self.graficar_intervalo(xmin=xmin_prov, xmax=xmax_prov)
            self.liminf = xmin_prov
            self.limsup = xmax_prov
            event.canvas.draw()
            if self.markerbajo:
                self.Plot.draw_artist(self.markerbajo)
            if self.markeralto:
                self.Plot.draw_artist(self.markeralto)
            self.barrabloq = True
            self.background = event.canvas.copy_from_bbox(self.Plot.bbox)

    def onScroll(self, event):

        """
        Process scroll events. All subplots are scrolled simultaneously

        Arguments:
        event -- a MouseEvent
        """

        if event.inaxes:
            xmin, xmax = self.Plot.get_xlim()
            print 'xmax cogido del scroll', xmax
            dx = xmax - xmin
            cx = (xmax + xmin) / 2
            print 'cx', cx
            print 'dx', dx
            cu = event.xdata

            if event.button == 'down':
                # se aleja

                dx *= 1.3

            else:
                dx /= 1.3
            # si cu es menor que el centro (o mucho menor), el limite por la izquierda se mantiene
            # print cx/cu
            if cx / cu > 1.1:  # 0

                _xmin = xmin
                _xmax = cx + dx / 2
            elif cx / cu < 0.9:  # 0
                _xmin = cx - dx / 2
                _xmax = xmax
            else:
                # print 'centro'
                _xmin = cx - dx / 2
                _xmax = cx + dx / 2
            # _xmin = ((cx+cu)/2) - dx/2
            # _xmax = ((cx+cu)/2) + dx/2

            if _xmin < 0:
                _xmin = 0
            if _xmax > int(self.parent.duracion_archivo):
                print 'xmax de max'
                print int(self.parent.duracion_archivo)
                _xmax = int(self.parent.duracion_archivo)
            print 'xmax del scroll ', _xmax

            self.graficar_intervalo(xmin=_xmin, xmax=_xmax)

            self.liminf = _xmin
            self.limsup = _xmax
            event.canvas.draw()
            self.barrabloq = True
            if self.markerbajo:
                self.Plot.draw_artist(self.markerbajo)
            if self.markeralto:
                self.Plot.draw_artist(self.markeralto)
            self.background = event.canvas.copy_from_bbox(self.Plot.bbox)


class MencionesDialog(wx.Dialog):
    # -*- coding: utf-8 -*-
    def __init__(self, archivo, inicio):
        """Constructor"""
        wx.Dialog.__init__(self, None, title="Menciones a buscar", size=(570, 250))
        self.comienzo = inicio
        # user info
        menciones_sizer = wx.BoxSizer(wx.HORIZONTAL)

        menciones_texto = wx.StaticText(self, -1, "Frase a encontrar:", (300, 240))
        menciones_sizer.Add(menciones_texto, 0, wx.ALL | wx.CENTER, 5)
        self.mencion = wx.TextCtrl(self)
        self.mencion.SetSize((200, 300))
        menciones_sizer.Add(self.mencion, 0, wx.ALL, 5)

        resultado_texto = wx.StaticText(self, -1, "Encontrado en:", (300, 240))
        menciones_sizer.Add(resultado_texto, 0, wx.ALL | wx.CENTER, 5)
        self.resultado = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.resultado.SetSize((200, 300))
        menciones_sizer.Add(self.resultado, 0, wx.ALL, 5)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, label='Ok')
        closeButton = wx.Button(self, label='Cerrar')
        okButton.Bind(wx.EVT_BUTTON, self.onBuscar)
        hbox.Add(okButton)
        hbox.Add(closeButton, flag=wx.LEFT, border=5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(menciones_sizer, 0, wx.ALL, 5)
        main_sizer.Add(hbox, 0, wx.ALL, 5)

        self.SetSizer(main_sizer)

        okButton.Bind(wx.EVT_BUTTON, lambda event: self.onBuscar(event, archivo), okButton)
        closeButton.Bind(wx.EVT_BUTTON, self.onClose)

    def onBuscar(self, event, archivo):

        print self.mencion.GetValue()
        self.buscador(archivo)

    def buscador(self, archivo):

        listaameter = []
        filename = archivo
        abuscar = self.mencion.GetValue()  # .decode('utf8')
        print abuscar
        print type(abuscar)
        # cur
        cur.execute("set names utf8;")
        cur.execute(u"INSERT INTO songs ( song_id,song_name, len,fingerprinted ) values (%s, %s, %s, %s)",
                    (1000, abuscar.decode('utf8'), 20, 1))
        db.commit()
        listabuscar = abuscar.split()

        with open(dictd, "r") as f:
            searchlines = f.readlines()

        for np, palabra in enumerate(listabuscar):
            print palabra
            encontrado = False
            for i, line in enumerate(searchlines):
                if palabra + ' ' in line:
                    encontrado = True
            if not encontrado:
                print 'Palabra NO en la lista'
                # if string.isalpha(): En principio si esta en el diccionario no tiene simbolos
                print palabra
                listabuscar.remove(palabra)

                listaameter.append(palabra)

        claves = 'D:\\i+d\\Captor\\reconvoz\docs\\menciones.txt'

        cuenta = 0
        fm = open(claves, "wb")
        lineamencion = ''
        for num, pal in enumerate(listabuscar):
            lineamencion += pal
            lineamencion += ' '
            if len(pal) > 4:
                cuenta += 1
            if cuenta > 2:
                fm.write(lineamencion + ' /1e-75/' + '\n')
                lineamencion = ''
                cuenta = 0
        if lineamencion:
            fm.write(lineamencion + ' /1e-75/' + '\n')
        fm.close()

        # [seq[i:i+size] for i  in range(0, len(seq), size)]

        ffmpeg = Popen([
            "C:\Users\plr\Downloads\\ffmpeg-20150217-git-2bae7b3-win64-static\\bin\\ffmpeg",
            # "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "-i", filename,
            "-vn", "-acodec", "pcm_s16le",  # Little Endian 16 bit PCM
            "-ac", "1", "-ar", str(16000),  # -ac = audio channels (1)
            "-f", "s16le", "-"],  # -f wav for WAV file
            stdin=PIPE, stdout=PIPE)  # , stderr = open(os.devnull, "w"))

        samples = ffmpeg.stdout
        config = Decoder.default_config()
        config.set_string('-hmm', hmdir)
        config.set_string('-lm', lmdir)
        config.set_string('-dict', dictd)

        decoder = Decoder(config)

        in_speech_bf = True
        decoder.set_kws('kw', claves)

        decoder.set_search('kw')

        decoder.start_utt()
        cont = 0

        encuentros = []
        texto = []

        hipotesis = ''
        while True:

            buf = samples.read(32000)  # 32000

            cont += 1
            if buf:
                decoder.process_raw(buf, False, False)
                try:
                    if decoder.hyp().hypstr != '':
                        # en decoder.hyp esta la cadena entera de reconocidos, en hipotesis tambien se va actualizando
                        if decoder.hyp().hypstr != hipotesis:
                            hipotesis = decoder.hyp().hypstr
                            print decoder.hyp().hypstr
                            # print 'encontrado en: '
                            # print 'Partial decoding result:', decoder.hyp().hypstr
                            encuentros.append(cont)
                            # hay que meter la ultima palabra

                            texto.append(hipotesis.split(' ')[-1])

                except AttributeError:
                    pass

                if decoder.get_in_speech():
                    print '.'
                    # sys.stdout.flush()
                if decoder.get_in_speech() != in_speech_bf:
                    in_speech_bf = decoder.get_in_speech()
                    if not in_speech_bf:
                        decoder.end_utt()
                        try:
                            if decoder.hyp().hypstr != '':
                                print 'Resultado parcial:', decoder.hyp().hypstr

                                print cont

                        except AttributeError:
                            pass
                        hipotesis = ''
                        decoder.start_utt()

            else:
                break

        # kl= decoder.n_frames()

        print '\n\nENCUENTROS'
        print abuscar
        print encuentros
        print texto
        print 'fin'
        for t in encuentros:
            self.resultado.AppendText(str((self.comienzo + datetime.timedelta(seconds=t - 3)).time()) + ' \n')

    def onClose(self, e):

        self.Destroy()


if __name__ == '__main__':
    app = wx.App(False)
    frame = MediaFrame()
    frame.Show()  # FullScreen(True, style=wx.FULLSCREEN_ALL)
    # wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()
