from enum import Enum, auto

class ProcessingStatus(Enum):
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()

def is_terminal_status(status: ProcessingStatus) -> bool:
    return status in (ProcessingStatus.COMPLETED, ProcessingStatus.FAILED)
