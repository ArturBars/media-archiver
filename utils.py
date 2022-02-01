import errno
import hashlib
import os
import shutil
from urllib.parse import urlparse

import requests

from settings import MEDIA_ROOT


def file_from_link(link):
    hashed_link = hashlib.md5(link.encode()).hexdigest()
    file_ext = urlparse(link).path.split('.')[-1]
    file_name = f'{hashed_link}.{file_ext}'
    file_system_path = MEDIA_ROOT.joinpath(file_name)
    return file_system_path


def uri_validator(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except:
        return False


def preload_media(source, link: str):
    file_path = file_from_link(link)

    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    if uri_validator(source):
        response = requests.get(source)

        if response.status_code not in (200,):
            return None

        with open(file_path, 'wb') as file:
            file.write(response.content)
    elif hasattr(source, 'file'):
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(source.file, buffer)
        finally:
            source.file.close()
    elif os.path.exists(os.path.dirname(source)):
        shutil.copy2(source, file_path)
    else:
        return None
    return file_path
