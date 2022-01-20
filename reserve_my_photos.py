import requests
import json

from datetime import datetime
from progress.bar import IncrementalBar

class VKDownloader:
    def __init__(self, token: str):
        self.token = token

    def get_urls_to_upload(self, vk_id, count_of_photos = 5):
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
        if list(res.json().keys())[0] != 'error':
            info_json = []
            list_of_names = []
            for item in res.json()['response']['items']:
                timestamp = int(item['date'])
                likes = item['likes']['count']
                file_data_to_add = {'file_name': None , 'size': item['sizes'][-1]['type'], 'url_to_downld': item['sizes'][-1]['url']}
                if f'likes' not in list_of_names:
                    file_data_to_add['file_name'] = f'{likes}'
                else:
                    date = str(datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S'))
                    file_data_to_add['file_name'] = f'{likes}_{date}'
                info_json.append(file_data_to_add)
            return info_json
        else:
            print('При обращении к Вконтакте возникла ошибка')
            print(f'Код ошибки - {res.json()["error"]["error_code"]}')
            print(f'Сообщение от сервера: {res.json()["error"]["error_msg"]}')

class YaUploader:
    def __init__(self, token: str):
        self.token = token
    
    def get_headers(self):
        return {
            'Content-Type': 'application/json', 
            'Authorization': f'OAuth {self.token}'
        }

    def _mkdir(self, vk_id):
        path_to_mkdir = f'saved_photos_of_{vk_id}'
        yadisk_api_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = { 'Content-Type': 'application/json', 'Authorization': f'OAuth {self.token}'}
        params = {'path':path_to_mkdir}
        res_to_mkdir = requests.put(url=f'{yadisk_api_url}',params=params,headers=headers)
        if res_to_mkdir.status_code != 201 and res_to_mkdir.status_code != 409:
            print('При создании папки возникла ошибка.')
            to_print = self._print_error_info(res_to_mkdir)
            return None
        return path_to_mkdir

    def upload(self, vk_id, info_json):
        yadisk_api_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        remote_path = self._mkdir(vk_id)
        # If directory creation ended succesfully
        if remote_path != None:
            params = {
                'path' : None,
                'url' : None
            }
            bar = IncrementalBar('Загрузка на Я.Диск', max = len(info_json))
            for item in info_json:
                params['path'] = f'{remote_path}/{item["file_name"]}'
                params['url'] = item['url_to_downld']
                res = requests.post(yadisk_api_url, params=params, headers=headers)
                if res.status_code != 202:
                    print(f'При загрузке файла "{item["file_name"]}" возникла ошибка.')
                    to_print = self._print_error_info(res)
                else:
                    bar.next()
                    pass
            bar.finish()
            res = self._upload_json_to_remote_disk(info_json, f'{remote_path}/file_info.json')


    def _get_upload_link(self, disk_file_path):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        params = {'path': disk_file_path, 'overwrite': 'true'}
        res = requests.get(upload_url, headers=headers, params=params)
        if res.status_code == 200:
            return res.json()
        else:
            print(f'При получении ссылки для загрузки JSON-файла возникла ошибка.')
            to_print = self._print_error_info(res)

    def _upload_json_to_remote_disk(self, info_json, disk_file_path):
        for dict_of_file in info_json:
            del dict_of_file['url_to_downld']
        href_attr = self._get_upload_link(disk_file_path=disk_file_path)
        if href_attr != None:
            href_attr = href_attr.get('href', '')
            res = requests.put(href_attr, data=json.dumps(info_json))
            res.raise_for_status()
            if res.status_code != 201:
                print(f'При загрузке JSON-файла возникла ошибка.')
                to_print = self._print_error_info(res)
    
    def check_user(self):
        yadisk_api_url = 'https://cloud-api.yandex.net/v1/disk'
        headers = self.get_headers()
        res = requests.get(url=yadisk_api_url, headers=headers)
        if res.status_code == 200:
            return True
        else:
            print('Возникла проблема при обращении к Я.Диску по токену:')
            to_print = self._print_error_info(res)
            return False

    def _print_error_info(self, res):
        print(f'Статус ответа - {res.status_code}')
        reply = res.json()
        print(f'Сообщение от сервера Я.Диска - {reply["message"]}')

def main():
    vk_token = ''
    ya_token = ''
    downloader = VKDownloader(vk_token)
    vk_id = ''
    count_of_photos = 2
    info_json = downloader.get_urls_to_upload(vk_id, count_of_photos)
    if info_json != None:
        uploader = YaUploader(ya_token)
        if uploader.check_user() != False:
            result = uploader.upload(vk_id, info_json)

main()
