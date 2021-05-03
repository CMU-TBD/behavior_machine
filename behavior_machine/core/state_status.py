import enum

@enum.unique
class StateStatus(enum.Enum):
    UNKNOWN = -1     # Unknown
    NOT_RUNNING = 0  # the default state, should be restarted by Parent after transition out
    RUNNING = 1     # The state is currently running
    SUCCESS = 2     # The state finished successfully
    FAILED = 3      # The state failed
    INTERRUPTED = 4  # Being interrupted
    EXCEPTION = 5  # An internal uncatched exception was thrown.
    NOT_SPECIFIED = 6  # execute() didn't say
