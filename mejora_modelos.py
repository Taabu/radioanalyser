# coding=utf-8
# __author__ = 'Mario Romera Fernández'

import os
import datetime
import MySQLdb
from Entrenador import entrenador

db = MySQLdb.connect(host="localhost",
                     user="root",
                     passwd="12345",
                     db="pruebas",
                     charset='utf8')
cur = db.cursor()

emisora = 1

# Seleccionar los numpys y targets del ultimo mes
ruta_origen = 'C:/Users/Mario/Desktop/InfoAdex09062015/entrenamiento'
ruta_destino = 'C:/Users/Mario/Desktop/InfoAdex09062015/modelos/'
fecha = datetime.datetime.now()
print ruta_destino, emisora, fecha.date()
ruta_destino_final = os.path.join(ruta_destino, str(emisora), str(fecha.date()))

try:
    os.makedirs(ruta_destino_final)
except OSError:
    pass

# extractor(ruta_origen, ruta_origen)

# Entrenar el modelo con esos archivos
parametros = []
parametros.append("bootstrap=False")
parametros.append("compute_importances=None")
parametros.append("criterion=entropy")
parametros.append("max_depth=None")
parametros.append("max_features=None")
parametros.append("max_leaf_nodes=None")
parametros.append("min_density=None")
parametros.append("min_samples_leaf=1")
parametros.append("min_samples_split=3")
parametros.append("n_estimators=100")
parametros.append("n_jobs=-1")

modelo = 'sklearn.ensemble.ExtraTreesClassifier'

nombre_modelo = entrenador(ruta_origen, ruta_destino_final + "/", parametros, modelo, [])

cur.execute("INSERT INTO modelos (nombre_modelo, fecha_modelo, cadena_modelo) VALUES (%s, %s, %s)", (nombre_modelo,
                                                                                                     fecha, emisora))
db.commit()

print nombre_modelo
