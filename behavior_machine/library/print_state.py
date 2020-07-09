from ..core import StateStatus, State


class PrintState(State):

    _text: str

    def __init__(self, name: str, text: str):
        """Constructor for PrintState

        Parameters
        ----------
        name : str
            Name of the State, useful in Debugging.
        text : str
            Text to print on Screen
        """
        super().__init__(name)
        self._text = text

    def execute(self, board):
        print(self._text)
        return StateStatus.SUCCESS
