from enum import Enum


class ProcessingTypesEnum(Enum):
    RoomBox = "ROOM_BOX"
    Preprocessing = "PREPROCESSING"
    Similarity = "SIMILARITY"
    RMatrix = "R_MATRIX"
    Rotate = "ROTATE"
    DoorDetecting = "DOOR_DETECTION"
    ObjectsDetecting = "OBJECTS_DETECTION"
