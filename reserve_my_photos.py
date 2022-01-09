import requests
import os
import json

from datetime import datetime
from progress.bar import IncrementalBar

class VKDownloader:
    def __init__(self, token: str):
        self.token = token

    def download(self, vk_id, accounting_file, count_of_photos = 5):
        vk_api_url = 'https://api.vk.com/method/photos.get'
        params = {
    'access_token':self.token,
    'v':'5.131',
    'owner_id':vk_id,
    'album_id':'profile',
    'rev':1,
    'extended':1,
    'photo_sizes':0,
    'count':count_of_photos
        }
        res = requests.get(vk_api_url, params=params)
        bar = IncrementalBar('Downloading', max = len(res.json()['response']['items']))
        for index, item in enumerate(res.json()['response']['items']):
            timestamp = int(item['date'])
            url_to_downld = item['sizes'][-1]['url']
            bar.next()
            res_to_downld = requests.get(url_to_downld)
            likes = item['likes']['count']
            date = str(datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S'))
            file_data_to_add = [{'file_name': None , 'size': item['sizes'][-1]['type']}]
            if f'{likes}' not in os.listdir():
                with open(f'{likes}', 'wb') as file:
                    file.write(res_to_downld.content)
                file_data_to_add[0]['file_name'] = f'{likes}'
                if index == 0:
                    with open(accounting_file, 'w') as f:
                        json.dump(file_data_to_add, f)
                else:
                    with open(accounting_file) as f:
                        json_data = json.load(f)
                    with open(accounting_file, 'w') as f:
                        json_data.append(file_data_to_add[0])
                        json.dump(json_data, f)
            else:
                with open(f'{likes}_{date}', 'wb') as file:
                    file.write(res_to_downld.content)
                file_data_to_add[0]['file_name'] = f'{likes}_{date}'
                if index == 0:
                    with open(accounting_file, 'w') as f:
                        json.dump(file_data_to_add, f)
                else:
                    with open(accounting_file) as f:
                        json_data = json.load(f)
                    with open(accounting_file, 'w') as f:
                        json_data.append(file_data_to_add[0])
                        json.dump(json_data, f)
        bar.finish()

class YaUploader:
    def __init__(self, token: str):
        self.token = token
    
    def get_headers(self):
        return {
            'Content-Type': 'application/json', 
            'Authorization': f'OAuth {self.token}'
        }

    def mkdir(self, vk_id):
        path_to_mkdir = f'saved_photos_of_{vk_id}'
        yadisk_api_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = { 'Content-Type': 'application/json', 'Authorization': f'OAuth {self.token}'}
        params = {'path':path_to_mkdir}
        res_to_mkdir = requests.put(url=f'{yadisk_api_url}',params=params,headers=headers)
        return path_to_mkdir

    def upload(self, vk_id, accounting_file, replace=True):
        yadisk_api_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        remote_path = self.mkdir(vk_id)
        with open(accounting_file, 'rb') as f:
            files = json.load(f)
        bar = IncrementalBar('Uploading', max = len(files))
        for file in files:
            path_to_local_file = file['file_name']
            path_to_remote_file = f'{remote_path}/{path_to_local_file}'
            res = requests.get(f'{yadisk_api_url}/upload?path={path_to_remote_file}&overwrite={replace}', headers=headers).json()
            with open(path_to_local_file, 'rb') as f:
                try:
                    requests.put(res['href'], files={'file':f})
                except KeyError:
                    print(res)
            bar.next()
        bar.finish()
   

def main():
    vk_token = ''
    downloader = VKDownloader(vk_token)
    vk_id = ''
    accounting_file = f'photos_of_{vk_id}.json'
    count_of_photos = 2
    result = downloader.download(vk_id, accounting_file, count_of_photos)
    ya_token = ''
    uploader = YaUploader(ya_token)
    result = uploader.upload(vk_id, accounting_file)

main()
