import requests
import os
import json

from datetime import datetime
from progress.bar import IncrementalBar
from pprint import pprint

class VKDownloader:
    def __init__(self, token: str):
        self.token = token

    def get_urls_to_upload(self, vk_id, accounting_file, count_of_photos):
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
        dict_of_urls = {}
        res = requests.get(vk_api_url, params=params)
        if res.status_code == 200:
            for item in res.json()['response']['items']:
                timestamp = int(item['date'])
                url_to_downld = item['sizes'][-1]['url']
                likes = item['likes']['count']
                date = str(datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S'))
                file_data_to_add = [{'file_name': None , 'size': item['sizes'][-1]['type']}]
                # Ckeck whether JSON-file exists
                if os.path.isfile(accounting_file) and len(dict_of_urls) == 0:
                    os.remove(accounting_file)
                    file_data_to_add[0]['file_name'] = f'{likes}'
                    with open(accounting_file, 'w') as f:
                        json.dump(file_data_to_add, f)
                else:
                    if len(dict_of_urls) == 0:
                        with open(accounting_file, 'w') as f:
                            dummy_data = []
                            json.dump(dummy_data, f)
                    with open(accounting_file) as f:
                        json_data = json.load(f)
                        list_of_names_in_json = []
                        for item in json_data:
                            list_of_names_in_json.append(item['file_name'])
                        # Check whether 'file-name' is in JSON before writing
                        if f'{likes}' not in list_of_names_in_json:
                            file_data_to_add[0]['file_name'] = f'{likes}'
                            with open(accounting_file, 'w') as f:
                                json.dump(file_data_to_add, f)
                        else:
                            file_data_to_add[0]['file_name'] = f'{likes}_{date}'
                            with open(accounting_file, 'w') as f:
                                json.dump(file_data_to_add, f)
                # Add pair of NAME-URL to dict
                dict_of_urls[file_data_to_add[0]['file_name']] = url_to_downld
        else:
            print('При обращении к Вконтакте возникла ошибка')
            print(f'Статус ответа - {res.status_code}')
        return dict_of_urls

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
        if res_to_mkdir.status_code != 201 and res_to_mkdir.status_code != 409:
            print('При создании папки возникла ошибка.')
            print(f'Статус ответа - {res_to_mkdir.status_code}')
            reply = res_to_mkdir.json()
            print(f'Сообщение от сервера Я.Диска - {reply["message"]}')
            return None
        return path_to_mkdir

    def upload(self, vk_id, dict_of_urls, replace=True):
        yadisk_api_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        remote_path = self.mkdir(vk_id)
        # If directory creation ended succesfully
        if remote_path != None:
            params = {
                'path' : None,
                'url' : None
            }
            bar = IncrementalBar('Загрузка на Я.Диск', max = len(dict_of_urls))
            for url in dict_of_urls.items():
                params['path'] = f'{remote_path}/{url[0]}'
                params['url'] = url[1]
                res = requests.post(yadisk_api_url, params=params, headers=headers)
                if res.status_code != 202:
                    print(f'При загрузке файла "{url[0]}" возникла ошибка.')
                    print(f'Статус ответа - {res.status_code}')
                    reply = res.json()
                    print(f'Сообщение от сервера Я.Диска - {reply["message"]}')
                else:
                    bar.next()
                    pass
            bar.finish()
    
    def check_user(self):
        yadisk_api_url = 'https://cloud-api.yandex.net/v1/disk'
        headers = self.get_headers()
        res = requests.get(url=yadisk_api_url, headers=headers)
        if res.status_code == 200:
            return True
        else:
            print('Возникла проблема при обращении к Я.Диску по токену:')
            print(f'Статус ответа - {res.status_code}')
            reply = res.json()
            print(f'Сообщение от сервера Я.Диска - {reply["message"]}')
            return False

def main():
    vk_token = ''
    downloader = VKDownloader(vk_token)
    vk_id = ''
    accounting_file = f'photos_of_{vk_id}.json'
    count_of_photos = 2
    list_of_urls = downloader.get_urls_to_upload(vk_id,accounting_file, count_of_photos)
    ya_token = ''
    uploader = YaUploader(ya_token)
    if uploader.check_user() == True:
        result = uploader.upload(vk_id, list_of_urls)

main()