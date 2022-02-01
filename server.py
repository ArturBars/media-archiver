import errno
import logging
import os

import requests
from fastapi import FastAPI, Body, HTTPException, UploadFile, Form
from starlette.requests import Request
from starlette.responses import FileResponse, Response
from starlette.status import HTTP_400_BAD_REQUEST

from utils import file_from_link, preload_media


def check_dir(path):
    """Check dir. Create if not exists."""
    if not os.path.isdir(path):
        os.makedirs(path)
        return True
    return False


check_dir('logs')

fileHandler = logging.FileHandler('logs/info.log')
consoleHandler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        fileHandler,
        consoleHandler
    ]
)
logger = logging.getLogger()

app = FastAPI()


@app.post('/preload')
def preload(request: Request, file: UploadFile = None,
            source: str = Form(None), link: str = Form(...)):
    if not (source or file):
        return Response('Source file or link not passed.',
                        status_code=HTTP_400_BAD_REQUEST)

    response, errors = preload_media(source or file, link)
    if errors:
        return Response(f'Cannot read source. Reason: {errors}',
                        status_code=HTTP_400_BAD_REQUEST)
    logger.info(f'Link {link} archived.')
    return Response(request.url_for('get') + f'?link={link}')


@app.post('/archive')
def archive(request: Request, link: str = Body(..., embed=True)):
    file_path = file_from_link(link)

    response = requests.get(link)

    if response.status_code not in (200,):
        logger.info(f'Link {link} no archived. Reason: {response.content}')
        return Response(response.content, status_code=response.status_code)

    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    with open(file_path, 'wb') as file:
        file.write(response.content)
    logger.info(f'Link {link} archived.')
    return Response(request.url_for('get') + f'?link={link}')


@app.get('/get')
def get(link: str):
    file_path = file_from_link(link)

    if not file_path.exists():
        raise HTTPException(status_code=404)
    logger.info(f'Link {link} requested.')
    return FileResponse(file_path)
