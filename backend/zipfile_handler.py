import zipfile
import tempfile
import io
import json
import os
import shutil
from typing import Dict, Any, List


class ZipfileHandler:

    _temp_directory: str

    _metadata: Dict[str, Any]

    _fuses_data: List[Dict[str, Any]]
    _music_data: bytes
    _ilda_data: bytes
    _dmx_data: bytes
    
    def __init__(self, zip_data: bytes):
        self._temp_directory = tempfile.mkdtemp()
        zipfile.ZipFile(io.BytesIO(zip_data)).extractall(self._temp_directory)

        metadata_filename = os.path.join(self._temp_directory, 'metadata.json')
        with open(metadata_filename, 'r') as metadata_file:
            self._metadata = json.load(metadata_file)

        if self._metadata['has_fuses']:
            fuses_filename = os.path.join(self._temp_directory, 'fuses.json')
            with open(fuses_filename, 'r') as fuses_file:
                self._fuses_data = fuses_file.read()
        else:
            self._fuses_data = None

        if self._metadata['has_music']:
            music_filename = os.path.join(
                self._temp_directory, 
                self._metadata['music_filename']
            )   
            with open(music_filename, 'rb') as music_file:
                self._music_data = music_file.read()
        else:
            self._music_data = None

        if self._metadata['has_ilda']:
            ilda_filename = os.path.join(self._temp_directory, 'ilda.ildx')
            with open(ilda_filename, 'rb') as ilda_file:
                self._ilda_data = ilda_file.read()
        else:
            self._ilda_data = None

        if self._metadata['has_dmx']:
            dmx_filename = os.path.join(self._temp_directory, 'dmx.bin')
            with open(dmx_filename, 'rb') as dmx_file:
                self._dmx_data = dmx_file.read()
        else:
            self._dmx_data = None

    @property
    def has_fuses(self) -> bool:
        return self._metadata['has_fuses']
    
    @property
    def has_music(self) -> bool:
        return self._metadata['has_music']
    
    @property
    def has_ilda(self) -> bool:
        return self._metadata['has_ilda']
    
    @property
    def has_dmx(self) -> bool:
        return self._metadata['has_dmx']
    
    @property
    def fuses_device_ids(self) -> List[str]:
        return self._metadata['fuses_device_ids']
    
    @property
    def music_device_ids(self) -> str:
        return self._metadata['music_device_ids']
    
    @property
    def ilda_device_ids(self) -> str:
        return self._metadata['ilda_device_ids']
    
    @property
    def dmx_device_ids(self) -> List[str]:
        return self._metadata['dmx_device_ids']
    
    @property
    def fuses_filename(self) -> str:
        return os.path.join(self._temp_directory, 'fuses.json')
    
    @property
    def music_filename(self) -> str:
        return os.path.join(
            self._temp_directory, 
            self._metadata['music_filename']
        )
    
    @property
    def ilda_filename(self) -> str:
        return os.path.join(self._temp_directory, 'ilda.ildx')
    
    @property
    def dmx_filename(self) -> str:
        return os.path.join(self._temp_directory, 'dmx.bin')

    @property
    def fuses_data(self) -> str:
        return self._fuses_data

    def __del__(self):
        shutil.rmtree(self._temp_directory)

    def pack_for(self, device_id: str) -> bytes:
        zip_data = io.BytesIO()
        with zipfile.ZipFile(zip_data, 'w') as zip_file:
            metadata_bytes = json.dumps(self._metadata).encode('utf-8')
            zip_file.writestr('metadata.json', metadata_bytes)
            if self._fuses_data and device_id in self.fuses_device_ids:
                zip_file.writestr('fuses.json', self._fuses_data)
            if self._music_data and device_id == self.music_device_ids:
                zip_file.writestr(
                    self._metadata['music_filename'], self._music_data
                )
            if self._ilda_data and device_id == self.ilda_device_ids:
                zip_file.writestr('ilda.ildx', self._ilda_data)
            if self._dmx_data and device_id in self.dmx_device_ids:
                zip_file.writestr('dmx.bin', self._dmx_data)
        return zip_data.getvalue()

    
