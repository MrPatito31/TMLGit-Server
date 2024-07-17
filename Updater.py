import http.client
import json
import os
import sys
import zipfile

def get_latest_release(repo_owner, repo_name):
    conn = http.client.HTTPSConnection("api.github.com")
    path = f"/repos/{repo_owner}/{repo_name}/releases/latest"
    headers = {'User-Agent': 'Mozilla/5.0'}
    conn.request("GET", path, headers=headers)
    response = conn.getresponse()
    data = response.read().decode('utf-8')
    conn.close()
    
    if response.status == 200:
        release_info = json.loads(data)
        return release_info
    else:
        print(f"Error al obtener el último release. Código de estado: {response.status}")
        return None

def download_file(url, save_path):
    url_parts = url.split('/')
    host = url_parts[2]
    path = '/' + '/'.join(url_parts[3:])
    conn = http.client.HTTPSConnection(host)
    conn.request("GET", path)
    response = conn.getresponse()
    
    # Si hay redirección, seguirla
    if response.status == 302:
        redirect_url = response.getheader('Location')
        conn.close()
        return download_file(redirect_url, save_path)
    
    if response.status == 200:
        total_size = int(response.getheader('Content-Length', 0))
        chunk_size = 1024  # 1 KB
        downloaded_size = 0

        with open(save_path, 'wb') as file:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                file.write(chunk)
                downloaded_size += len(chunk)
                progress = downloaded_size / total_size * 100
                sys.stdout.write(f"\rDescargando: {progress:.2f}%")
                sys.stdout.flush()
        print(f'\nArchivo descargado y guardado en {save_path}')
    else:
        print(f'Error al descargar el archivo. Código de estado: {response.status}')
    
    conn.close()

def unzip_file(zip_path, extract_to, exclude_files=None):
    if exclude_files is None:
        exclude_files = []

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            if member in exclude_files:
                continue
            zip_ref.extract(member, extract_to)
    print(f'Archivo descomprimido en {extract_to}')

# Ejemplo de uso
repo_owner = "tModLoader"
repo_name = "tModLoader"

# Obtener información del último release
release_info = get_latest_release(repo_owner, repo_name)

if release_info:
    # Mostrar la versión del último release
    version = release_info.get('tag_name', release_info.get('name'))
    print(f"Versión del último release: {version}")

    # Seleccionar automáticamente la segunda opción
    assets = release_info.get('assets', [])
    selected_index = 1  # Índice 1 para seleccionar el segundo archivo
    if 0 <= selected_index < len(assets):
        selected_asset = assets[selected_index]
        asset_url = selected_asset['browser_download_url']
        save_path = os.path.join(os.getcwd(), selected_asset['name'])
        
        # Descargar el archivo seleccionado
        download_file(asset_url, save_path)
        
        # Descomprimir el archivo si es un ZIP, excluyendo archivos específicos
        if save_path.endswith('.zip'):
            exclude_files = ['serverconfig.txt', 'start-tModLoader.bat', 'start-tModLoader-FamilyShare.bat',
                             'start-tModLoaderServer.bat', 'RecentGitHubCommits.txt']  # Cambia esto por los nombres de los archivos que quieras excluir
            unzip_file(save_path, os.getcwd(), exclude_files)
        
        # Eliminar el archivo descargado
        os.remove(save_path)
        print(f'Archivo descargado eliminado: {save_path}')
    else:
        print("No hay suficientes archivos en el release para seleccionar la segunda opción.")
