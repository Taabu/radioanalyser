# coding=utf-8
# __author__ = 'Mario Romera Fernández'

import wx
from odbc_as400 import cursor


class DynamicListComboBox4Caract(wx.ComboBox):
    """
    ComboBox con lista dinamica.
    Se crea: DynamicListComboBox(self, "Texto", tabla, campotabla, choices)
        "Texto" = texto por defecto
        tabla = tabla del AS400
        campotabla = campo de la tabla para hacer la búsqueda
        choices = lista con las opciones
        self.currentText almacena el valor seleccionado
    """

    def __init__(self, parent, value, tabla, campotabla, choices=[], **par):
        wx.ComboBox.__init__(self, parent, wx.ID_ANY, value, size=(300, 25),
                             style=wx.CB_SORT | wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER,
                             choices=choices, **par)
        self.campotabla = campotabla
        self.tabla = tabla
        self.choices = choices
        self.choices.sort()
        self.choices = [x.upper() for x in self.choices]
        self.Bind(wx.EVT_TEXT, self.EvtText)
        self.Bind(wx.EVT_CHAR, self.EvtChar)
        self.Bind(wx.EVT_COMBOBOX, self.EvtCombobox)
        self.currentText = ''
        self.ignoreText = False

    def EvtCombobox(self, event):
        self.currentText = self.GetStringSelection()
        self.ChangeValue(self.currentText)
        self.ignoreText = True

    def actualizar(self, event):
        if len(self.choices) > 0:
            self.Clear()
            self.AppendItems(self.choices)
            self.Popup()
        self.ChangeValue(self.currentText.upper())
        self.SetInsertionPoint(len(self.currentText))

    def EvtChar(self, event):
        if event.GetKeyCode() == 8 and len(self.currentText) > 4:
            self.currentText = self.currentText[:-1]
            self.ChangeValue(self.currentText)
            self.choices = []
            busqueda = u"'%{}%'".format(self.currentText)
            print busqueda
            cursor.execute(
                "SELECT DISTINCT %s FROM %s WHERE %s LIKE %s" % (
                self.campotabla, self.tabla, self.campotabla, busqueda))
            resultados = cursor.fetchall()
            for resultado in resultados:
                # print resultado[0]
                self.choices.append(resultado[0])
            # si hemos borrado tod0 el texto, reiniciamos la lista de opciones
            if self.IsTextEmpty():
                self.Clear()
                self.AppendItems(self.choices)
            else:
                self.actualizar(event)
        else:
            event.Skip()

    def EvtText(self, event):

        if self.ignoreText:
            self.ignoreText = False
            event.Skip()
        else:
            self.currentText = event.GetString().upper()
            if len(self.currentText) == 4:
                self.Clear()
                self.choices = []
                busqueda = u"'%{}%'".format(self.currentText)
                print busqueda
                cursor.execute(
                    "SELECT DISTINCT %s FROM %s WHERE %s LIKE %s" % (
                    self.campotabla, self.tabla, self.campotabla, busqueda))
                resultados = cursor.fetchall()
                for resultado in resultados:
                    self.choices.append(resultado[0])
            elif len(self.currentText) == 0:
                self.choices = []
                self.Clear()
            self.actualizar(event)


if __name__ == '__main__':
    class TrialPanel(wx.Panel):
        def __init__(self, parent):
            wx.Panel.__init__(self, parent, wx.ID_ANY)

            choices = []
            cb = DynamicListComboBox4Caract(self, "", 'CDMPMR00', 'CAMARC', choices)


    app = wx.App()
    frame = wx.Frame(None, -1, 'Demo MyComboBox Control', size=(400, 400))
    TrialPanel(frame)
    frame.Show()
    app.MainLoop()
