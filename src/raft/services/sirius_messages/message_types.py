"""Module for message classes."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from .data_types import (
    AuvMessageHeader,
    ImageCaptureDataV1,
    ImageCaptureDataV2,
    TeledyneDVLData,
    LQModemData,
    EvologicsModemData,
    BatteryData,
    ThrusterData,
)


Header = TypeVar("Header")
Body = TypeVar("Body")


@dataclass
class AuvMessage:

    header: Header
    body: Body

    @property
    def header_type(self) -> type:
        return Header

    @property
    def body_type(self) -> type:
        return Body


# NOTE: Protocol
type ImageMessageV1 = AuvMessage[AuvMessageHeader, ImageCaptureDataV1]
type ImageMessageV2 = AuvMessage[AuvMessageHeader, ImageCaptureDataV2]
type TeledyneDVLMessage = AuvMessage[AuvMessageHeader, TeledyneDVLData]
type LQModemMessage = AuvMessage[AuvMessageHeader, LQModemData]
type EvologicsModemMessage = AuvMessage[AuvMessageHeader, EvologicsModemData]
type BatteryMessage = AuvMessage[AuvMessageHeader, BatteryData]
type ThrusterMessage = AuvMessage[AuvMessageHeader, ThrusterData]
