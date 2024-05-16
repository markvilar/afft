from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class Geolocation:
    latitude: float
    longitude: float
    height: float


@dataclass
class Position3D:
    x: float
    y: float
    z: float


@dataclass
class Orientation3D:
    roll: float
    pitch: float
    yaw: float


@dataclass
class ImageFile:
    label: str
    filename: str


@dataclass
class Camera:
    identifier: str
    label: str
    timestamp: float
    geolocation: Geolocation
    images: Dict[str, ImageFile]
    orientation: Optional[Orientation3D]
    accessories: Optional[Dict[str, float]]

    def has_orientation(self) -> bool:
        """Returns true if the camera has an orientation."""
        return not self.orientation is None

    def has_accessories(self) -> bool:
        """Returns true if the camera has an orientation."""
        return not self.accessories is None

    def as_dict(self) -> Dict[str, int | float | str | bool]:
        """Returns the camera fields as a dictionary."""
        fields = dict()
        fields["identifier"] = self.identifier
        fields["label"] = self.label
        fields["timestamp"] = self.timestamp

        fields.update(asdict(self.geolocation))

        for key in self.images:
            fields.update(
                {
                    key + "_label": self.images[key].label,
                    key + "_filename": self.images[key].filename,
                }
            )

        if self.has_orientation():
            fields.update(asdict(self.orientation))

        if self.has_accessories():
            fields.update(self.accessories)

        return fields
