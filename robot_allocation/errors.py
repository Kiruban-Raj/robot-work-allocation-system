class AllocationError(Exception):
    """Base class for every user-facing allocation failure."""


class NoRobotsAvailableError(AllocationError):
    def __init__(self):
        super().__init__("Error: No robots available for assignment.")


class InvalidInputError(AllocationError):
    def __init__(self, message: str = "Error: Work hours must be a positive integer."):
        super().__init__(message)


class InsufficientCapacityError(AllocationError):
    def __init__(self):
        super().__init__("Error: Insufficient robot capacity to complete the requested work.")
