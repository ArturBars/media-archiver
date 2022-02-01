import errno
import os

import requests
from fastapi import FastAPI, Body, HTTPException, UploadFile, Form
from starlette.requests import Request
from starlette.responses import FileResponse, Response
from starlette.status import HTTP_400_BAD_REQUEST

from utils import file_from_link, preload_media

app = FastAPI()


@app.post('/preload')
def preload(request: Request, file: UploadFile = None,
            source: str = Form(None), link: str = Form(...)):
    if not (source or file):
        return Response('Source file or link not passed.',
                        status_code=HTTP_400_BAD_REQUEST)

    response = preload_media(source or file, link)
    if not response:
        return Response('Cannot read source.',
                        status_code=HTTP_400_BAD_REQUEST)

    return Response(request.url_for('get') + f'?link={link}')


@app.post('/archive')
def archive(request: Request, link: str = Body(..., embed=True)):
    file_path = file_from_link(link)

    response = requests.get(link)

    if response.status_code not in (200,):
        return Response(response.content, status_code=response.status_code)

    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    with open(file_path, 'wb') as file:
        file.write(response.content)

    return Response(request.url_for('get') + f'?link={link}')


@app.get('/get')
def get(link: str):
    file_path = file_from_link(link)

    if not file_path.exists():
        raise HTTPException(status_code=404)

    return FileResponse(file_path)
