# coding=utf-8
# __author__ = 'Mario Romera Fernández'


def carga_programas_as400_mysql():
    """
    Carga la tabla de programas INFOCDM.cdmppo00n del AS400 a la tabla `captor`.`programas` de MySql
    """
    from datetime import date, time
    from MySQLdb.cursors import DictCursor
    from varsUtilsCaptorRadioV2 import cargar_conexion_as400_infoadex, cargar_conexion_mysql_infoadex

    cnx_as400 = cargar_conexion_as400_infoadex()
    cnx_mysql = cargar_conexion_mysql_infoadex()

    cursor_as400 = cnx_as400.cursor()
    cursor_mysql = cnx_mysql.cursor(DictCursor)

    cont = 0

    # Leemos la tabla de programas del AS400
    lista = []
    try:
        queryAS400 = u"SELECT * FROM INFOCDM.cdmppo00n"
        cursor_as400.execute(queryAS400)
    except:
        queryAS400 = u"SELECT * FROM cdmppo00n"
        cursor_as400.execute(queryAS400)

    columnas = [columna[0] for columna in cursor_as400.description]
    for resultado in cursor_as400.fetchall():
        lista.append(dict(zip(columnas, resultado)))

    # Borramos la tabla de programas de MySql
    try:
        queryMySql = u"DROP TABLE `captor`.`programas`"
        cursor_mysql.execute(queryMySql)
        cnx_mysql.commit()
    except:
        print u"No se ha podido borrar la tabla captor.programas"

    # Creamos la tabla de programas nueva en MySql
    queryMySql = (u"CREATE TABLE `captor`.`programas` ("
                  u"`hora_emision` TIME, "
                  u"`dia_semana` CHAR, "
                  u"`fecha_inserccion` DATE, "
                  u"`fecha_alta` DATE, "
                  u"`onda` VARCHAR(10), "
                  u"`cadena` VARCHAR(10), "
                  u"`emisora` VARCHAR(10), "
                  u"`nombre` VARCHAR(250), "
                  u"`codigo` VARCHAR(10), "
                  u"KEY (`hora_emision`) "
                  u") ENGINE = InnoDB DEFAULT CHARSET=utf8;")

    cursor_mysql.execute(queryMySql)
    cnx_mysql.commit()

    # Leemos los datos cargados del AS400 y los insertamos en MySql
    for i in lista:
        try:
            hora_emision = time(hour=int(i["PGHORA"]), minute=int(i["PGMINT"]))
            dia_semana = i["DIASEM"].rstrip().decode("latin-1")
            aIn, mIn, dIn = int(i["PGAAIN"]), int(i["PGMMIN"]), int(i["PGDDIN"])
            if aIn == 0:
                aIn = 1
            if mIn == 0:
                mIn = 1
            if dIn == 0:
                dIn = 1
            fecha_inserccion = date(year=aIn, month=mIn, day=dIn)
            aAl, mAl, dAl = int(i["PGAAAL"]), int(i["PGMMAL"]), int(i["PGDDAL"])
            if aAl == 0:
                aAl = 1
            if mAl == 0:
                mAl = 1
            if dAl == 0:
                dAl = 1
            fecha_alta = date(year=aAl, month=mAl, day=dAl)
            onda = i["RAONDA"].rstrip().decode("latin-1")
            cadena = i["RACADN"].rstrip().decode("latin-1")
            emisora = i["RAEMIS"].rstrip().decode("latin-1")
            nombre = i["PGNOMB"].rstrip().decode("latin-1")
            codigo = i["PGCODI"].rstrip().decode("latin-1")
            insertVariables = u"'{}','{}','{}','{}','{}','{}','{}','{}','{}'".format(hora_emision, dia_semana,
                                                                                     fecha_inserccion, fecha_alta, onda,
                                                                                     cadena, emisora, nombre, codigo)
            queryMySql = (u"INSERT INTO `captor`.`programas` ("
                          u"`hora_emision`,"
                          u"`dia_semana`,"
                          u"`fecha_inserccion`,"
                          u"`fecha_alta`,"
                          u"`onda`,"
                          u"`cadena`,"
                          u"`emisora`,"
                          u"`nombre`,"
                          u"`codigo`) "
                          u"VALUES ({})").format(
                insertVariables)
            cursor_mysql.execute(queryMySql)
            cnx_mysql.commit()
            cont += 1

        except Exception, e:
            print u"No se ha podido añadir la linea {}".format(i)
            print Exception
            print e
            pass

    print u"Añadidos {} programas".format(cont)


def carga_emisoras_as400_mysql():
    """
    Carga la tabla de emisoras INFOCDM.INFOSOPORT del AS400 a la tabla `captor`.`emisoras` de MySql
    """
    from MySQLdb.cursors import DictCursor
    from varsUtilsCaptorRadioV2 import cargar_conexion_as400_infoadex, cargar_conexion_mysql_infoadex

    cnx_as400 = cargar_conexion_as400_infoadex()
    cnx_mysql = cargar_conexion_mysql_infoadex()

    cursor_as400 = cnx_as400.cursor()
    cursor_mysql = cnx_mysql.cursor(DictCursor)

    cont = 0

    # Leemos la tabla de emisoras del AS400
    lista = []
    try:
        queryAS400 = u"SELECT * FROM INFOXXI.INFSOPORT WHERE IDMEDIOS = 'RD'"
        cursor_as400.execute(queryAS400)
    except:
        queryAS400 = u"SELECT * FROM INFSOPORT WHERE IDMEDIOS = 'RD'"
        cursor_as400.execute(queryAS400)

    columnas = [columna[0] for columna in cursor_as400.description]
    for resultado in cursor_as400.fetchall():
        lista.append(dict(zip(columnas, resultado)))

    # Borramos la tabla de emisoras de MySql
    try:
        queryMySql = u"DROP TABLE `captor`.`emisoras`"
        cursor_mysql.execute(queryMySql)
        cnx_mysql.commit()
    except:
        print u"No se ha podido borrar la tabla captor.emisoras"

    # Creamos la tabla de programas nueva en MySql
    queryMySql = (u"CREATE TABLE `captor`.`emisoras` ("
                  u"`onda` VARCHAR(10), "
                  u"`cadena` VARCHAR(10), "
                  u"`emisora` VARCHAR(10), "
                  u"`id_provincia` INT, "
                  u"`id_comunidad` INT, "
                  u"`clase_soporte` VARCHAR(10), "
                  u"`id_medios` VARCHAR(10), "
                  u"`id_grupo_comunicacion` INT, "
                  u"`id_exclusivo` INT, "
                  u"`descripcion` VARCHAR(250), "
                  u"KEY (`id_exclusivo`) "
                  u") ENGINE = InnoDB DEFAULT CHARSET=utf8;")

    cursor_mysql.execute(queryMySql)
    cnx_mysql.commit()

    # Leemos los datos cargados del AS400 y los insertamos en MySql
    for i in lista:
        try:
            onda = i["IDSOPOR1"].rstrip().decode("latin-1")
            cadena = i["IDSOPOR2"].rstrip().decode("latin-1")
            emisora = i["IDSOPOR3"].rstrip().decode("latin-1")
            id_provincia = int(i["IDPROVIN"])
            id_comunidad = int(i["IDCOMUNI"])
            clase_soporte = i["IDCLSOPO"].rstrip().decode("latin-1")
            id_medios = i["IDMEDIOS"].rstrip().decode("latin-1")
            id_grupo_comunicacion = int(i["IDGRCOMU"])
            id_exclusivo = int(i["IDEXCLUS"])
            descripcion = i["CDESCRIPCI"].rstrip().decode("latin-1")

            insertVariables = u"'{}','{}','{}','{}','{}','{}','{}','{}','{}','{}'".format(onda, cadena,
                                                                                          emisora, id_provincia,
                                                                                          id_comunidad,
                                                                                          clase_soporte, id_medios,
                                                                                          id_grupo_comunicacion,
                                                                                          id_exclusivo, descripcion)
            queryMySql = (u"INSERT INTO `captor`.`emisoras` ("
                          u"`onda`,"
                          u"`cadena`,"
                          u"`emisora`,"
                          u"`id_provincia`,"
                          u"`id_comunidad`,"
                          u"`clase_soporte`,"
                          u"`id_medios`,"
                          u"`id_grupo_comunicacion`,"
                          u"`id_exclusivo`,"
                          u"`descripcion`) "
                          u"VALUES ({})").format(
                insertVariables)
            cursor_mysql.execute(queryMySql)
            cnx_mysql.commit()
            cont += 1

        except Exception, e:
            print u"No se ha podido añadir la linea {}".format(i)
            print Exception
            print e
            pass

    print u"Añadidas {} emisoras".format(cont)


if __name__ == '__main__':
    carga_programas_as400_mysql()
    carga_emisoras_as400_mysql()
