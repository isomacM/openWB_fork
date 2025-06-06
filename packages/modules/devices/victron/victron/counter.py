#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.victron.victron.config import VictronCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class VictronCounter(AbstractCounter):
    def __init__(self, component_config: VictronCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        unit = self.component_config.configuration.modbus_id
        energy_meter = self.component_config.configuration.energy_meter
        with self.__tcp_client:
            if energy_meter:
                powers = self.__tcp_client.read_holding_registers(2600, [ModbusDataType.INT_16]*3, unit=unit)
                currents = [
                    self.__tcp_client.read_holding_registers(reg, ModbusDataType.INT_16, unit=unit) / 10
                    for reg in [2617, 2619, 2621]]
                voltages = [
                    self.__tcp_client.read_holding_registers(reg, ModbusDataType.UINT_16, unit=unit) / 10
                    for reg in [2616, 2618, 2620]]
                power = sum(powers)
            else:
                powers = self.__tcp_client.read_holding_registers(820, [ModbusDataType.INT_16]*3, unit=unit)
                power = sum(powers)

        imported, exported = self.sim_counter.sim_count(power)

        if energy_meter:
            counter_state = CounterState(
                voltages=voltages,
                currents=currents,
                powers=powers,
                imported=imported,
                exported=exported,
                power=power
            )
        else:
            counter_state = CounterState(
                powers=powers,
                imported=imported,
                exported=exported,
                power=power
            )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VictronCounterSetup)
