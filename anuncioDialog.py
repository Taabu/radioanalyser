# coding=utf-8
# __author__ = 'Mario'

import datetime
import wave
import os
from MySQLdb.cursors import DictCursor
import wx
import wx.lib.inspection
import VistaSpot
from varsUtilsCaptorRadioV2 import cargar_conexion_sql_local, cargar_conexion_mysql_local, \
    cargar_djv_infoadex

cnx_as400 = cargar_conexion_sql_local()
cnx_mysql = cargar_conexion_mysql_local()

cursor_as400 = cnx_as400.cursor()
cursor_mysql = cnx_mysql.cursor(DictCursor)

djv = cargar_djv_infoadex()


class AnuncioDialog(wx.Dialog):
    def __init__(self, archivo, t_muestreo, muestras, tam, fecha, comienzo, final, menuanuncios, bloques_ordenado,
                 datos_anuncio, emisora_cinta, confidence, segmento):
        """Constructor"""

        self.dias_semana = {1: "L", 2: "M", 3: "X", 4: "J", 5: "V", 6: "S", 7: "D"}

        if emisora_cinta == 2:
            self.grupo = "INTE"
            self.cadena = "INTE"
            self.emision = "INTE"
        elif emisora_cinta == 3:
            self.grupo = "ESRA"
            self.cadena = "ESRA"
            self.emision = "ESRM"

        wx.Dialog.__init__(self, None, title=u"Ingreso de anuncio", size=(970, 950))

        fuenteTitulo = wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        fuenteNormal = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

        self.db = cnx_mysql
        self.djv = djv
        self.cursorMySQL = cursor_mysql
        self.archivo = archivo
        self.fs = t_muestreo
        self.audio = muestras
        self.segmento = segmento
        self.tam = tam
        self.comienzo = comienzo
        self.final = final
        self.m_a = menuanuncios
        self.fecha = fecha
        self.bloques_ordenados = bloques_ordenado
        self.datos_anuncios = datos_anuncio
        self.emisora = emisora_cinta
        self.nombre_cinta = os.path.splitext(os.path.basename(self.archivo))[0]
        self.confidence = confidence
        self.ruta = "C:/CaptorRadio-v2/anuncios"
        self.listaSectorSubsectorProducto = []
        self.listaResultado = []
        self.totalResultados = 0
        self.listaSoportes = []
        self.listaGrupo = []
        self.listaCadena = []
        self.listaEmision = []
        self.listaProgramas = []
        self.listaTipoAnuncios = []
        self.listaProgramas = []
        self.marcaSelec = ""
        self.modeloSelec = ""
        self.sectorSelec = ""
        self.subsectorSelec = ""
        self.productoSelec = ""
        self.codigoPrograma = ""

        # creamos el layout
        self.anunciomainSizer = wx.BoxSizer(wx.VERTICAL)

        # Sizer 1 contiene el título RADIO
        self.anuncio_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.stMedio = wx.StaticText(self, label=u"RADIO")
        self.stMedio.SetFont(fuenteTitulo)
        self.anuncio_sizer1.Add(self.stMedio, flag=wx.CENTER, border=10)
        self.anunciomainSizer.Add(self.anuncio_sizer1, 1, wx.LEFT | wx.CENTER, 0)
        # Fin Sizer 1
        # -------------------------------------------------------------------------------
        # Sizer 2 contine MARCA, MODELO, SECTOR, SUBSECTOR, PRODUCTO
        self.anuncio_sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.stMarca = wx.StaticText(self, label=u"MARCA")
        self.stMarca.SetFont(fuenteNormal)
        self.anuncio_sizer2.Add(self.stMarca, flag=wx.LEFT, border=10)
        self.txMarca = wx.TextCtrl(self)
        self.anuncio_sizer2.Add(self.txMarca, flag=wx.LEFT, border=10)

        self.stModelo = wx.StaticText(self, label=u"MODELO")
        self.stModelo.SetFont(fuenteNormal)
        self.anuncio_sizer2.Add(self.stModelo, flag=wx.LEFT, border=10)
        self.txModelo = wx.TextCtrl(self)
        self.anuncio_sizer2.Add(self.txModelo, flag=wx.LEFT, border=10)

        self.stSector = wx.StaticText(self, label=u"SECTOR")
        self.stSector.SetFont(fuenteNormal)
        self.anuncio_sizer2.Add(self.stSector, flag=wx.LEFT, border=10)

        self.stSubsector = wx.StaticText(self, label=u"SUBSECTOR")
        self.stSubsector.SetFont(fuenteNormal)
        self.anuncio_sizer2.Add(self.stSubsector, flag=wx.LEFT, border=130)

        self.stProducto = wx.StaticText(self, label=u"PRODUCTO")
        self.stProducto.SetFont(fuenteNormal)
        self.anuncio_sizer2.Add(self.stProducto, flag=wx.LEFT, border=130)

        self.anunciomainSizer.Add(self.anuncio_sizer2, 1, wx.LEFT, 0)
        # Fin Sizer 2
        # -------------------------------------------------------------------------------
        # Sizer 3 contiene los combobox asociados a MARCA, MODELO, SECTOR, SUBSECTOR y PRODUCTO
        self.anuncio_sizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.cbMarca = wx.ComboBox(self, size=(179, 25), choices=[],
                                   style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.cbMarca.Bind(wx.EVT_COMBOBOX, self.onSelectMarca)
        self.anuncio_sizer3.Add(self.cbMarca, flag=wx.LEFT, border=10)

        self.cbModelo = wx.ComboBox(self, size=(189, 25), choices=[],
                                    style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.cbModelo.Bind(wx.EVT_COMBOBOX, self.onSelectModelo)
        self.anuncio_sizer3.Add(self.cbModelo, flag=wx.LEFT, border=10)

        self.cbSector = wx.ComboBox(self, size=(185, 25), choices=[],
                                    style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.cbSector.Bind(wx.EVT_COMBOBOX, self.onSelectSector)
        self.anuncio_sizer3.Add(self.cbSector, flag=wx.LEFT, border=10)

        self.cbSubsector = wx.ComboBox(self, size=(220, 25), choices=[],
                                       style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.cbSubsector.Bind(wx.EVT_COMBOBOX, self.onSelectSubsector)
        self.anuncio_sizer3.Add(self.cbSubsector, flag=wx.LEFT, border=10)

        self.cbProducto = wx.ComboBox(self, size=(210, 25), choices=[],
                                      style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.cbProducto.Bind(wx.EVT_COMBOBOX, self.onSelectProducto)
        self.anuncio_sizer3.Add(self.cbProducto, flag=wx.LEFT, border=10)

        self.anunciomainSizer.Add(self.anuncio_sizer3, 1, wx.LEFT, 0)
        # Fin Sizer 3
        # -------------------------------------------------------------------------------
        # Sizer 4 contiene un texto con las posibilidades
        self.anuncio_sizer4 = wx.BoxSizer(wx.HORIZONTAL)

        self.stResultados = wx.StaticText(self, label=u"Resultados posibles")
        self.stResultados.SetFont(fuenteNormal)
        self.anuncio_sizer4.Add(self.stResultados, flag=wx.ALIGN_LEFT | wx.LEFT, border=10)
        self.stResultados2 = wx.StaticText(self)
        self.stResultados2.SetFont(fuenteNormal)
        self.anuncio_sizer4.Add(self.stResultados2, flag=wx.ALIGN_LEFT | wx.LEFT, border=10)

        self.stAnunciante = wx.StaticText(self, label=u"Anunciante")
        self.stAnunciante.SetFont(fuenteNormal)
        self.anuncio_sizer4.Add(self.stAnunciante, flag=wx.ALIGN_LEFT | wx.LEFT, border=238)
        self.stAnunciante2 = wx.StaticText(self)
        self.stAnunciante2.SetFont(fuenteNormal)
        self.anuncio_sizer4.Add(self.stAnunciante2, flag=wx.ALIGN_LEFT | wx.LEFT, border=10)

        self.anunciomainSizer.Add(self.anuncio_sizer4, 1, wx.ALIGN_LEFT | wx.LEFT, 0)
        # Fin Sizer 4
        # -------------------------------------------------------------------------------
        # Sizer 5 contiene los datos del programa
        self.anuncio_sizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.stGrupo = wx.StaticText(self, label=u"GRUPO")
        self.stGrupo.SetFont(fuenteNormal)
        self.anuncio_sizer5.Add(self.stGrupo, flag=wx.ALIGN_LEFT | wx.LEFT, border=10)
        self.cbGrupo = wx.ComboBox(self, size=(150, 25), choices=self.listaGrupo,
                                   style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.cbGrupo.Bind(wx.EVT_COMBOBOX, self.onSelectGrupo)
        self.anuncio_sizer5.Add(self.cbGrupo, flag=wx.LEFT, border=10)
        self.stCadena = wx.StaticText(self, label=u"CADENA")
        self.stCadena.SetFont(fuenteNormal)
        self.anuncio_sizer5.Add(self.stCadena, flag=wx.ALIGN_LEFT | wx.LEFT, border=10)
        self.cbCadena = wx.ComboBox(self, size=(150, 25), choices=self.listaCadena,
                                    style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)

        self.cbCadena.Bind(wx.EVT_COMBOBOX, self.onSelectCadena)
        self.anuncio_sizer5.Add(self.cbCadena, flag=wx.LEFT, border=10)
        self.stEmision = wx.StaticText(self, label=u"EMISIÓN")
        self.stEmision.SetFont(fuenteNormal)
        self.anuncio_sizer5.Add(self.stEmision, flag=wx.ALIGN_LEFT | wx.LEFT, border=10)
        self.cbEmision = wx.ComboBox(self, size=(150, 25), choices=self.listaEmision,
                                     style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)

        self.cbEmision.Bind(wx.EVT_COMBOBOX, self.onSelectEmision)
        self.anuncio_sizer5.Add(self.cbEmision, flag=wx.LEFT, border=10)
        self.stSoporte = wx.StaticText(self)
        self.stSoporte.SetFont(fuenteNormal)
        self.anuncio_sizer5.Add(self.stSoporte, flag=wx.LEFT, border=20)

        self.anunciomainSizer.Add(self.anuncio_sizer5, 1, wx.LEFT, 0)
        # Fin Sizer 5
        # -------------------------------------------------------------------------------
        # Sizer 6 Contiene más datos del programa
        self.anuncio_sizer6 = wx.BoxSizer(wx.HORIZONTAL)

        self.stPrograma = wx.StaticText(self, label=u"PROGRAMA")
        self.stPrograma.SetFont(fuenteNormal)
        self.anuncio_sizer6.Add(self.stPrograma, flag=wx.ALIGN_LEFT | wx.LEFT, border=10)

        self.cbPrograma = wx.ComboBox(self, size=(150, 25), choices=self.listaProgramas,
                                      style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.cbPrograma.Bind(wx.EVT_COMBOBOX, self.onSelectPrograma)
        self.anuncio_sizer6.Add(self.cbPrograma, flag=wx.LEFT, border=10)

        self.stProgramaCodi = wx.StaticText(self)
        self.stProgramaCodi.SetFont(fuenteNormal)
        self.anuncio_sizer6.Add(self.stProgramaCodi, flag=wx.ALIGN_LEFT | wx.LEFT, border=10)

        self.stProgramaH = wx.StaticText(self, label=u"HORA EMISIÓN")
        self.stProgramaH.SetFont(fuenteNormal)
        self.anuncio_sizer6.Add(self.stProgramaH, flag=wx.LEFT, border=448)

        self.stProgramaHMS = wx.StaticText(self)
        self.stProgramaHMS.SetFont(fuenteNormal)
        self.anuncio_sizer6.Add(self.stProgramaHMS, flag=wx.LEFT, border=10)

        self.anunciomainSizer.Add(self.anuncio_sizer6, 1, wx.LEFT, 0)
        # Fin Sizer 6
        # -------------------------------------------------------------------------------
        # Sizer 7 Contiene información del anuncio
        self.anuncio_sizer7 = wx.BoxSizer(wx.HORIZONTAL)

        self.stFechaAnuncio = wx.StaticText(self, label=u"FECHA ANUNCIO")
        self.stFechaAnuncio.SetFont(fuenteNormal)
        self.anuncio_sizer7.Add(self.stFechaAnuncio, flag=wx.LEFT, border=10)

        self.stFechaAnuncio2 = wx.StaticText(self, label=unicode(self.comienzo))
        self.stFechaAnuncio2.SetFont(fuenteNormal)
        self.anuncio_sizer7.Add(self.stFechaAnuncio2, flag=wx.LEFT, border=10)

        self.anunciomainSizer.Add(self.anuncio_sizer7, 1, wx.LEFT, 0)
        # Fin Sizer 7
        # -------------------------------------------------------------------------------
        # Sizer 8 Contiene información del anuncio
        self.anuncio_sizer8 = wx.BoxSizer(wx.HORIZONTAL)

        self.stTipoAnuncio = wx.StaticText(self, label=u"TIPO ANUNCIO")
        self.stTipoAnuncio.SetFont(fuenteNormal)
        self.anuncio_sizer8.Add(self.stTipoAnuncio, flag=wx.LEFT, border=10)

        self.cbTipoAnuncio = wx.ComboBox(self, size=(150, 25), choices=self.listaTipoAnuncios,
                                         style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.anuncio_sizer8.Add(self.cbTipoAnuncio, flag=wx.LEFT, border=10)

        self.txTexto = wx.TextCtrl(self, size=(500, 25))
        self.anuncio_sizer8.Add(self.txTexto, flag=wx.LEFT, border=10)

        self.anunciomainSizer.Add(self.anuncio_sizer8, 1, wx.LEFT, 0)
        # Fin Sizer 8
        # -------------------------------------------------------------------------------
        # Sizer 9
        self.anuncio_sizer9 = wx.BoxSizer(wx.HORIZONTAL)
        self.anunciomainSizer.Add(self.anuncio_sizer9, 1, wx.LEFT, 0)

        # Sizer 10 contiene los botones de BUSCAR, RESET y GUARDAR
        self.anuncio_sizer10 = wx.BoxSizer(wx.HORIZONTAL)

        self.btBuscar = wx.Button(self, label=u"BUSCAR")
        self.btBuscar.Bind(wx.EVT_BUTTON, self.buscarAS400)
        self.anuncio_sizer10.Add(self.btBuscar, flag=wx.LEFT, border=10)

        self.btReset = wx.Button(self, label=u"RESET")
        self.btReset.Bind(wx.EVT_BUTTON, self.onReset)
        self.anuncio_sizer10.Add(self.btReset, flag=wx.LEFT, border=10)

        self.bguardar = wx.Button(self, label=u"GUARDAR")
        self.bguardar.Bind(wx.EVT_BUTTON, self.OnGuardar)
        self.anuncio_sizer10.Add(self.bguardar, 0, wx.LEFT, 10)

        self.anunciomainSizer.Add(self.anuncio_sizer10, 1, wx.LEFT | wx.CENTER, 0)

        self.iniciarDesplegables()

        self.cbGrupo.SetValue(self.grupo)
        cadenas = [x["IDSOPOR2"] for x in self.listaSoportes if x["IDSOPOR1"] == self.grupo]
        self.cbCadena.AppendItems(list(set(cadenas)))
        self.cbCadena.SetValue(self.cadena)
        emisiones = [x["IDSOPOR3"] for x in self.listaSoportes if
                     x["IDSOPOR1"] == self.cbGrupo.GetValue() and x["IDSOPOR2"] == self.cadena]
        self.cbEmision.AppendItems(list(set(emisiones)))

        self.SetSizerAndFit(self.anunciomainSizer)
        self.Layout()

    def guardar_wav(self, buffer, nombre, fs, numc):
        output = wave.open(nombre, 'w')
        output.setparams((numc, 2, fs, 1, 'NONE', 'not compressed'))
        output.writeframes(buffer)
        output.close()

    def cargarProgramas(self):

        query = "SELECT * FROM INFOCDM.cdmppo00n WHERE DIASEM = '" + self.dias_semana[
            self.comienzo.isoweekday()] + "' and RAEMIS = '" + self.emision + \
                "' AND ((PGHORA * 3600) + (PGMINT * 60)) < ((" + str(
            self.comienzo.hour) + "  * 3600) + (" + str(
            self.comienzo.minute) + " * 60)) ORDER BY PGHORA DESC, PGMINT DESC FETCH FIRST 1 ROW ONLY"

        cursor_as400.execute(query)
        columnas = [columna[0] for columna in cursor_as400.description]
        for resultado in cursor_as400.fetchall():
            self.listaProgramas.append(dict(zip(columnas, resultado)))

    def iniciarDesplegables(self):
        """
        Limpia todos los campos, resultados, etc.
        """

        self.marcaSelec = ""
        self.modeloSelec = ""
        self.sectorSelec = ""
        self.subsectorSelec = ""
        self.productoSelec = ""
        self.txMarca.Clear()
        self.txModelo.Clear()
        self.cbMarca.Clear()
        self.cbModelo.Clear()
        self.cbSector.Clear()
        self.cbSubsector.Clear()
        self.cbProducto.Clear()
        self.listaResultado = []
        self.listaSectorSubsectorProducto = []
        self.totalResultados = len(self.listaResultado)
        self.stResultados2.SetLabel("")
        self.stAnunciante2.SetLabel("")
        self.cargarSectorSubsectoProducto()
        self.cargarSoportes()
        self.cargarGrupos()
        self.cargarTipos()
        self.cargarProgramas()

    def onReset(self, event):
        """
        Limpia todos los campos, resultados, etc.
        """

        self.iniciarDesplegables()

    def limpiarCB(self):
        """
        Limpia los cinco ComboBox para buscar un anuncio
        """

        self.cbMarca.Clear()
        self.cbModelo.Clear()
        self.cbSector.Clear()
        self.cbSubsector.Clear()
        self.cbProducto.Clear()

    def actualizarCB(self):
        """
        Actualiza los cinco ComboBox con los resultados posibles una vez seleccionado al menos algún campo
        Actualiza el campo stResultados2 y si sólo queda un resultado prosible rellena todos los campos
        """

        listaMarca = []
        listaModelo = []
        listaSector = []
        listaSubsector = []
        listaProducto = []

        self.limpiarCB()

        for resultado in self.listaResultado:
            listaMarca.append(resultado["CAMARC"])
            listaModelo.append(resultado["CAMODE"])
            listaSector.append(self.convertirSectorSubsectorProducto(resultado["MRFMSC"], "   ", "   "))
            listaSubsector.append(
                self.convertirSectorSubsectorProducto(resultado["MRFMSC"], resultado["MRSUBT"], "   "))
            listaProducto.append(
                self.convertirSectorSubsectorProducto(resultado["MRFMSC"], resultado["MRSUBT"], resultado["MRPROD"]))

        listaMarca = list(set(listaMarca))
        listaModelo = list(set(listaModelo))
        listaSector = list(set(listaSector))
        listaSubsector = list(set(listaSubsector))
        listaProducto = list(set(listaProducto))

        self.cbMarca.AppendItems(listaMarca)
        self.cbModelo.AppendItems(listaModelo)
        self.cbSector.AppendItems(listaSector)
        self.cbSubsector.AppendItems(listaSubsector)
        self.cbProducto.AppendItems(listaProducto)

        self.cbMarca.SetStringSelection(self.marcaSelec)
        self.cbModelo.SetStringSelection(self.modeloSelec)
        self.cbSector.SetStringSelection(self.sectorSelec)
        self.cbSubsector.SetStringSelection(self.subsectorSelec)
        self.cbProducto.SetStringSelection(self.productoSelec)

        self.totalResultados = len(self.listaResultado)
        self.stResultados2.SetLabel(str(self.totalResultados))

        if self.totalResultados == 1:
            self.cbMarca.SetStringSelection(self.listaResultado[0]["CAMARC"])
            self.cbModelo.SetStringSelection(self.listaResultado[0]["CAMODE"])
            self.cbSector.SetStringSelection(self.convertirSectorSubsectorProducto(self.listaResultado[0]["MRFMSC"],
                                                                                   "   ", "   "))
            self.cbSubsector.SetStringSelection(self.convertirSectorSubsectorProducto(self.listaResultado[0]["MRFMSC"],
                                                                                      self.listaResultado[0]["MRSUBT"],
                                                                                      "   "))
            self.cbProducto.SetStringSelection(self.convertirSectorSubsectorProducto(self.listaResultado[0]["MRFMSC"],
                                                                                     self.listaResultado[0]["MRSUBT"],
                                                                                     self.listaResultado[0]["MRPROD"]))
            self.stAnunciante2.SetLabel(self.listaResultado[0]["MRLTAN"])

    def cargarTipos(self):
        """
        Carga los tipos de anuncios en listaTipoAnuncios
        :return:
        """

        try:
            cursor_as400.execute("SELECT * FROM INFOXXI.INFFRANUN WHERE IDMEDIOS = 'RD'")
        except:
            cursor_as400.execute("SELECT * FROM INFFRANUN WHERE IDMEDIOS = 'RD'")
        columnas = [columna[0] for columna in cursor_as400.description]
        for resultado in cursor_as400.fetchall():
            self.listaTipoAnuncios.append(dict(zip(columnas, resultado)))

        listaDesc = []
        for desc in self.listaTipoAnuncios:
            listaDesc.append(desc["CDESCRIPCI"])

        self.cbTipoAnuncio.AppendItems(listaDesc)

    def cargarSectorSubsectoProducto(self):
        """
        Carga todos los sectores, subsectores y productos en listaSectorSubsectorProducto
        """

        try:
            cursor_as400.execute("SELECT * FROM INFOCDM.CDMPPR00")
        except:
            cursor_as400.execute("SELECT * FROM CDMPPR00")
        columnas = [columna[0] for columna in cursor_as400.description]
        for resultado in cursor_as400.fetchall():
            self.listaSectorSubsectorProducto.append(dict(zip(columnas, resultado)))

    def convertirSectorSubsectorProducto(self, sector, subsector, producto):
        """
        Convierte un sector, subsector y producto en su descripción
        :param sector:
        :param subsector:
        :param producto:
        :return: descripcion(utf-8)
        """
        for x in self.listaSectorSubsectorProducto:
            if x["PRFMSC"].decode('unicode-escape') == sector and (
                        x["PRSUBT"].decode('unicode-escape') == subsector) and x["PRPROD"].decode(
                        'unicode-escape') == producto:
                desc = x["PRDESC"]
                return desc

    def extraerSectorSubsectorProducto(self, desc):
        """
        Convierte una descripción en sector, subsector y producto
        :param desc:
        :return:
        """
        lista = []
        for x in self.listaSectorSubsectorProducto:
            if x["PRDESC"].decode('unicode-escape') == desc:
                sector = x["PRFMSC"]
                subsector = x["PRSUBT"]
                producto = x["PRPROD"]
                lista.append((sector, subsector, producto))
        return lista

    def cargarSector(self):

        sectores = [x["PRDESC"] for x in self.listaSectorSubsectorProducto if x["PRSUBT"] == '' and x["PRPROD"] == '']
        for sector in sectores:
            self.listaSector.append(sector)
        self.cbSector.AppendItems(self.listaSector)

    def cargarSoportes(self):
        """
        Carga todos los soportes de radio en una lista
        """
        try:
            cursor_as400.execute("SELECT * FROM INFOXXI.INFSOPORT WHERE IDMEDIOS = 'RD'")
        except:
            cursor_as400.execute("SELECT * FROM INFSOPORT WHERE IDMEDIOS = 'RD'")
        columnas = [columna[0] for columna in cursor_as400.description]
        for resultado in cursor_as400.fetchall():
            self.listaSoportes.append(dict(zip(columnas, resultado)))

    def cargarGrupos(self):

        for soporte in self.listaSoportes:
            if not soporte["IDSOPOR1"] in self.listaGrupo:
                self.listaGrupo.append(soporte["IDSOPOR1"])
        self.cbGrupo.AppendItems(self.listaGrupo)

    def buscarAS400(self, event):
        """
        Carga los posibles resultados de la búsqueda del AS400 en listaResultado
        """

        # todo: sector, subsector, producto

        busquedaMarca = u"'%{}%'".format(self.txMarca.GetValue().upper())
        queryMarca = "SELECT * FROM CDMPMR00 WHERE CAMARC LIKE %s" % busquedaMarca

        if self.txModelo.GetValue() != "":
            busquedaModelo = u"'%{}%'".format(self.txModelo.GetValue().upper())
            queryModelo = " AND CAMODE LIKE %s" % busquedaModelo
        else:
            queryModelo = ""

        self.limpiarCB()

        query = queryMarca + queryModelo
        cursor_as400.execute(query)
        columnas = [columna[0] for columna in cursor_as400.description]
        for resultado in cursor_as400.fetchall():
            self.listaResultado.append(dict(zip(columnas, resultado)))

        self.actualizarCB()

    def onSelectPrograma(self, event):

        self.stProgramaCodi.SetLabel(unicode(self.cbPrograma.GetValue()))
        hora = [x["PGHORA"] for x in self.listaProgramas if
                x["PGNOMB"].decode('unicode-escape') == self.cbPrograma.GetValue()]
        minuto = [x["PGMINT"] for x in self.listaProgramas if
                  x["PGNOMB"].decode('unicode-escape') == self.cbPrograma.GetValue()]
        horaEmision = datetime.time(hour=int(hora[0]), minute=int(minuto[0]))
        self.stProgramaHMS.SetLabel(unicode(horaEmision))
        codigoPrograma = [x["PGCODI"] for x in self.listaProgramas if
                          x["PGNOMB"].decode('unicode-escape') == self.cbPrograma.GetValue()]
        self.codigoPrograma = codigoPrograma[0]

    def onSelectGrupo(self, event):

        self.cbCadena.Clear()
        self.cbEmision.Clear()
        cadenas = [x["IDSOPOR2"] for x in self.listaSoportes if
                   x["IDSOPOR1"] == self.cbGrupo.GetValue()]
        self.cbCadena.AppendItems(list(set(cadenas)))

    def onSelectCadena(self, event):

        self.cbEmision.Clear()
        emisiones = [x["IDSOPOR3"] for x in self.listaSoportes if
                     x["IDSOPOR1"] == self.cbGrupo.GetValue() and x["IDSOPOR2"] == self.cbCadena.GetValue()]
        self.cbEmision.AppendItems(list(set(emisiones)))

    def onSelectEmision(self, event):

        soporte = [x["CDESCRIPCI"] for x in self.listaSoportes if
                   x["IDSOPOR1"] == self.cbGrupo.GetValue() and x["IDSOPOR2"] == self.cbCadena.GetValue() and x[
                       "IDSOPOR3"] == self.cbEmision.GetValue()]
        self.stSoporte.SetLabel(unicode(soporte[0]))

        programas = [x["PGNOMB"] for x in self.listaProgramas if
                     x["RAONDA"] == self.cbGrupo.GetValue() and x["RACADN"] == self.cbCadena.GetValue() and x[
                         "RAEMIS"] == self.cbEmision.GetValue() and x["PGHORA"] < self.comienzo.hour]
        self.cbPrograma.AppendItems(list(set(programas)))

    def onSelectMarca(self, event):
        """
        Actualiza listaResultado en función de la marca seleccionada
        :param event: not used
        :return: not used
        """

        nuevaListaResultado = []
        self.marcaSelec = self.cbMarca.GetValue()
        for resultado in self.listaResultado:
            if resultado["CAMARC"].decode('unicode-escape') == self.marcaSelec:
                nuevaListaResultado.append(resultado)
        self.listaResultado = nuevaListaResultado
        self.actualizarCB()

    def onSelectModelo(self, event):
        """
        Actualiza listaResultado en función del modelo seleccionado
        :param event: not used
        :return: not used
        """

        nuevaListaResultado = []
        self.modeloSelec = self.cbModelo.GetValue()
        for resultado in self.listaResultado:
            if resultado["CAMODE"].decode('unicode-escape') == self.modeloSelec:
                nuevaListaResultado.append(resultado)
        self.listaResultado = nuevaListaResultado
        self.actualizarCB()

    def onSelectSector(self, event):
        """
        Actualiza listaResultado en función del sector seleccionado
        :param event: not used
        :return: not used
        """

        nuevaListaResultado = []
        self.sectorSelec = self.cbSector.GetValue()
        for resultado in self.listaResultado:
            l = self.extraerSectorSubsectorProducto(self.sectorSelec)
            for i in l:
                sector, subsector, producto = i
                if resultado["MRFMSC"].decode('unicode-escape') == sector:
                    nuevaListaResultado.append(resultado)
        self.listaResultado = nuevaListaResultado
        self.actualizarCB()

    def onSelectSubsector(self, event):
        """
        Actualiza listaResultado en función del subsector seleccionado
        :param event: not used
        :return: not used
        """

        nuevaListaResultado = []
        self.subsectorSelec = self.cbSubsector.GetValue()
        for resultado in self.listaResultado:
            l = self.extraerSectorSubsectorProducto(self.subsectorSelec)
            for i in l:
                sector, subsector, producto = i
                if resultado["MRFMSC"].decode('unicode-escape') == sector and resultado["MRSUBT"].decode(
                        'unicode-escape') == subsector:
                    nuevaListaResultado.append(resultado)
        self.listaResultado = nuevaListaResultado
        self.actualizarCB()

    def onSelectProducto(self, event):
        """
        Actualiza listaResultado en función del producto seleccionado
        :param event: not used
        :return: not used
        """

        nuevaListaResultado = []
        self.productoSelec = self.cbProducto.GetValue()
        for resultado in self.listaResultado:
            l = self.extraerSectorSubsectorProducto(self.productoSelec)
            for i in l:
                sector, subsector, producto = i
                if resultado["MRFMSC"].decode('unicode-escape') == sector and resultado["MRSUBT"].decode(
                        'unicode-escape') == subsector and resultado["MRPROD"].decode('unicode-escape') == producto:
                    nuevaListaResultado.append(resultado)
        self.listaResultado = nuevaListaResultado
        self.actualizarCB()

    def OnGuardar(self, event):
        anuncio = self.listaResultado[0]
        longitud_anuncio = (len(self.audio) / 44100)

        try:
            self.cursorMySQL.execute(
                "SELECT `auto_increment` FROM INFORMATION_SCHEMA.TABLES WHERE table_name = 'songs';")
            last_id = self.cursorMySQL.fetchone()[0]
        except:
            last_id = 20000000

        anuncio["NOMBRE"] = unicode("{}_{}_{}_{}").format(anuncio["CAMARC"].decode('unicode-escape'),
                                                          anuncio["CAMODE"].decode('unicode-escape'),
                                                          str(longitud_anuncio), str(last_id))
        anuncio["TIPO ANUNCIO"] = self.cbTipoAnuncio.GetValue()
        anuncio["TEXTO"] = self.txTexto.GetValue()
        anuncio["CAMARC"] = unicode("{}").format(anuncio["CAMARC"].decode('unicode-escape'))
        anuncio["CAMODE"] = unicode("{}").format(anuncio["CAMODE"].decode('unicode-escape'))
        self.djv.fingerprint_audio(datetime.datetime.now(), self.audio, self.fs, anuncio["NOMBRE"],
                                   anuncio["TIPO ANUNCIO"], anuncio["TEXTO"],
                                   'RD', self.cbGrupo.GetValue(), self.cbCadena.GetValue(), self.cbEmision.GetValue(),
                                   self.comienzo.year, self.comienzo.month, self.comienzo.day,
                                   self.comienzo.hour, self.comienzo.minute, self.comienzo.second,
                                   anuncio["MRABRE"], anuncio["CAMARC"], anuncio["CAMODE"],
                                   anuncio["MRCOMP"], "", last_id, self.nombre_cinta)
        self.db.commit()
        self.cursorMySQL.execute("SELECT song_id FROM songs WHERE song_name = %s;", (anuncio["NOMBRE"],))
        id = self.cursorMySQL.fetchone()
        if id is None:
            anuncio["ID"] = 999999
        else:
            anuncio["ID"] = id[0]

        self.cursorMySQL.execute(
            "INSERT INTO ocurrencias (fecha_anuncio, id_anuncio, emisora_anuncio, duracion_anuncio, nombre_cinta, "
            "confidence, codigo_medio, grupo, cadena, emision, anho, mes, dia, hora, minuto, segundo, "
            "codigo_marca_modelo, nombre_marca, nombre_modelo, compartido, forma_publicidad, total_inserciones_bloque, "
            "numero_insercion_dentro_bloque, codigo_programa, codigo_marketing_directo, codigo_operador, "
            "codigo_version, descripcion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
            "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (datetime.datetime.now(), anuncio["ID"], self.emisora, longitud_anuncio, self.nombre_cinta, self.confidence,
             'RD',
             self.cbGrupo.GetValue(), self.cbCadena.GetValue(), self.cbEmision.GetValue(), self.comienzo.year,
             self.comienzo.month, self.comienzo.day, self.comienzo.hour, self.comienzo.minute,
             self.comienzo.second, anuncio["MRABRE"], anuncio["CAMARC"], anuncio["CAMODE"],
             anuncio["MRCOMP"], "", "", "", self.codigoPrograma, "", "", anuncio["ID"], anuncio["TEXTO"]))
        self.db.commit()

        datos_anuncios, bloquecambiado = VistaSpot.insertanuevoanuncio(self.bloques_ordenados, self.archivo,
                                                                       self.comienzo, self.final,
                                                                       self.datos_anuncios,
                                                                       anuncio, self.fecha)

        self.m_a.SetDatos(datos_anuncios)

        nombre_wav = os.path.join(self.ruta, anuncio["NOMBRE"].replace("/", "-") + '.wav')
        self.guardar_wav(self.segmento, nombre_wav, self.fs, 1)

        self.Destroy()


if __name__ == '__main__':
    class TrialPanel(wx.Panel):
        def __init__(self, parent):
            def onButton(self):
                anund = AnuncioDialog("C:/archivos/20151008080000.wav", 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
                anund.SetPosition((200, 200))
                anund.Show()

            wx.Panel.__init__(self, parent, wx.ID_ANY)

            bcomprobar = wx.Button(self, label="AnuncioDialog")
            bcomprobar.Bind(wx.EVT_BUTTON, onButton)


    app = wx.App()
    frame = wx.Frame(None, -1, 'Trial Panel')
    TrialPanel(frame)
    frame.Show()
    # wx.lib.inspection.InspectionTool().Show()
    app.MainLoop()
