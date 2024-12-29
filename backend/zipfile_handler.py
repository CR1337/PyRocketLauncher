import zipfile
import tempfile
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
    
    def __init__(self, zip_filename: str):
        self._temp_directory = tempfile.mkdtemp()
        zipfile.ZipFile(zip_filename).extractall(self._temp_directory)

        metadata_filename = os.path.join(self._temp_directory, 'metadata.json')
        with open(metadata_filename, 'r') as metadata_file:
            self._metadata = json.load(metadata_file)

        if self._metadata['has_fuses']:
            fuses_filename = os.path.join(self._temp_directory, 'fuses.json')
            with open(fuses_filename, 'r') as fuses_file:
                self._fuses_data = json.load(fuses_file)
        else:
            self._fuses_data = None

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
        if os.path.exists(self._temp_directory):
            shutil.rmtree(self._temp_directory)

    def pack_for(self, device_id: str) -> str:
        packed_file = tempfile.NamedTemporaryFile('w', delete=False, suffix='.zip')
        with zipfile.ZipFile(packed_file.name, 'w') as zip_file:
            metadata_bytes = json.dumps(self._metadata).encode('utf-8')
            zip_file.writestr('metadata.json', metadata_bytes)

            if self._fuses_data and device_id in self.fuses_device_ids:
                zip_file.write(self.fuses_filename, 'fuses.json')

            if self._music_data and device_id == self.music_device_ids:
                zip_file.write(
                    self.music_filename, self._metadata['music_filename']
                )

            if self._ilda_data and device_id == self.ilda_device_ids:
                zip_file.write(self.ilda_filename, 'ilda.ildx')

            if self._dmx_data and device_id in self.dmx_device_ids:
                zip_file.write(self.dmx_filename, 'dmx.bin')

        return packed_file.name

    
