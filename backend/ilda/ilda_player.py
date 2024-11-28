from dataclasses import dataclass
from typing import List, Tuple, Dict
import ctypes

from backend.ilda.ilda import IldaInterface, HeliosPoint
from backend.ilda.ildx import (
    IldxFormatCode, ILDX_STATUS_CODE_BLANKING_MASK, 
    IldxHeader, Ildx3dIndexedRecord, 
    Ildx2dIndexedRecord, IldxColorPlatteRecord, Ildx3dTrueColorRecord, 
    Ildx2dTrueColorRecord, decode_start_timestamp
)

from backend.abstract_player import AbstractPlayer, AbstractPlayerItem


@dataclass
class IldaFrame(AbstractPlayerItem):
    points: List[HeliosPoint] = None
    last_frame: bool = False
    timestamp: float = None
    points_per_second: int = None


@dataclass
class IldaAnimation:
    frames: List[IldaFrame]
    start_timestamp: int
    fps: int


ColorPalette = List[Tuple[int, int, int]]

class IldaPlayer(AbstractPlayer):
    DAC_INDEX: int = 0
    HEADER_SIZE: int = ctypes.sizeof(IldxHeader)
    COLOR_SIZE: int = ctypes.sizeof(IldxColorPlatteRecord)
    MAX_ATTEMPS: int = 128
    OUTPUT_IMMEADIATELY: int = 0b01
    PLAY_ONLY_ONCE: int = 0b10

    DEFAULT_FPS: int = 30
    DEFAULT_COLOR_PALETTE: ColorPalette = [
        (255, 0, 0),
        (255, 16, 0),
        (255, 32, 0),
        (255, 48, 0),
        (255, 64, 0),
        (255, 80, 0),
        (255, 96, 0),
        (255, 112, 0),
        (255, 128, 0),
        (255, 144, 0),
        (255, 160, 0),
        (255, 176, 0),
        (255, 192, 0),
        (255, 208, 0),
        (255, 224, 0),
        (255, 240, 0),
        (255, 255, 0),
        (224, 255, 0),
        (192, 255, 0),
        (160, 255, 0),
        (128, 255, 0),
        (96, 255, 0),
        (64, 255, 0),
        (32, 255, 0),
        (0, 255, 0),
        (0, 255, 36),
        (0, 255, 73),
        (0, 255, 109),
        (0, 255, 146),
        (0, 255, 182),
        (0, 255, 219),
        (0, 255, 255),
        (0, 227, 255),
        (0, 198, 255),
        (0, 170, 255),
        (0, 142, 255),
        (0, 113, 255),
        (0, 85, 255),
        (0, 56, 255),
        (0, 28, 255),
        (0, 0, 255),
        (32, 0, 255),
        (64, 0, 255),
        (96, 0, 255),
        (128, 0, 255),
        (160, 0, 255),
        (192, 0, 255),
        (224, 0, 255),
        (255, 0, 255),
        (255, 32, 255),
        (255, 64, 255),
        (255, 96, 255),
        (255, 128, 255),
        (255, 160, 255),
        (255, 192, 255),
        (255, 224, 255),
        (255, 255, 255),
        (255, 224, 224),
        (255, 192, 192),
        (255, 160, 160),
        (255, 128, 128),
        (255, 96, 96),
        (255, 64, 64),
        (255, 32, 32)
    ]
    DEFAULT_COLOR_PALETTE = DEFAULT_COLOR_PALETTE * (256 // len(DEFAULT_COLOR_PALETTE))

    _animations: Dict[float, IldaAnimation]
    _color_palette: ColorPalette

    def __init__(self, ildx_filename: str):
        device_amount = IldaInterface.OpenDevices()
        if device_amount < 1:
            raise RuntimeError("No ILDA devices found")
        
        IldaInterface.SetShutter(self.DAC_INDEX, 1)
        
        with open(ildx_filename, 'rb') as file:
            ildx_data = file.read()

        self._color_palette = self.DEFAULT_COLOR_PALETTE

        self._animations = {}
        current_animation, offset, was_palette = self._read_animation(ildx_data, 0)
        while current_animation is not None:
            if not was_palette:
                self._animations[current_animation.start_timestamp / 1000.0] = current_animation
            current_animation, offset, was_palette = self._read_animation(
                ildx_data, offset
            )

        self._attach_timestamps()
        self._extract_items()

        super().__init__()

    def destroy(self):
        super().destroy()
        IldaInterface.CloseDevices()
                
    def _read_animation(
        self, data: bytes, offset: int
    ) -> Tuple[IldaAnimation, int, bool]:
        try:
            header = IldxHeader.from_buffer_copy(data[offset:offset + self.HEADER_SIZE])
        except ValueError:
            return None, offset, False

        fps = header.framesPerSecondOrFrameAmount
        if fps == 0:
            fps = self.DEFAULT_FPS
        start_timestamp = decode_start_timestamp(header)

        format_code = IldxFormatCode(header.formatCode)
        if format_code == IldxFormatCode.ILDX_FORMAT_CODE_COLOR_PALETTE:
            self._color_palette, offset = self._read_palette(data, offset)
            return IldaAnimation(None, -1, -1), offset, True

        total_frames = header.totalFrames
        if total_frames == 0:
            return None, offset + self.HEADER_SIZE, False
        
        frames = []
        for i in range(total_frames):
            new_frames, offset = self._read_frame(data, offset, i == 0)
            if new_frames is not None:
                frames.extend(new_frames)
            else:
                return None, offset, False

        return IldaAnimation(frames, start_timestamp, fps), offset, False
    
    def _read_palette(self, data: bytes, offset: int) -> Tuple[ColorPalette, int]:
        header = IldxHeader.from_buffer_copy(data[offset:offset + self.HEADER_SIZE])
        number_of_colors = header.numberOfRecords

        palette = []
        for i in range(number_of_colors):
            color = IldxColorPlatteRecord.from_buffer_copy(
                data[offset + i * self.COLOR_SIZE:offset + (i + 1) * self.COLOR_SIZE]
            )
            palette.append((color.red, color.green, color.blue))
        
        return palette, offset + self.HEADER_SIZE + number_of_colors * self.COLOR_SIZE

    def _read_frame(self, data: bytes, offset: int, is_first_frame: bool = False) -> Tuple[List[IldaFrame], int]:
        try:
            header = IldxHeader.from_buffer_copy(data[offset:offset + self.HEADER_SIZE])
        except ValueError:
            return None, offset + self.HEADER_SIZE
        
        format_code = IldxFormatCode(header.formatCode)
        number_of_points = header.numberOfRecords
        if is_first_frame:
            repetitions = 1
        else:
            repetitions = max(1, header.framesPerSecondOrFrameAmount)
        
        if format_code == IldxFormatCode.ILDX_FORMAT_CODE_3D_INDEXED:
            point_type = Ildx3dIndexedRecord
            point_size = ctypes.sizeof(Ildx3dIndexedRecord)
            converter_func = self._convert_indexed_point
        elif format_code == IldxFormatCode.ILDX_FORMAT_CODE_2D_INDEXED:
            point_type = Ildx2dIndexedRecord
            point_size = ctypes.sizeof(Ildx2dIndexedRecord)
            converter_func = self._convert_indexed_point
        elif format_code == IldxFormatCode.ILDX_FORMAT_CODE_3D_TRUE_COLOR:
            point_type = Ildx3dTrueColorRecord
            point_size = ctypes.sizeof(Ildx3dTrueColorRecord)
            converter_func = self._convert_true_color_point
        elif format_code == IldxFormatCode.ILDX_FORMAT_CODE_2D_TRUE_COLOR:
            point_type = Ildx2dTrueColorRecord
            point_size = ctypes.sizeof(Ildx2dTrueColorRecord)
            converter_func = self._convert_true_color_point

        raw_points = (
            point_type.from_buffer_copy(
                data[offset + i * point_size:offset + (i + 1) * point_size]
            )
            for i in range(number_of_points)
        )
        points = [converter_func(point) for point in raw_points]

        return [IldaFrame(None, points) for _ in range(repetitions)], offset + self.HEADER_SIZE + number_of_points * point_size
    
    def _rescale_point(self, x: int, y: int) -> Tuple[int, int]:
        return (x + 0xFFFF // 2) * 0xFFF // 0xFFFF, (y + 0xFFFF // 2) * 0xFFF // 0xFFFF

    def _convert_indexed_point(self, point: Ildx2dIndexedRecord | Ildx3dIndexedRecord) -> HeliosPoint:
        blanked = bool(point.statusCode & ILDX_STATUS_CODE_BLANKING_MASK)
        return HeliosPoint(
            *self._rescale_point(point.x, point.y),
            *self._color_palette[point.colorIndex],
            0 if blanked else 255
        )

    def _convert_true_color_point(self, point: Ildx3dTrueColorRecord | Ildx2dTrueColorRecord) -> HeliosPoint:
        blanked = bool(point.statusCode & ILDX_STATUS_CODE_BLANKING_MASK)
        return HeliosPoint(
            *self._rescale_point(point.x, point.y),
            point.r, point.g, point.b,
            0 if blanked else 255
        )
    
    def _attach_timestamps(self):
        for start_timestamp, animation in self._animations.items():
            start_timestamp = start_timestamp / 1000.0
            ms_per_frame = 1000.0 / animation.fps
            for i, frame in enumerate(animation.frames):
                if frame.points is None:
                    frame.points = []
                frame.timestamp = start_timestamp + (i * ms_per_frame) / 1000.0
                if i == len(animation.frames) - 1:
                    frame.last_frame = True
                frame.points_per_second = animation.fps * len(frame.points)
                
    def _extract_items(self):
        self._items = []
        for animation in self._animations.values():
            self._items.extend(animation.frames)
            
    def destroy(self):
        super().destroy()
        IldaInterface.CloseDevices()

    def _play_item(self):
        frame = self._items[self._current_item_index]
        
        n_points = len(frame.points)
        HeliosPointArray = HeliosPoint * n_points
        points_array = HeliosPointArray(*frame.points)

        n_attemps = 0
        while(n_attemps < self.MAX_ATTEMPS and IldaInterface.GetStatus(self.DAC_INDEX) != 1):
            n_attemps += 1
        IldaInterface.WriteFrame(
            self.DAC_INDEX, 
            frame.points_per_second, 
            self.OUTPUT_IMMEADIATELY | self.PLAY_ONLY_ONCE,
            points_array, 
            len(frame.points)
        )

    def _start_playing(self):
        IldaInterface.SetShutter(self.DAC_INDEX, 0)

    def _end_playing(self):
        IldaInterface.Stop(self.DAC_INDEX)
        IldaInterface.SetShutter(self.DAC_INDEX, 1)