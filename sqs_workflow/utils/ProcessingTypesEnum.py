from enum import Enum


class ProcessingTypesEnum(Enum):
    RoomBox = "ROOM_BOX"
    Preprocessing = "PREPROCESSING"
    Similarity = "SIMILARITY"
    RMatrix = "R_MATRIX"
    DoorDetecting = "DOOR_DETECTING"
