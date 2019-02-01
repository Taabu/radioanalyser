# coding=utf-8
# __author__ = 'Mario Romera Fernández'

import wx
import wx.dataview as dv
import datetime
import dateutil.parser
from MySQLdb.cursors import DictCursor
import os
import numpy as np
from varsUtilsCaptorRadioV2 import cargar_conexion_mysql_infoadex, cargar_djv_infoadex

cnx_mysql = cargar_conexion_mysql_infoadex()
cursor_mysql = cnx_mysql.cursor(DictCursor)

djv = cargar_djv_infoadex()


class Anuncio(object):
    def __init__(self, id, marca, modelo, bloque, inicio, final):
        self.id = id
        self.marca = marca
        self.modelo = modelo
        self.bloque = bloque
        self.inicio = inicio
        self.final = final

    def __repr__(self):
        return 'Anuncio: %s-%s' % (self.marca, self.inicio)


class Bloque(object):
    def __init__(self, nombre):
        self.nombre = nombre
        self.anuncios = []

    def __repr__(self):
        return 'Bloque: ' + self.nombre


class MyTreeListModel(dv.PyDataViewModel):
    def __init__(self, data):
        dv.PyDataViewModel.__init__(self)
        self.data = data

        # The objmapper is an instance of DataViewItemObjectMapper and is used
        # to help associate Python objects with DataViewItem objects. Normally
        # a dictionary is used so any Python object can be used as data nodes.
        # If the data nodes are weak-referencable then the objmapper can use a
        # WeakValueDictionary instead. Each PyDataViewModel automagically has
        # an instance of DataViewItemObjectMapper preassigned. This
        # self.objmapper is used by the self.ObjectToItem and
        # self.ItemToObject methods used below.
        self.objmapper.UseWeakRefs(True)

    # Report how many columns this model provides data for.
    def GetColumnCount(self):
        return 6

    # Map the data column numbers to the data type
    def GetColumnType(self, col):
        mapper = {0: 'string',
                  1: 'string',
                  2: 'string',
                  3: 'string',  # the real value is an int, but the renderer should convert it okay
                  4: 'string',  # antes DATETIME pero es un lio los formatos
                  5: 'string'
                  }
        return mapper[col]

    def GetChildren(self, parent, children):
        # The view calls this method to find the children of any node in the
        # control. There is an implicit hidden root node, and the top level
        # item(s) should be reported as children of this node. A List view
        # simply provides all items as children of this hidden root. A Tree
        # view adds additional items as children of the other items, as needed,
        # to provide the tree hierachy.
        ##self.log.write("GetChildren\n")

        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for bloque in self.data:
                children.append(self.ObjectToItem(bloque))
            return len(self.data)

        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Bloque):
            for anuncio in node.anuncios:
                children.append(self.ObjectToItem(anuncio))
            return len(node.anuncios)
        return 0

    def IsContainer(self, item):
        # Return True if the item has children, False otherwise.
        ##self.log.write("IsContainer\n")

        # The hidden root is a container
        if not item:
            return True
        # and in this model the genre objects are containers
        node = self.ItemToObject(item)
        if isinstance(node, Bloque):
            return True
        # but everything else (the song objects) are not
        return False

    def HasContainerColumns(self, item):
        # self.log.write('HasContainerColumns\n')
        return True

    def GetParent(self, item):
        # Return the item which is this item's parent.
        ##self.log.write("GetParent\n")

        if not item:
            return dv.NullDataViewItem

        node = self.ItemToObject(item)
        if isinstance(node, Bloque):
            return dv.NullDataViewItem
        elif isinstance(node, Anuncio):
            for g in self.data:
                if g.nombre == node.bloque:
                    return self.ObjectToItem(g)

    def GetValue(self, item, col):
        # Return the value to be displayed for this item and column. For this
        # example we'll just pull the values from the data objects we
        # associated with the items in GetChildren.

        # Fetch the data object for this item.
        node = self.ItemToObject(item)

        if isinstance(node, Bloque):
            # We'll only use the first column for the Genre objects,
            # for the other columns lets just return empty values
            mapper = {0: node.nombre,
                      1: "",
                      2: "",
                      3: "",  # wx.DateTimeFromTimeT(0),
                      4: "",  # wx.DateTimeFromTimeT(0),
                      5: ""  # wx.DateTimeFromTimeT(0),
                      }
            return mapper[col]


        elif isinstance(node, Anuncio):
            mapper = {0: node.bloque,
                      1: node.inicio,
                      2: node.final,
                      3: node.marca,
                      4: node.modelo,
                      5: node.id
                      }

            return mapper[col]

        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        ##self.log.write('GetAttr')

        node = self.ItemToObject(item)
        if isinstance(node, Bloque):
            attr.SetColour('blue')
            attr.SetBold(True)
            return True
        return False

    def Compare(self, item1, item2, col, ascending):
        if not ascending:  # swap sort order?
            item2, item1 = item1, item2
        node1 = self.ItemToObject(item1)

        node2 = self.ItemToObject(item2)
        if isinstance(node1, Bloque):
            lista1 = [x.inicio for x in node1.anuncios]
            lista2 = [x.inicio for x in node2.anuncios]
            return cmp(lista1, lista2)
        elif isinstance(node1, Anuncio):
            return cmp(node1.inicio, node2.inicio)


class PanelAnuncios(wx.Panel):
    def __init__(self, parent, data=None, model=None):

        wx.Panel.__init__(self, parent, size=(600, 250))

        self.anuncio = None
        self.parent = parent
        self.dvc = dv.DataViewCtrl(self,
                                   style=wx.BORDER_THEME
                                         | dv.DV_ROW_LINES
                                         | dv.DV_VERT_RULES
                                         | dv.DV_MULTIPLE
                                   )

        self.model = None
        if model is None:
            if data:
                self.model = MyTreeListModel(data)
        else:
            self.model = model

        # Tel the DVC to use the model
        if self.model:
            self.dvc.AssociateModel(self.model)

        self.tr = tr = dv.DataViewTextRenderer()
        c0 = dv.DataViewColumn("Bloque",  # title
                               tr,  # renderer
                               0,  # data model column
                               width=250)
        self.dvc.AppendColumn(c0)
        # else:
        # self.dvc.AppendTextColumn("Bloque",   0, width=80)


        c3 = self.dvc.AppendTextColumn('Inicio', 1, width=200, mode=dv.DATAVIEW_CELL_ACTIVATABLE)
        c4 = self.dvc.AppendTextColumn('Final', 2, width=200, mode=dv.DATAVIEW_CELL_ACTIVATABLE)

        c1 = self.dvc.AppendTextColumn("Anuncio", 3, width=300, mode=dv.DATAVIEW_CELL_ACTIVATABLE)
        c2 = self.dvc.AppendTextColumn("Marca", 4, width=150, mode=dv.DATAVIEW_CELL_ACTIVATABLE)

        c5 = self.dvc.AppendTextColumn("id", 5, width=40, mode=dv.DATAVIEW_CELL_ACTIVATABLE)

        # Notice how we pull the data from col 3, but this is the 6th col
        # added to the DVC. The order of the view columns is not dependent on
        # the order of the model columns at all.

        # c5.Alignment = wx.ALIGN_RIGHT


        # Set some additional attributes for all the columns

        for i, c in enumerate(self.dvc.Columns):
            c.Sortable = True
            c.Reorderable = True

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.dvc, 1, wx.EXPAND)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnClick)

        b1 = wx.Button(self, label="Vista Completa", name="vistacompleta")
        self.Bind(wx.EVT_BUTTON, self.OnNewView, b1)

        self.Sizer.Add(b1, 0, wx.ALL, 5)

    def SetDatos(self, data):
        self.data = data
        self.model = MyTreeListModel(self.data)
        self.dvc.AssociateModel(self.model)
        col1 = self.dvc.GetColumn(1)
        col1.SetSortOrder(True)
        # col1=self.dvc.GetColumn(0)
        # col1.SetSortOrder(True)
        # self.model.Resort()
        if self.model:
            self.model.Resort()

    def OnClick(self, evt):

        # print evt.GetColumn()

        self.anuncio = dv.PyDataViewModel.ItemToObject(self.model, evt.GetItem())
        # print self.anuncio.inicio
        try:
            self.parent.anuncioseleccionado['inicio'] = self.anuncio.inicio
            self.parent.anuncioseleccionado['final'] = self.anuncio.final
            self.parent.anuncioseleccionado['bloque'] = self.anuncio.bloque
            self.parent.anuncioseleccionado['marca'] = self.anuncio.marca
            self.parent.anuncioseleccionado['modelo'] = self.anuncio.modelo
            print self.parent.anuncioseleccionado
            dateinicio = dateutil.parser.parse(self.anuncio.inicio)
            datefinal = dateutil.parser.parse(self.anuncio.final)
            print dateinicio
            print self.parent.inicio_grabacion
            print (dateinicio - self.parent.inicio_grabacion).total_seconds()
            if (dateinicio - self.parent.inicio_grabacion).total_seconds() > 3600 or (
                dateinicio - self.parent.inicio_grabacion).total_seconds() < 1:
                print 'error en el anuncio por tiempo'
                return

            self.parent.mediaPlayer.Seek((dateinicio - self.parent.inicio_grabacion).total_seconds() * 1000)
            self.parent.graf.cambiar_ejes((dateinicio - self.parent.inicio_grabacion).total_seconds(),
                                          (datefinal - self.parent.inicio_grabacion).total_seconds())
        except:
            print 'error en el anuncio seleccionado'

    def OnNewView(self, evt):

        f = wx.Frame(None, title="Nueva vista del panel de anuncios", size=(600, 400))
        PanelAnuncios(f, model=self.model)
        b = f.FindWindowByName("vistacompleta")
        b.Disable()
        f.Show()


def insertanuevoanuncio(bloques, nombrecinta, comienzo, final, datos, spot, comienzograbacion):
    cambiabloque = True
    limitebloques = []
    rutacinta, nomcinta = os.path.split(nombrecinta)
    data = dict()
    for i in datos:
        data[i.nombre] = i

    nombrecomun = nomcinta.split('.')[0] + '_bloque'
    if not bloques:
        # COGEMOS EL PRIMER ANUNCIO Y LE ASIGNAMOS BLOQUE 1, A PARTIR DE AQUI SE ORGANIZARAN LOS DEMAS
        print 'no hay bloques'

        bloquedelanuncio = nombrecomun + '1'
        print 'nuevo anuncio', comienzo, final

        anuncio = Anuncio(spot["ID"], spot["NOMBRE"], spot["CAMARC"], bloquedelanuncio,
                          comienzo.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))

        bloque = data.get(anuncio.bloque)

        if bloque is None:
            bloque = Bloque(anuncio.bloque)
            data[anuncio.bloque] = bloque
        bloque.anuncios.append(anuncio)
        bloques.append((bloquedelanuncio.decode('utf-8'), (comienzo, final)))


    else:
        for limites in bloques:
            limitebloques.append(limites[1][0])
            limitebloques.append(limites[1][1])
        for indice, b in enumerate(bloques):
            if comienzo > b[1][0]:

                if final < b[1][1]:
                    anuncio = Anuncio(spot["ID"], spot["NOMBRE"], spot["CAMARC"], b[0],
                                      comienzo.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))

                    bloque = data.get(anuncio.bloque)
                    if bloque is None:
                        bloque = Bloque(anuncio.bloque)
                        data[anuncio.bloque] = bloque
                    bloque.anuncios.append(anuncio)

                    cambiabloque = False

        if cambiabloque:
            print 'anuncio fuera de bloques'
            iniciof = comienzo
            finalf = final

            # minima distancia a inicio de un bloque
            bloquefuera_inicio = np.argmin([abs(x - iniciof) for x in limitebloques])
            bloquefuera_final = np.argmin([abs(x - finalf) for x in limitebloques])

            if bloquefuera_inicio == bloquefuera_final:
                # el numero del bloque se coge de la parte entera de la division por 2 por ser inicio, final, inicio, final...
                bnum = bloquefuera_inicio / 2

                if iniciof < bloques[bnum][1][0]:

                    if (bloques[bnum][1][0] - iniciof).seconds > 120:
                        print 'otro bloque'

                        bloques.insert(bnum, (u'bloquex', (
                        iniciof - datetime.timedelta(seconds=80), finalf + datetime.timedelta(seconds=80))))

                        bloqueantes = comienzograbacion
                        for num, blq in enumerate(bloques):

                            bloquei = blq[1][0]
                            bloquef = blq[1][1]
                            print "bloquei {} {}".format(bloquei, type(bloquei))
                            print "comienzograbacion {} {}".format(comienzograbacion, type(comienzograbacion))
                            if bloquei < comienzograbacion:
                                bloquei = comienzograbacion
                            elif bloquei < bloqueantes:
                                print 'BLOQUES SUPERPUESTOS!!'
                                bloquei = bloqueantes + datetime.timedelta(seconds=10)
                            if bloquef > comienzograbacion + datetime.timedelta(seconds=3600):
                                bloquef = comienzograbacion + datetime.timedelta(seconds=3590)
                            bloques[num] = (nombrecomun + unicode(num + 1), (bloquei, bloquef))
                            bloqueantes = bloquef

                        # cambiar data y objeto bloque
                        datan = dict()
                        for blq in data:
                            if int(blq[-1]) >= bnum + 1:
                                bloquen = data[blq]
                                nombren = blq[:-1] + unicode(int(blq[-1]) + 1)
                                for anun in bloquen.anuncios:
                                    anun.bloque = nombren
                                bloquen.nombre = nombren
                                datan[nombren] = bloquen
                            else:
                                datan[blq] = data[blq]

                        data = datan

                        anuncio = Anuncio(spot['ID'], spot['NOMBRE'], spot["CAMARC"], bloques[bnum][0],
                                          iniciof.strftime("%d/%m/%Y %H:%M:%S"), finalf.strftime("%d/%m/%Y %H:%M:%S"))

                        bloque = data.get(anuncio.bloque)

                        if bloque is None:
                            bloque = Bloque(anuncio.bloque)
                            data[anuncio.bloque] = bloque
                        bloque.anuncios.append(anuncio)
                    else:
                        bloques[bnum] = (
                        bloques[bnum][0], (iniciof - +datetime.timedelta(seconds=90), bloques[bnum][1][1]))
                        anuncio = Anuncio(spot['ID'], spot['NOMBRE'], spot["CAMARC"], bloques[bnum][0],
                                          iniciof.strftime("%d/%m/%Y %H:%M:%S"), finalf.strftime("%d/%m/%Y %H:%M:%S"))

                        bloque = data.get(anuncio.bloque)

                        if bloque is None:
                            bloque = Bloque(anuncio.bloque)
                            data[anuncio.bloque] = bloque
                        bloque.anuncios.append(anuncio)


                else:

                    if iniciof > bloques[bnum][1][1] and finalf > bloques[bnum][1][1] and (
                        finalf - bloques[bnum][1][1]).seconds > 120:
                        print 'otro bloque posterior'
                        print iniciof
                        print finalf
                        print bloques[bnum][1][0]
                        print bloques[bnum][1][1]
                        bloques.insert(bnum + 1, (u'bloquex', (
                        iniciof - datetime.timedelta(seconds=50), finalf + datetime.timedelta(seconds=50))))

                        bloqueantes = comienzograbacion
                        for num, blq in enumerate(bloques):

                            bloquei = blq[1][0]
                            bloquef = blq[1][1]
                            if bloquei < comienzograbacion:
                                bloquei = comienzograbacion
                            elif bloquei < bloqueantes:
                                print 'BLOQUES SUPERPUESTOS!!'
                                bloquei = bloqueantes + datetime.timedelta(seconds=10)
                            if bloquef > comienzograbacion + datetime.timedelta(seconds=3600):
                                bloquef = comienzograbacion + datetime.timedelta(seconds=3590)
                            bloques[num] = (nombrecomun + unicode(num + 1), (bloquei, bloquef))
                            bloqueantes = bloquef

                        datan = dict()
                        datan[nombrecomun + unicode(bnum + 2)] = Bloque(nombrecomun + unicode(bnum + 2))
                        for blq in data:
                            if int(blq[-1]) > bnum + 1:
                                bloquen = data[blq]
                                nombren = blq[:-1] + unicode(int(blq[-1]) + 1)
                                for anun in bloquen.anuncios:
                                    anun.bloque = nombren
                                bloquen.nombre = nombren
                                datan[nombren] = bloquen

                            else:
                                datan[blq] = data[blq]

                        data = datan

                        anuncio = Anuncio(spot['ID'], spot['NOMBRE'], spot["CAMARC"], bloques[bnum + 1][0],
                                          iniciof.strftime("%d/%m/%Y %H:%M:%S"), finalf.strftime("%d/%m/%Y %H:%M:%S"))

                        bloque = data.get(anuncio.bloque)

                        if bloque is None:
                            bloque = Bloque(anuncio.bloque)
                            data[anuncio.bloque] = bloque
                        bloque.anuncios.append(anuncio)

                    else:
                        bloques[bnum] = (
                        bloques[bnum][0], (bloques[bnum][1][0], finalf + datetime.timedelta(seconds=90)))

                        anuncio = Anuncio(spot['ID'], spot['NOMBRE'], spot["CAMARC"], bloques[bnum][0],
                                          iniciof.strftime("%d/%m/%Y %H:%M:%S"), finalf.strftime("%d/%m/%Y %H:%M:%S"))

                        bloque = data.get(anuncio.bloque)

                        if bloque is None:
                            bloque = Bloque(anuncio.bloque)
                            data[anuncio.bloque] = bloque
                        bloque.anuncios.append(anuncio)

            elif bloquefuera_inicio % 2 != 0:

                # el final se acerca a otro bloque o al reves, unimos bloques
                # union de bloques complicada
                print 'union de bloques'
                bnuminicio = bloquefuera_inicio / 2
                bnumfinal = bloquefuera_final / 2

                bloques[bnuminicio] = (bloques[bnuminicio][0], (bloques[bnuminicio][1][0], bloques[bnumfinal][1][1]))

                anuncio = Anuncio(spot['ID'], spot['NOMBRE'], spot["CAMARC"], bloques[bnuminicio][0],
                                  iniciof.strftime("%d/%m/%Y %H:%M:%S"), finalf.strftime("%d/%m/%Y %H:%M:%S"))

                bloque = data.get(anuncio.bloque)
                if bloque is None:
                    bloque = Bloque(anuncio.bloque)
                    data[anuncio.bloque] = bloque
                bloque.anuncios.append(anuncio)

                # hay que cambiar los nombres de bloques
                # y pasar los anuncios al nuevo bloque suma
                # YA NO ESTA EL BLOQUE BNUMFINAL +1
                # QUE ES EL bloques[0][0][:-1]++unicode(bnumfinal)
                bloquenomaquitar = bloques[0][0][:-1] + unicode(bnumfinal + 1)
                bloqueaunir = bloques[0][0][:-1] + unicode(bnumfinal)
                bloques.pop(bnumfinal)

                print 'bloque ya quitado de lista de bloques', bloquenomaquitar
                bloqueaquitar = data.get(bloquenomaquitar)
                for anun in bloqueaquitar.anuncios:  # lista con los anuncios a trasladar

                    anun.bloque = bloqueaunir
                    bloque.anuncios.append(anun)

                #
                # quitamos nombre de bloque eliminado
                for indi, bli in enumerate(bloques):
                    if bli[0].split('bloque')[1] != unicode(indi + 1):
                        print 'cambio de bloques'
                        bloques[indi] = (
                        bloques[indi][0][:-1] + unicode(indi + 1), (bloques[indi][1][0], bloques[indi][1][1]))

                data.pop(bloquenomaquitar)
                # CORRER NOMBRES DE BLOQUE

                for blqs in data.values():
                    if int(blqs.nombre[-1]) > bnumfinal + 1:
                        nomnuevo = blqs.nombre[:-1] + unicode(int(blqs.nombre[-1]) - 1)
                        data[nomnuevo] = data.pop(blqs.nombre)
                        blqs.nombre = nomnuevo
                        # estamos ante un tipo bloque con el nombre mal
                        for an in blqs.anuncios:
                            an.bloque = nomnuevo

    data = data.values()
    if cambiabloque:
        return data, bloques
    else:
        return data, None


def recuperadatos(bloques, nombrecinta, comienzograbacion):
    print 'en recuperadatos'
    print nombrecinta
    cambiabloque = False

    rutacinta, nomcinta = os.path.split(nombrecinta)
    try:
        cursor_mysql.execute("select * from ocurrencias WHERE nombre_cinta = '%s'" % os.path.splitext(nomcinta)[0])
        anuncios = cursor_mysql.fetchall()
        anuncios = list(anuncios)
        print "anuncios {}".format(anuncios)
    except:
        print 'ERROR EN LA CARGA DE DATOS DE ANUNCIOS'
        return
    print 'datosanuncios de db conseguidos'

    limitebloques = []
    listafuera = []
    data = dict()
    nombrecomun = nomcinta.split('.')[0] + '_bloque'

    if not bloques:
        # COGEMOS EL PRIMER ANUNCIO Y LE ASIGNAMOS BLOQUE 1, A PARTIR DE AQUI SE ORGANIZARAN LOS DEMAS
        print 'no hay bloques'
        j = anuncios[0]
        # inicio = datetime.datetime(year=int(j["anho"]), month=int(j["mes"]), day=int(j["dia"]), hour=int(j["hora"]), minute=int(j["minuto"]), second=int(j["segundo"]))
        inicio = j["fecha_ocurrencia"]
        final = inicio + datetime.timedelta(seconds=j['duracion_anuncio'])
        bloquedelanuncio = nombrecomun + '1'
        print 'nuevo anuncio', inicio, final

        cursor_mysql.execute("select * from songs where song_id = %i" % j['id_anuncio'])
        adb = cursor_mysql.fetchall()[0]
        try:
            anuncio = Anuncio(j['ID'], adb['NOMBRE'], adb["CAMARC"], bloquedelanuncio,
                              inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
        except:
            anuncio = Anuncio(j['id_anuncio'], adb["song_name"], adb["nombre_marca"], bloquedelanuncio,
                              inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))

        bloque = data.get(anuncio.bloque)

        if bloque is None:
            bloque = Bloque(anuncio.bloque)
            data[anuncio.bloque] = bloque
        bloque.anuncios.append(anuncio)
        bloques.append((bloquedelanuncio.decode('utf-8'), (inicio, final)))
        anuncios.pop(0)

    for limites in bloques:
        limitebloques.append(limites[1][0])
        limitebloques.append(limites[1][1])

    for i in anuncios:

        colocado = False
        inicio = i["fecha_ocurrencia"]
        final = inicio + datetime.timedelta(seconds=i['duracion_anuncio'])
        print 'nuevo anuncio', inicio, final
        if i['id_anuncio'] == 485 or i['confidence'] < 100:
            print 'cuerpo libre'
            pass
        else:
            for indice, b in enumerate(bloques):
                if inicio > b[1][0]:

                    if final < b[1][1]:
                        cursor_mysql.execute("select * from songs where song_id = %i" % i['id_anuncio'])
                        adb = cursor_mysql.fetchall()[0]
                        bloquedelanuncio = b[0]
                        try:
                            anuncio = Anuncio(i['ID'], adb['NOMBRE'], adb["CAMARC"], bloquedelanuncio,
                                              inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                        except:
                            anuncio = Anuncio(i['id_anuncio'], adb["song_name"], adb["nombre_marca"], bloquedelanuncio,
                                              inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))

                        bloque = data.get(anuncio.bloque)

                        if bloque is None:
                            bloque = Bloque(anuncio.bloque)
                            data[anuncio.bloque] = bloque
                        bloque.anuncios.append(anuncio)
                        print bloque
                        colocado = True

            if not colocado:
                cambiabloque = True
                listafuera.append(i)

    for fuera in listafuera:
        print '\n'
        print fuera
        iniciof = fuera["fecha_ocurrencia"]
        finalf = iniciof + datetime.timedelta(seconds=fuera['duracion_anuncio'])
        del limitebloques[:]
        limitebloques = []
        print 'bloques', bloques
        for limites in bloques:
            limitebloques.append(limites[1][0])
            limitebloques.append(limites[1][1])
        print 'limitebloques', limitebloques
        # minima distancia a inicio de un bloque
        bloquefuera_inicio = np.argmin([abs(x - iniciof) for x in limitebloques])
        bloquefuera_final = np.argmin([abs(x - finalf) for x in limitebloques])
        print bloquefuera_inicio
        print bloquefuera_final
        if bloquefuera_inicio == bloquefuera_final:
            # el numero del bloque se coge de la parte entera de la division por 2 por ser inicio, final, inicio, final
            bnum = bloquefuera_inicio / 2
            # print 'estamos cerca del bloque', bnum-1,iniciof

            if iniciof < bloques[bnum][1][0]:
                print 'empieza antes... mucho antes?'
                print iniciof
                print bloques[bnum][1][0]
                # print bloques
                if (bloques[bnum][1][0] - iniciof).seconds > 120:
                    print 'otro bloque'

                    bloques.insert(bnum, (
                    u'bloquex', (iniciof - datetime.timedelta(seconds=80), finalf + datetime.timedelta(seconds=80))))

                    bloqueantes = comienzograbacion
                    for num, blq in enumerate(bloques):

                        bloquei = blq[1][0]
                        bloquef = blq[1][1]
                        if bloquei < comienzograbacion:
                            bloquei = comienzograbacion
                        elif bloquei < bloqueantes:
                            print 'BLOQUES SUPERPUESTOS!!'
                            bloquei = bloqueantes + datetime.timedelta(seconds=10)
                        if bloquef > comienzograbacion + datetime.timedelta(seconds=3600):
                            bloquef = comienzograbacion + datetime.timedelta(seconds=3590)
                        bloques[num] = (nombrecomun + unicode(num + 1), (bloquei, bloquef))
                        bloqueantes = bloquef

                    print 'ya ta previo', bloques
                    print data
                    # cambiar data y objeto bloque
                    datan = dict()
                    for blq in data:
                        if int(blq[-1]) >= bnum + 1:
                            bloquen = data[blq]
                            nombren = blq[:-1] + unicode(int(blq[-1]) + 1)
                            for anun in bloquen.anuncios:
                                anun.bloque = nombren
                            bloquen.nombre = nombren
                            datan[nombren] = bloquen
                        else:
                            datan[blq] = data[blq]
                    # mydict[new_key] = mydict.pop(old_key)
                    print datan
                    data = datan
                    cursor_mysql.execute("select * from songs where song_id = %i" % fuera['id_anuncio'])
                    adb = cursor_mysql.fetchall()[0]  # OJO A ESE INDICE 0
                    inicio = fuera["fecha_ocurrencia"]
                    final = inicio + datetime.timedelta(seconds=fuera['duracion_anuncio'])
                    try:
                        anuncio = Anuncio(fuera['ID'], adb['NOMBRE'], adb["CAMARC"], bloquedelanuncio,
                                          inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                    except:
                        anuncio = Anuncio(fuera['id_anuncio'], adb["song_name"], adb["nombre_marca"], bloquedelanuncio,
                                          inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                    bloque = data.get(anuncio.bloque)
                    print ' de antes'
                    print adb['song_name']
                    print anuncio.bloque
                    if bloque is None:
                        bloque = Bloque(anuncio.bloque)
                        data[anuncio.bloque] = bloque
                    bloque.anuncios.append(anuncio)
                else:

                    bloques[bnum] = (bloques[bnum][0], (iniciof - datetime.timedelta(seconds=80), bloques[bnum][1][1]))
                    cursor_mysql.execute("select * from songs where song_id = %i" % fuera['id_anuncio'])
                    adb = cursor_mysql.fetchall()[0]  # OJO A ESE INDICE 0
                    inicio = fuera["fecha_ocurrencia"]
                    final = inicio + datetime.timedelta(seconds=fuera['duracion_anuncio'])
                    try:
                        anuncio = Anuncio(fuera['ID'], adb['NOMBRE'], adb["CAMARC"], bloquedelanuncio,
                                          inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                    except:
                        anuncio = Anuncio(fuera['id_anuncio'], adb["song_name"], adb["nombre_marca"], bloquedelanuncio,
                                          inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                    bloque = data.get(anuncio.bloque)
                    # print adb['song_name']
                    # print anuncio.bloque
                    if bloque is None:
                        bloque = Bloque(anuncio.bloque)
                        data[anuncio.bloque] = bloque
                    bloque.anuncios.append(anuncio)
                    print 'en el else'
                    print bloques[bnum]
                    print bloques[bnum][1][1]

            elif finalf > bloques[bnum][1][1]:
                if iniciof > bloques[bnum][1][1] and (finalf - bloques[bnum][1][1]).seconds > 120:
                    print 'otro bloque posterior'
                    print iniciof
                    print finalf
                    print bloques[bnum][1][0]
                    print bloques[bnum][1][1]
                    bloques.insert(bnum + 1, (
                    u'bloquex', (iniciof - datetime.timedelta(seconds=50), finalf + datetime.timedelta(seconds=50))))
                    bloqueantes = comienzograbacion
                    for num, blq in enumerate(bloques):

                        bloquei = blq[1][0]
                        bloquef = blq[1][1]
                        if bloquei < comienzograbacion:
                            bloquei = comienzograbacion
                        elif bloquei < bloqueantes:
                            print 'BLOQUES SUPERPUESTOS!!'
                            bloquei = bloqueantes + datetime.timedelta(seconds=10)
                        if bloquef > comienzograbacion + datetime.timedelta(seconds=3600):
                            bloquef = comienzograbacion + datetime.timedelta(seconds=3590)
                        bloques[num] = (nombrecomun + unicode(num + 1), (bloquei, bloquef))
                        bloqueantes = bloquef

                    print 'ya ta posterior', bnum
                    print bloques
                    print data
                    # cambiar data y objeto bloque
                    datan = dict()
                    datan[nombrecomun + unicode(bnum + 2)] = Bloque(nombrecomun + unicode(bnum + 2))
                    for blq in data:
                        if int(blq[-1]) > bnum + 1:
                            print 'dentro'
                            bloquen = data[blq]
                            nombren = blq[:-1] + unicode(int(blq[-1]) + 1)
                            for anun in bloquen.anuncios:
                                anun.bloque = nombren
                            bloquen.nombre = nombren
                            datan[nombren] = bloquen

                        else:
                            datan[blq] = data[blq]
                    print 'despues del copy'
                    print datan
                    data = datan
                    # bloques[nbnum]=(bloques[nbnum][0],(iniciof-datetime.timedelta(seconds=30),bloques[nbnum][1][1]))
                    cursor_mysql.execute("select * from songs where song_id = %i" % fuera['id_anuncio'])
                    adb = cursor_mysql.fetchall()[0]  # OJO A ESE INDICE 0
                    inicio = fuera["fecha_ocurrencia"]
                    final = inicio + datetime.timedelta(seconds=fuera['duracion_anuncio'])
                    try:
                        anuncio = Anuncio(fuera['ID'], adb['NOMBRE'], adb["CAMARC"], bloquedelanuncio,
                                          inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                    except:
                        anuncio = Anuncio(fuera['id_anuncio'], adb["song_name"], adb["nombre_marca"], bloquedelanuncio,
                                          inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                    bloque = data.get(anuncio.bloque)
                    print ' de despues'
                    print adb['song_name']
                    print anuncio.bloque
                    if bloque is None:
                        bloque = Bloque(anuncio.bloque)
                        data[anuncio.bloque] = bloque
                    bloque.anuncios.append(anuncio)

                else:
                    bloques[bnum] = (bloques[bnum][0], (bloques[bnum][1][0], finalf + datetime.timedelta(seconds=80)))
                    cursor_mysql.execute("select * from songs where song_id = %i" % fuera['id_anuncio'])
                    adb = cursor_mysql.fetchall()[0]  # OJO A ESE INDICE 0
                    inicio = fuera["fecha_ocurrencia"]
                    final = inicio + datetime.timedelta(seconds=fuera['duracion_anuncio'])
                    try:
                        anuncio = Anuncio(fuera['ID'], adb['NOMBRE'], adb["CAMARC"], bloquedelanuncio,
                                          inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                    except:
                        anuncio = Anuncio(fuera['id_anuncio'], adb["song_name"], adb["nombre_marca"], bloquedelanuncio,
                                          inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                    bloque = data.get(anuncio.bloque)
                    # print adb['song_name']
                    # print bloque.nombre
                    if bloque is None:
                        bloque = Bloque(anuncio.bloque)
                        data[anuncio.bloque] = bloque
                    bloque.anuncios.append(anuncio)
            else:
                print 'EH encaja en bloques ya modificados'
                cursor_mysql.execute("select * from songs where song_id = %i" % fuera['id_anuncio'])
                adb = cursor_mysql.fetchall()[0]  # OJO A ESE INDICE 0
                inicio = fuera["fecha_ocurrencia"]
                final = inicio + datetime.timedelta(seconds=fuera['duracion_anuncio'])
                try:
                    anuncio = Anuncio(fuera['ID'], adb['NOMBRE'], adb["CAMARC"], bloquedelanuncio,
                                      inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                except:
                    anuncio = Anuncio(fuera['id_anuncio'], adb["song_name"], adb["nombre_marca"], bloquedelanuncio,
                                      inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
                bloque = data.get(anuncio.bloque)
                # print adb['song_name']
                # print bloque.nombre
                if bloque is None:
                    bloque = Bloque(anuncio.bloque)
                    data[anuncio.bloque] = bloque
                bloque.anuncios.append(anuncio)

        elif bloquefuera_inicio % 2 != 0:
            # el final se acerca a otro bloque o al reves, unimos bloques
            # union de bloques complicada
            print 'union de bloques'
            bnuminicio = bloquefuera_inicio / 2
            bnumfinal = bloquefuera_final / 2

            bloques[bnuminicio] = (bloques[bnuminicio][0], (bloques[bnuminicio][1][0], bloques[bnumfinal][1][1]))
            cursor_mysql.execute("select * from songs where song_id = %i" % fuera['id_anuncio'])
            adb = cursor_mysql.fetchall()[0]  # OJO A ESE INDICE 0
            inicio = fuera["fecha_ocurrencia"]
            final = inicio + datetime.timedelta(seconds=fuera['duracion_anuncio'])
            try:
                anuncio = Anuncio(fuera['ID'], adb['NOMBRE'], adb["CAMARC"], bloquedelanuncio,
                                  inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
            except:
                anuncio = Anuncio(fuera['id_anuncio'], adb["song_name"], adb["nombre_marca"], bloquedelanuncio,
                                  inicio.strftime("%d/%m/%Y %H:%M:%S"), final.strftime("%d/%m/%Y %H:%M:%S"))
            print adb['song_name']
            print bloques[bnuminicio][0]
            print iniciof
            bloque = data.get(anuncio.bloque)
            if bloque is None:
                bloque = Bloque(anuncio.bloque)
                data[anuncio.bloque] = bloque
            bloque.anuncios.append(anuncio)

            # hay que cambiar los nombres de bloques
            # y pasar los anuncios al nuevo bloque suma
            # YA NO ESTA EL BLOQUE BNUMFINAL +1
            # QUE ES EL bloques[0][0][:-1]++unicode(bnumfinal)
            bloquenomaquitar = bloques[0][0][:-1] + unicode(bnumfinal + 1)
            bloqueaunir = bloques[0][0][:-1] + unicode(bnumfinal)
            bloques.pop(bnumfinal)

            print 'bloque ya quitado de lista de bloques', bloquenomaquitar
            bloqueaquitar = data.get(bloquenomaquitar)
            for anun in bloqueaquitar.anuncios:  # lista con los anuncios a trasladar

                anun.bloque = bloqueaunir
                bloque.anuncios.append(anun)

            #
            # quitamos nombre de bloque eliminado
            for indi, bli in enumerate(bloques):
                if bli[0].split('bloque')[1] != unicode(indi + 1):
                    print 'cambio de bloques'
                    bloques[indi] = (
                    bloques[indi][0][:-1] + unicode(indi + 1), (bloques[indi][1][0], bloques[indi][1][1]))

            data.pop(bloquenomaquitar)
            # CORRER NOMBRES DE BLOQUE

            for blqs in data.values():
                if int(blqs.nombre[-1]) > bnumfinal + 1:
                    print 'in'
                    nomnuevo = blqs.nombre[:-1] + unicode(int(blqs.nombre[-1]) - 1)
                    data[nomnuevo] = data.pop(blqs.nombre)
                    blqs.nombre = nomnuevo
                    # estamos ante un tipo bloque con el nombre mal
                    for an in blqs.anuncios:
                        an.bloque = nomnuevo

    # recorremos los bloques para aquellos que no tienen anuncios

    for blq in bloques:
        if data.get(blq[0]) is None:
            bloque = Bloque(blq[0])
            data[blq[0]] = bloque

    data = data.values()
    print 'final de recuperadatos'
    for bloque in data:
        print [x.inicio for x in bloque.anuncios]

    if cambiabloque:
        return data, bloques
    else:
        return data, None


def pydate2wxdate(date):
    assert isinstance(date, (datetime.datetime, datetime.date))
    tt = date.timetuple()
    dmy = (tt[2], tt[1] - 1, tt[0])
    wxt = wx.DateTimeFromDMY(*dmy)
    wxt.SetHour(date.hour)
    wxt.SetMinute(date.minute)
    wxt.SetSecond(date.second)
    return wxt


def wxdate2pydate(date):
    assert isinstance(date, wx.DateTime)
    if date.IsValid():
        ymd = map(int, date.FormatISODate().split('-'))
        return datetime.date(*ymd)
    else:
        return None


def simuladatos():
    a = {'anuncio1': {'anuncio': 'pepsi max',
                      'marca': 'pepsi',
                      'inicio': '2015-03-26T14:36:36',
                      'final': '2015-03-26T14:36:56',
                      'id': 234},
         'anuncio2': {'anuncio': 'renault',
                      'marca': 'clio',
                      'inicio': '2015-03-26T14:36:58',
                      'final': '2015-03-26T14:37:16',
                      'id': 232}}

    bloques = [(u'20150326143001_bloque1',
                (datetime.datetime(2015, 3, 26, 14, 36, 16), datetime.datetime(2015, 3, 26, 14, 37, 56))), (
               u'20150326143001_bloque2',
               (datetime.datetime(2015, 3, 26, 14, 52, 6), datetime.datetime(2015, 3, 26, 14, 54, 36)))]

    data = dict()
    for i in a.values():
        print 'nuevo'
        print i
        inicio = dateutil.parser.parse(i['inicio'])
        final = dateutil.parser.parse(i['final'])

        for b in bloques:
            if inicio > b[1][0]:

                if final < b[1][1]:
                    anuncio = Anuncio(i['id'], i['anuncio'], i['marca'], b[0], i['inicio'], i['final'])

                    bloque = data.get(anuncio.bloque)
                    if bloque is None:
                        bloque = Bloque(anuncio.bloque)
                        data[anuncio.bloque] = bloque
                    bloque.anuncios.append(anuncio)

                else:

                    print 'limite exterior fuera de bloque'
                    # todo CONTROLAR AMPLIACION DE BLOQUES

    data = data.values()

    return data


if __name__ == '__main__':
    simuladatos()
