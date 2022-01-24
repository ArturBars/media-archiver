import errno
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, Body, HTTPException
from starlette.responses import FileResponse, Response
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

MEDIA_ROOT = BASE_DIR / 'static'


def file_from_link(link):
    hashed_link = hashlib.md5(link.encode()).hexdigest()
    file_ext = urlparse(link).path.split('.')[-1]
    file_name = f'{hashed_link}.{file_ext}'
    file_system_path = MEDIA_ROOT.joinpath(file_name)
    return file_system_path


@app.post('/archive')
def archive(link: str = Body(..., embed=True)):
    file_path = file_from_link(link)

    response = requests.get(link)

    if response.status_code != 200:
        return HTTP_400_BAD_REQUEST

    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    with open(file_path, 'wb') as file:
        file.write(response.content)

    return Response(status_code=HTTP_201_CREATED)


@app.get('/get')
def get(link: str):
    file_path = file_from_link(link)

    if not file_path.exists():
        raise HTTPException(status_code=404)

    return FileResponse(file_path)
