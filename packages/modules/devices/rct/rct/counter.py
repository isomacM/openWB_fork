#!/usr/bin/env python3
import logging

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.devices.rct.rct.config import RctCounterSetup
from modules.devices.rct.rct.rct_lib import RCT

log = logging.getLogger(__name__)


class RctCounter(AbstractCounter):
    def __init__(self, component_config: RctCounterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, rct_client: RCT):
        # generate id list for fast bulk read
        my_tab = []
        exported = rct_client.add_by_name(my_tab, 'energy.e_grid_feed_total')
        imported = rct_client.add_by_name(my_tab, 'energy.e_grid_load_total')
        power = rct_client.add_by_name(my_tab, 'g_sync.p_ac_sc_sum')
        volt1 = rct_client.add_by_name(my_tab, 'g_sync.u_l_rms[0]')
        volt2 = rct_client.add_by_name(my_tab, 'g_sync.u_l_rms[1]')
        volt3 = rct_client.add_by_name(my_tab, 'g_sync.u_l_rms[2]')
        power1 = rct_client.add_by_name(my_tab, 'g_sync.p_ac_sc[0]')
        power2 = rct_client.add_by_name(my_tab, 'g_sync.p_ac_sc[1]')
        power3 = rct_client.add_by_name(my_tab, 'g_sync.p_ac_sc[2]')
        freq = rct_client.add_by_name(my_tab, 'grid_pll[0].f')
        stat1 = rct_client.add_by_name(my_tab, 'fault[0].flt')
        stat2 = rct_client.add_by_name(my_tab, 'fault[1].flt')
        stat3 = rct_client.add_by_name(my_tab, 'fault[2].flt')
        stat4 = rct_client.add_by_name(my_tab, 'fault[3].flt')

        # read all parameters
        rct_client.read(my_tab)

        counter_state = CounterState(
            imported=imported.value,
            exported=exported.value*-1.0,
            power=power.value,
            frequency=freq.value,
            powers=[power1.value, power2.value, power3.value],
            voltages=[volt1.value, volt2.value, volt3.value]
        )
        self.store.set(counter_state)
        if (stat1.value + stat2.value + stat3.value + stat4.value) > 0:
            # Werte werden trotz Fehlercode übermittelt.
            self.fault_state.warning(
                f"Speicher-Status ist ungleich 0. Status 1: {stat1.value}, Status 2: {stat2.value}, "
                f"Status 3: {stat3.value}, Status 4: {stat4.value},")


component_descriptor = ComponentDescriptor(configuration_factory=RctCounterSetup)
