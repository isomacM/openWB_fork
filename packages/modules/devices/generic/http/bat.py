#!/usr/bin/env python3
from typing import Any, TypedDict

from requests import Session

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.generic.http.api import create_request_function, create_request_function_array
from modules.devices.generic.http.config import HttpBatSetup


class KwargsDict(TypedDict):
    device_id: int
    url: str


class HttpBat(AbstractBat):
    def __init__(self, component_config: HttpBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

        self.__get_currents = create_request_function_array(self.kwargs['url'], [
            self.component_config.configuration.current_l1_path,
            self.component_config.configuration.current_l2_path,
            self.component_config.configuration.current_l3_path,
        ])
        self.__get_power = create_request_function(self.kwargs['url'], self.component_config.configuration.power_path)
        self.__get_imported = create_request_function(
            self.kwargs['url'], self.component_config.configuration.imported_path)
        self.__get_exported = create_request_function(
            self.kwargs['url'], self.component_config.configuration.exported_path)
        self.__get_soc = create_request_function(self.kwargs['url'], self.component_config.configuration.soc_path)

    def update(self, session: Session) -> None:
        power = self.__get_power(session)
        exported = self.__get_exported(session)
        imported = self.__get_imported(session)
        if imported is None or exported is None:
            imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            currents=self.__get_currents(session),
            power=power,
            exported=exported,
            imported=imported,
            soc=self.__get_soc(session)
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=HttpBatSetup)
