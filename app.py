import config
from fastapi import FastAPI, UploadFile
from fastapi.responses import RedirectResponse
from lanzou.api import LanZouCloud
import uvicorn
from hashlib import md5
from os import remove

client = LanZouCloud()
status = client.login_by_cookie(config.cookie)  # 登录
if status != LanZouCloud.SUCCESS:
    raise BaseException

api = FastAPI()


@api.post('/upload')
async def upload(file: UploadFile):
    global file_id
    file_id = 0

    def callback(fid, is_file):
        global file_id
        file_id = fid

    file_content: bytes = await file.read()
    file_md5 = md5(file_content).hexdigest()

    # 写临时文件
    temp_file_path = '/tmp/' + file_md5 + '.tar.gz'
    open(temp_file_path, 'wb').write(file_content)
    client.upload_file(file_path=temp_file_path, folder_id=config.folder_id, uploaded_handler=callback)
    remove(temp_file_path)
    file_name = str(file_id) + '.' + file.content_type.split('/')[1]
    return {'file_name': file_name, 'file_id': file_id, 'url': config.url_prefix + '/pic/' + file_name}


@api.get('/pic/{file_name}')
async def get_pic(file_name: str):
    try:
        file_id = int(file_name.split('.')[0])
        url = client.get_durl_by_url(client.get_share_info(file_id).url).durl
        if url == "":
            return {'error': 'error'}
        return RedirectResponse(url)
    except:
        return {'error': 'error'}


@api.get('/info/{file_name}')
async def get_info(file_name: str):
    try:
        file_id = int(file_name.split('.')[0])
        file = client.get_file_info_by_id(file_id)
        return {'file_name': file_name, 'file_id': file_id, 'fake_file_name': file.name, 'direct_url': file.durl,
                'share_url': file.url, 'size': file.size}
    except:
        return {'error': 'error'}


uvicorn.run(app=api, host=config.host, port=config.port)
