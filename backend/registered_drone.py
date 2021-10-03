from dataclasses import dataclass

from backend.communication.argos_drone_link import ArgosDroneLink
from backend.communication.drone_link import DroneLink
from backend.models.drone import Drone, DroneType
from backend.state import DroneState


@dataclass
class RegisteredDrone:
    uuid: str
    link: DroneLink
    state: DroneState = DroneState.WAITING

    @property
    def drone_type(self) -> DroneType:
        return DroneType.ARGOS if isinstance(self.link, ArgosDroneLink) else DroneType.CRAZYFLIE

    def to_model(self) -> Drone:
        return Drone(uuid=self.uuid, state=self.state, type=self.drone_type)
