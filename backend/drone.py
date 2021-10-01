from dataclasses import dataclass

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.drone_link import DroneLink
from backend.models.drone_model import DroneModel, DroneType
from backend.state import DroneState


@dataclass
class Drone:
    uuid: str
    link: DroneLink
    state: DroneState = DroneState.WAITING

    @property
    def drone_type(self) -> DroneType:
        return DroneType.ARGOS if isinstance(self.link, ArgosDroneLink) else DroneType.CRAZYFLIE

    def to_model(self) -> DroneModel:
        return DroneModel(uuid=self.uuid, state=self.state, type=self.drone_type)
