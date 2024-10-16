import zipfile
import os
import argparse
from ftplib import FTP
import datetime
from datetime import timedelta
import re
import requests


parser = argparse.ArgumentParser(description="Busca grabaciones en el servidor y extrae los archivos")



parser.add_argument('isla', type=str, help='Isla', choices=[{{data1}}])
parser.add_argument('cadena_busqueda', type=str, help='cadena de busqueda: idllamada o telefono, entre 6 y 13 caracteres ')
parser.add_argument('fecha1', type=str, nargs='?', default=None, help='Fecha, formato yyyymmdd o yyyymm o yyyy')
parser.add_argument('fecha2', type=str, nargs='?', default=None, help='Fecha, formato yyyymmdd o yyyymm o yyyy')
parser.add_argument('GID', type=str, nargs='?', default=None, help='Global ID')



args = parser.parse_args()

if len(args.cadena_busqueda)<6 or len(args.cadena_busqueda)>13:
    raise ValueError("La cadena de bsuqueda debe tener entre 6 y 13 caracteres")

path_carpeta = r"{{data2}}"+args.isla+"/Actual"
path_carpeta_alt = r"{{data3}}"+args.isla+"/Historico"
carpeta_extraccion = r"{{data4}}Buscar-Grabaciones"
archivos_extraidos = []

def archivos_zip(path):
    try:
        with zipfile.ZipFile(path, 'r') as zip_a_buscar:
            nombres_archivos = zip_a_buscar.namelist()
            return nombres_archivos
    except Exception as e:
        print("Error busqueda de zips: {}".format(e))
        return []


def buscar_grabacion(expresion, archivo):
    archivos_ok = []
    try:
        for nombre_archivo in archivos_zip(archivo):
            if expresion in nombre_archivo and nombre_archivo.endswith(".mp3"):
                archivos_ok.append(nombre_archivo)
    except Exception as e:
        print("Error busqueda de grabacion: {}".format(e))
        archivos_ok = "Error"
    return archivos_ok

def generar_fechas_intermedias(fecha_inicio, fecha_fin):
    #Recibe fecha en formato yyyymmdd
    fecha_inicio = datetime.date(int(fecha_inicio[0:4]), int(fecha_inicio[4:6]), int(fecha_inicio[6:8]))
    fecha_fin = datetime.date(int(fecha_fin[0:4]), int(fecha_fin[4:6]), int(fecha_fin[6:8]))
    
    fechas = []
    

    while fecha_inicio <= fecha_fin:

        fechas.append(fecha_inicio.strftime('%Y_%m_%d'))

        fecha_inicio += timedelta(days=1)
    
    return fechas

def buscar_grabacion_en_carpeta(fecha_desde,fecha_hasta, cadena_busqueda, carpeta):
    #tambien se puede pasar telefono en lugar de idllamada
    #fecha = yyyymmdd
##    if (len(fecha)==8):
##        fecha_nombre = '_'+fecha[0:4]+'_'+fecha[4:6]+'_'+fecha[6:8]
##    if (len(fecha)==6):
##        fecha_nombre = '_'+fecha[0:4]+'_'+fecha[4:6]+'_'
##    if (len(fecha)==4):
##        fecha_nombre = '_'+fecha[0:4]+'_'
##    else:
##        expresion = '_'
    rango_fechas =  generar_fechas_intermedias(fecha_desde, fecha_hasta)
    resultados = {}
    try:
        for root, dirs, files in os.walk(carpeta):
            for file in files:
                if file.endswith(".zip") and file[9:19] in rango_fechas:
                    archivo_zip = os.path.join(root, file)
                    archivos_encontrados = buscar_grabacion(cadena_busqueda, archivo_zip)
                    if archivos_encontrados:
                        resultados[archivo_zip] = archivos_encontrados
                        
    except Exception as e:
        print("Error busqueda en carpeta: {}".format(e))
    return resultados

def extraer_archivos(resultados, destino):
    global archivos_extraidos
    try:
        for archivo_zip, archivos in resultados.items():
            with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
                for archivo in archivos:
                    zip_ref.extract(archivo, destino)
                    archivos_extraidos.append(os.path.join(destino, archivo))
    except Exception as e:
        print("Error extraccion: {}".format(e))

def subir_archivos_ftp(archivos, carpeta_destino, servidor, usuario, pass_ftp):
    try:
        with FTP(servidor) as ftp:
            ftp.login(user=usuario, passwd=pass_ftp)
            for archivo in archivos:
                with open(archivo, 'rb') as f:
                    nombre_archivo = os.path.basename(archivo)
                    ruta_archivo_remoto = os.path.join(carpeta_destino, nombre_archivo)
                    #ruta_archivo_remoto = ruta_archivo_remoto.replace("/", "\\")
                    print(ruta_archivo_remoto)
                    ftp.storbinary('STOR {}'.format(ruta_archivo_remoto), f)
                    print('Subido: {} a {}'.format(archivo, ruta_archivo_remoto))
                    ftpReply = ftp.close();
                    print(ftpReply);

    except Exception as e:
        print("Error al subir archivos por FTP: {}".format(e))

fecha1_arg = args.fecha1 or ''
fecha2_arg = args.fecha2 or ''
resultado = buscar_grabacion_en_carpeta(fecha1_arg, fecha2_arg, args.cadena_busqueda, path_carpeta)
if not resultado:
    resultado = buscar_grabacion_en_carpeta(fecha1_arg, fecha2_arg, args.cadena_busqueda, path_carpeta_alt)

#extraer_archivos(resultado, carpeta_extraccion)
print (resultado)
print (len(resultado))

servidor_ftp = '{{data5}}'
usuario_ftp = '{{data6}}'
pass_ftp = '{{data7}}'
carpeta_remota = '/UPLOAD/'
archivo_salida = args.cadena_busqueda+'_'+fecha1_arg+'_'+fecha2_arg+'.txt'
archivo_salida_path = os.path.join('{{data8}}/Buscar-Grabaciones',archivo_salida)
telefono = ''

if (len(resultado)!=0):
    with open(archivo_salida_path, 'w') as f:
        for archivo_zip, archivos in resultado.items():
            for archivo in archivos:
                match_idllamada = re.search(r'-(\d+)-', archivo)
                match_tel = re.search(r'^(\d+)-', archivo)
                idllamada = match_idllamada.group(1) if match_idllamada else 'N/A'
                telefono  = match_tel.group(1) if match_tel else 'N/A'
                f.write('{},{},{},{},{}##&&##'.format(telefono,idllamada,archivo,archivo_zip, args.GID))
    f.close()
else:
    with open(archivo_salida_path, 'w') as f:
        f.write('')
    f.close()

archivo_salida_arr = [] 
archivo_salida_arr.append(archivo_salida_path)

subir_archivos_ftp(archivo_salida_arr, carpeta_remota, servidor_ftp, usuario_ftp, pass_ftp)

param1 = args.fecha1
param2 = args.fecha2
param3 = telefono if telefono else args.cadena_busqueda
param4 = str(len(resultado))
param5 = archivo_salida
param6 = args.GID 

url = '{{data9}}?idTask=287&param1={}&param2={}&param3={}&param4={}&param5={}&param6={}'.format(param1, param2, param3, param4, param5, param6)
response = requests.get(url)
print(url)
print(response.status_code, ' - ', response.text)


