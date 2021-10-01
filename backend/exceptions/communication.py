from backend.exceptions.exception import BackendException


class CommunicationException(BackendException):
    pass


class ArgosCommunicationException(CommunicationException):
    def __init__(self, port: int) -> None:
        super().__init__(f"Unable to connect to Argos drone on port {port}")


class CrazyflieCommunicationException(CommunicationException):
    def __init__(self, uri: str) -> None:
        super().__init__(f"Unable to connect to Crazyflie drone with URI {uri}")
