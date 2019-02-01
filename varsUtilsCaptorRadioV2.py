# coding=utf-8
# __author__ = 'Mario Romera Fernández'
# __license__ = 'GNU General Public License v2.0'


################################################################################
############################## CONEXIONES A BBDD ###############################
# Conexión a la BBDD MySql de InfoAdex
def cargar_conexion_mysql_infoadex():
    """
    Creates a MySql connection object pointing InfoAdex MySql DB
    :return: MySql connection object
    """
    from MySQLdb import connect
    return connect(host="192.168.2.170",
                   user="root",
                   passwd="infoadex",
                   db="captor",
                   use_unicode=True,
                   charset="utf8",
                   init_command='SET NAMES UTF8')


# Conexión a la BBDD MySql local (Mario)
def cargar_conexion_mysql_local():
    """
    Creates a MySql connection object pointing local MySql DB
    :return: MySql connection object
    """
    from MySQLdb import connect
    return connect(host="127.0.0.1",
                   user="root",
                   passwd="12345",
                   db="captor",
                   use_unicode=True,
                   charset="utf8",
                   init_command='SET NAMES UTF8')


# Conexion a la BBDD AS400 de InfoAdex
def cargar_conexion_as400_infoadex():
    """
    Creates a pyobdc connection object pointing InfoAdex AS400 DB
    :return: pyodbc connection object
    """
    from pyodbc import connect
    return connect('DSN=AS400;SYSTEM=192.168.1.101;UID=INFOADEX;PWD=INFOADEX')


# Conexion a la BBDD SQL en local copia del AS400 de InfoAdex
def cargar_conexion_sql_local():
    """
    Creates a pyobdc connection object pointing local Sql DB
    :return: pyodbc connection object
    """
    from pyodbc import connect
    return connect('DRIVER={SQL Server};SERVER=LENOVO-PC\SQLEXPRESS;DATABASE=InfoAdex;Trusted_Connection=yes')


############################ END CONEXIONES A BBDD #############################
################################################################################

################################################################################
################################ OBJETO DEJAVU #################################
# Objeto Dejavu a la BBDD MySql InfoAdex
def cargar_djv_infoadex():
    """
    Creates a Dejavu object pointing InfoAdex MySql DB
    :return: Dejavu object
    """
    from dejavuCAPTOR import Dejavu
    _configMySqlInfoAdex = {
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
    return Dejavu(_configMySqlInfoAdex)


# Objeto Dejavu a la BBDD MySql local (Mario)
def cargar_djv_local():
    """
    Creates a Dejavu object pointing local MySql DB
    :return: Dejavu object
    """
    from dejavuCAPTOR import Dejavu
    _configLocal = {
        "database": {
            "host": "127.0.0.1",
            "user": "root",
            "passwd": "12345",
            "db": "captor",
            "use_unicode": True,
            "charset": 'utf8',
            "init_command": 'SET NAMES UTF8'
        },
        "database_type": "mysql"
    }
    return Dejavu(_configLocal)


############################## END OBJETO DEJAVU ###############################
################################################################################

################################################################################
######################### CONFIGURACIÓN CAPTORRADIO V2 #########################
FRECUENCIA_MUESTREO = 44100
VENTANA = 0.020
SOLAPE = 50
NUM_PARAMETROS = 20
PARAMETROS = ['lst_energy', 'hzcrr', 'centroid', 'spread', 'variance', 'rolloff', 'mean', 'crest']
TIPO_PARAMETROS = [0, 0, 1, 1, 1, 1, 1, 1]
MFCC = 12
DELTAS = False
CHROMA = 0
FLUX = 0


####################### END CONFIGURACIÓN CAPTORRADIO V2 #######################
################################################################################


################################################################################
############################### OPERACIONES BBDD ###############################
# Carga el programa en el que sucede el anuncio
def cargar_programa_anuncio(inicio_anuncio, onda, cadena, emisora, cursor):
    """
    Retrieves the code ID of the program in which the ad occurs
    :param inicio_anuncio: begginig of the ad (datetime)
    :param emisora: radio station's name
    :param cursor: cursor to DB
    :return: code ID
    """
    from datetime import time
    dias_semana = {0: "D",
                   1: "L",
                   2: "M",
                   3: "X",
                   4: "J",
                   5: "V",
                   6: "S",
                   7: "D"}

    query = (u"SELECT codigo "
             u"FROM captor.programas "
             u"WHERE dia_semana = '{}' "
             u"AND onda = '{}' "
             u"AND cadena = '{}' "
             u"AND emisora = '{}' "
             u"AND hora_emision < '{}' "
             u"ORDER BY hora_emision DESC LIMIT 1;").format(dias_semana[inicio_anuncio.isoweekday()],
                                                            onda, cadena, emisora, inicio_anuncio.time())

    cursor.execute(query)
    codigoPrograma = cursor.fetchone()

    if codigoPrograma is None:
        query = (u"SELECT codigo "
                 u"FROM captor.programas "
                 u"WHERE dia_semana = '{}' "
                 u"AND onda = '{}' "
                 u"AND cadena = '{}' "
                 u"AND emisora = '{}' "
                 u"AND hora_emision < '{}' "
                 u"ORDER BY hora_emision DESC LIMIT 1;").format(dias_semana[inicio_anuncio.isoweekday() - 1],
                                                                onda, cadena, emisora,
                                                                time(hour=23, minute=59, second=59))
        cursor.execute(query)
        codigoPrograma = cursor.fetchone()

    return codigoPrograma["codigo"]


def extraer_datos_emisora(nombre, cursor):
    query = (u"SELECT onda, cadena, emisora "
             u"FROM emisoras "
             u"WHERE descripcion = '{}'").format(nombre)
    cursor.execute(query)
    return cursor.fetchone()

############################# END OPERACIONES BBDD #############################
################################################################################
