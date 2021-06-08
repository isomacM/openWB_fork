""" EV-Logik
ermittelt, den Ladestrom, den das EV gerne zur Verfügung hätte.

In den control parametern wird sich der Lademodus, Submodus, Priorität, Phasen und Stromstärke gemerkt,
mit denen das EV aktuell in der Regelung berücksichtigt wird. Bei der Ermittlung der benötigten Strom-
stärke wird auch geprüft, ob sich an diesen Parametern etwas geändert hat. Falls ja, muss das EV
in der Regelung neu priorisiert werden und eine neue Zuteilung des Stroms erhalten.
"""

import data
import log
import pub
import timecheck


def get_ev_to_rfid(rfid):
    """ sucht zur übergebenen RFID-ID das EV.

    Parameter
    ---------
    rfid: int
        Tag-ID

    Return
    ------
    vehicle: int
        Nummer des EV, das zum Tag gehört
    """
    for vehicle in data.ev_data:
        if "ev" in vehicle:
            try:
                if data.ev_data[vehicle].data["match_ev"]["selected"] == "rfid":
                    if data.ev_data[vehicle].data["match_ev"]["tag_id"] == rfid:
                        return data.ev_data[vehicle].ev_num
            except Exception as e:
                log.exception_logging(e)
                return data.ev_data[0].ev_num
    else:
        return None


class ev():
    """Logik des EV
    """

    def __init__(self, index):
        self.data = {}
        self.ev_template = None
        self.charge_template = None
        self.ev_num = index
        if "set" not in self.data:
            self.data["set"] = {}
        if "control_parameter" not in self.data:
            self.data["control_parameter"] = {}
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/required_current", 0)
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/phases", 0)
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/prio", 0)
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/timestamp_switch_on_off", "0")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/timestamp_auto_phase_switch", "0")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/timestamp_perform_phase_switch", "0")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/submode", "stop")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/chargemode", "stop")
        self.data["control_parameter"]["required_current"] = 0 
        self.data["control_parameter"]["phases"] = 0 
        self.data["control_parameter"]["prio"] = False
        self.data["control_parameter"]["timestamp_switch_on_off"] = "0"
        self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
        self.data["control_parameter"]["timestamp_perform_phase_switch"] = "0"
        self.data["control_parameter"]["submode"] = "stop"
        self.data["control_parameter"]["chargemode"] = "stop"

    def reset_ev(self):
        """ setzt alle Werte zurück, die während des Algorithmus gesetzt werden.
        """
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/required_current", 0)
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/timestamp_switch_on_off", "0")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/timestamp_auto_phase_switch", "0")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/timestamp_perform_phase_switch", "0")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/submode", "stop")
        pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/chargemode", "stop")
        self.data["control_parameter"]["required_current"] = 0 
        self.data["control_parameter"]["timestamp_switch_on_off"] = "0"
        self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
        self.data["control_parameter"]["timestamp_perform_phase_switch"] = "0"
        self.data["control_parameter"]["submode"] = "stop"
        self.data["control_parameter"]["chargemode"] = "stop"

    def get_required_current(self):
        """ ermittelt, ob und mit welchem Strom das EV geladen werden soll (unabhängig vom Lastmanagement)

        Return
        ------
        state: bool
            Soll geladen werden?
        message: str
            Nachricht, warum nicht geladen werden soll
        submode: str
            Lademodus, in dem tatsächlich geladen wird
        required_current: int
            Strom, der nach Ladekonfiguration benötigt wird
        """
        submode = None
        required_current = None
        message = None
        state = True
        try:
            if self.charge_template.data["chargemode"]["selected"] == "scheduled_charging":
                required_current, submode, message = self.charge_template.scheduled_charging(self.data["get"]["soc"], self.ev_template)
            elif self.charge_template.data["time_charging"]["active"] == True:
                required_current, submode, message = self.charge_template.time_charging()
            if (required_current == 0) or (required_current == None):
                if self.charge_template.data["chargemode"]["selected"] == "instant_charging":
                    required_current, submode, message = self.charge_template.instant_charging(self.data["get"]["soc"], self.data["get"]["charged_since_plugged_counter"])
                elif self.charge_template.data["chargemode"]["selected"] == "pv_charging":
                    required_current, submode, message = self.charge_template.pv_charging(self.data["get"]["soc"])
                elif self.charge_template.data["chargemode"]["selected"] == "standby":
                    required_current, submode, message = self.charge_template.standby()
                    
                elif self.charge_template.data["chargemode"]["selected"] == "stop":
                 required_current, submode, message = self.charge_template.stop()
            if submode == "stop" or (self.charge_template.data["chargemode"]["selected"] == "stop"):
                state = False

            return state, message, submode, required_current
        except Exception as e:
            log.exception_logging(e)
            return False, "ein interner Fehler aufgetreten ist.", "stop", 0

    def check_state(self, required_current, submode, set_current):
        """ prüft, ob sich etwas an den Parametern für die Regelung geändert hat, 
        sodass der LP neu in die Priorisierung eingeordnet werden muss und publsihed die Regelparameter.

        Parameter
        ---------
        required_current: int
            neue Stromstärke, mit der geladen werden soll
        submode: str
            neuer Lademodus, in dem geladen werden soll
        set_current: int
            Soll-Stromstärke

        Return
        ------
        mode_changed: bool
            Der Lademodus/ die Konfiguration wurde geändert.
        """
        try:
            mode_changed = False
            # Die benötigte Stromstärke hat sich durch eine Änderung des Lademdous oder der Konfiguration geändert.
            # Der Ladepunkt muss in der Regelung neu priorisiert werden.
            if self.data["control_parameter"]["required_current"] != required_current:
                # Wenn im PV-Laden mit übrigem Überschuss geladen wird und dadurch die aktuelle Soll-Stromstärke über der neuen benötigten Stromstärke liegt, 
                # muss der LP im Algorithmus nicht neu eingeordnet werden, da der LP mit der bisherigen Stormstärke weiter laden kann und sich die benötigte 
                # Stromstärke nur auf die Reihenfolge innerhalb des Prioritätstupels bezieht und auf dieser Ebene kein LP, der bereits lädt, für einen neu 
                # hinzugekommenen abgeschaltet werden darf.
                if ((self.data["control_parameter"]["submode"] == "pv_charging" or self.data["control_parameter"]["chargemode"] == "pv_charging") and 
                    set_current > self.data["control_parameter"]["required_current"]):
                    mode_changed = False
                else:
                    mode_changed = True
            self.data["control_parameter"]["required_current"] = required_current
            self.data["control_parameter"]["submode"] = submode
            pub.pub("openWB/set/vehicle/"+str(self.ev_num) +"/control_parameter/submode", submode)
            self.data["control_parameter"]["chargemode"] = self.charge_template.data["chargemode"]["selected"]
            pub.pub("openWB/set/vehicle/"+str(self.ev_num )+"/control_parameter/chargemode", self.charge_template.data["chargemode"]["selected"])
            self.data["control_parameter"]["prio"] = self.charge_template.data["prio"]
            pub.pub("openWB/set/vehicle/"+str(self.ev_num )+"/control_parameter/prio", self.charge_template.data["prio"])
            return mode_changed
        except Exception as e:
            log.exception_logging(e)
            return True

    def get_soc(self):
        """ermittelt den SoC, wenn die Zugangsdaten konfiguriert sind.
        """
        pass

    def check_min_max_current(self, required_current):
        """ prüft, ob der gesetzte Ladestrom über dem Mindest-Ladestrom und unter dem Maximal-Ladestrom des EVs liegt. Falls nicht, wird der 
        Ladestrom auf den Mindest-Ladestrom bzw. den Maximal-Ladestrom des EV gesetzt.

        Parameter
        ---------
        required_current: float
            Strom, der vom Lademodus benötgt wird

        Return
        ------
        float: Strom, mit dem das EV laden darf
        """
        try:
            # Überprüfung bei 0 (automatische Umschaltung) erfolgt nach der Prüfung der Phasenumschaltung, wenn fest steht, mit vielen Phasen geladen werden soll.
            if self.data["control_parameter"]["phases"] != 0:
                # EV soll/darf nicht laden
                if required_current != 0:
                    if required_current < self.ev_template.data["min_current"]:
                        required_current = self.ev_template.data["min_current"]
                    else:
                        if self.data["control_parameter"]["phases"] == 1:
                            max_current = self.ev_template.data["max_current_one_phase"]
                        else:
                            max_current = self.ev_template.data["max_current_multi_phases"]
                        if required_current > max_current:
                            required_current = max_current
            return required_current
        except Exception as e:
            log.exception_logging(e)
            return 0

    def check_min_max_current_for_pv_charging(self, required_current, phases):
        """ prüft, ob der gesetzte Ladestrom über dem Mindest-Ladestrom des Lademdous und unter dem Maximal-Ladestrom des EVs liegt. Falls nicht, wird der 
        Ladestrom auf den Mindest-Ladestrom bzw. den Maximal-Ladestrom gesetzt.

        Parameter
        ---------
        required_current: float
            Strom, der vom Lademodus benötgt wird

        phases: int
            Anzahl Phasen, mit denen geladen werden soll

        Return
        ------
        float: Strom, mit dem das EV laden darf
        """
        try:
            if required_current != 0:
                if required_current < self.data["control_parameter"]["required_current"]:
                    return self.data["control_parameter"]["required_current"]
                if phases == 1:
                    max_current = self.ev_template.data["max_current_one_phase"]
                else:
                    max_current = self.ev_template.data["max_current_multi_phases"]
                if required_current > max_current:
                    return max_current
            return required_current
        except Exception as e:
            log.exception_logging(e)
            return 0

    def auto_phase_switch(self, current, phases_to_use, current_get):
        """ prüft, ob ein Timer für die Phasenumschaltung gestartet oder gestoppt werden muss oder ein Timer für die Phasenumschaltung abgelaufen ist.

        Parameter
        ---------
        current: int
            Stromstärke, mit der aktuell geladen wird.
        phases_to_use: int
            Anzahl der aktuell nutzbaren Phasen
        current_get: list
            Stromstärke, mit der aktuell geladen wird

        Return
        ------
        phases_to_use: int
            Phasenanzahl , mit der geladen werden soll.
        """
        try:
            pv_config = data.general_data["general"].data["chargemode_config"]["pv_charging"]
            if self.data["control_parameter"]["timestamp_perform_phase_switch"] != "0":
                phase_switch_delay = data.general_data["general"].data["chargemode_config"]["pv_charging"]["phase_switch_delay"]
                if timecheck.check_timestamp(self.data["control_parameter"]["timestamp_perform_phase_switch"], 53+phase_switch_delay-1) == False:
                    self.data["control_parameter"]["timestamp_perform_phase_switch"] = "0"
                    pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_perform_phase_switch", "0")
                    # Aktuelle Ladeleistung und Differenz wieder freigeben.
                    if self.data["control_parameter"]["phases"] == 3:
                        data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.ev_template.data["min_current"] * 3 * 230
                    else:
                        data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.ev_template.data["max_current_one_phase"] * 230
            elif phases_to_use == 1:
                # Wenn im einphasigen Laden mit Maximalstromstärke geladen wird und der Timer abläuft, wird auf 3 Phasen umgeschaltet.
                if self.data["control_parameter"]["timestamp_auto_phase_switch"] != "0" and max(current_get) == self.ev_template.data["max_current_one_phase"]:
                    if timecheck.check_timestamp(self.data["control_parameter"]["timestamp_auto_phase_switch"], pv_config["phase_switch_delay"]*60) == False:
                        phases_to_use = 3
                        # Nach dem Umschalten erstmal mit Mindeststromstärke laden.
                        current = self.ev_template.data["min_current"]
                        self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
                        pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_auto_phase_switch", "0")
                        log.message_debug_log("info", "Umschaltung von 1 auf 3 Phasen.")
                        # Timestamp für die Durchführungsdauer
                        # Aktuelle Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                        data.pv_data["all"].data["set"]["reserved_evu_overhang"] += self.ev_template.data["max_current_one_phase"] * 230
                        self.data["control_parameter"]["timestamp_perform_phase_switch"] = timecheck.create_timestamp()
                        pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_perform_phase_switch", self.data["control_parameter"]["timestamp_perform_phase_switch"])
                # Wenn im einphasigen Laden die Maximalstromstärke erreicht wird und der Timer noch nicht läuft, Timer für das Umschalten auf 3 Phasen starten.
                elif self.data["control_parameter"]["timestamp_auto_phase_switch"] == "0" and max(current_get) == self.ev_template.data["max_current_one_phase"]:
                    self.data["control_parameter"]["timestamp_auto_phase_switch"] = timecheck.create_timestamp()
                    pub.pub("openWB/set/vehicle/"+str(self.ev_num) +
                        "/control_parameter/timestamp_auto_phase_switch", self.data["control_parameter"]["timestamp_auto_phase_switch"])
                    log.message_debug_log("info", "Umschaltverzoegerung von 1 auf 3 Phasen für "+str(pv_config["phase_switch_delay"]) + "Min aktiv.")
                    # Differenz reservieren, damit nicht noch mehr umschalten wollen.
                    data.pv_data["all"].data["set"]["reserved_evu_overhang"] += self.ev_template.data["min_current"] * 3 * 230 - self.ev_template.data["max_current_one_phase"] * 230
                # Wenn der Timer läuft und nicht mit Maximalstromstärke geladen wird, Timer stoppen.
                elif self.data["control_parameter"]["timestamp_auto_phase_switch"] != "0" and max(current_get) < self.ev_template.data["max_current_one_phase"]:
                    self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
                    pub.pub("openWB/set/vehicle/"+str(self.ev_num) +
                            "/control_parameter/timestamp_auto_phase_switch", "0")
                    log.message_debug_log("info", "Umschaltverzoegerung von 1 auf 3 Phasen abgebrochen.")
                    data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.ev_template.data["min_current"] * 3 * 230 - self.ev_template.data["max_current_one_phase"] * 230
            else:
                if self.data["control_parameter"]["timestamp_auto_phase_switch"] != "0" and all((current == self.ev_template.data["min_current"] or current == 0) for current in current_get):
                    if timecheck.check_timestamp(self.data["control_parameter"]["timestamp_auto_phase_switch"], (16-pv_config["phase_switch_delay"])*60) == False:
                        phases_to_use = 1
                        # Nach dem Umschalten wieder mit Maximalstromstärke laden.
                        current = self.ev_template.data["max_current_one_phase"]
                        self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
                        pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_auto_phase_switch", "0")
                        log.message_debug_log("info", "Umschaltung von 3 auf 1 Phase.")
                        # Timestamp für die Durchführungsdauer
                        self.data["control_parameter"]["timestamp_perform_phase_switch"] = timecheck.create_timestamp()
                        pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_perform_phase_switch", self.data["control_parameter"]["timestamp_perform_phase_switch"])
                       # Aktuelle Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                        data.pv_data["all"].data["set"]["reserved_evu_overhang"] += self.ev_template.data["min_current"] * 3 * 230
                # Wenn im dreiphasigen Laden die Minimalstromstärke erreicht wird und der Timer noch nicht läuft, Timer für das Umschalten auf eine Phase starten.
                elif self.data["control_parameter"]["timestamp_auto_phase_switch"] == "0" and all(current == self.ev_template.data["min_current"] for current in current_get):
                    self.data["control_parameter"]["timestamp_auto_phase_switch"] = timecheck.create_timestamp()
                    pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_auto_phase_switch", self.data["control_parameter"]["timestamp_auto_phase_switch"])
                    log.message_debug_log("info", "Umschaltverzoegerung von 3 auf 1 Phase für "+str( 16-pv_config["phase_switch_delay"]) + "Min aktiv.")
                    data.pv_data["all"].data["set"]["reserved_evu_overhang"] += self.ev_template.data["max_current_one_phase"] * 230 - self.ev_template.data["min_current"] * 3 * 230
                # Wenn der Timer läuft und mit mehr als Minimalstromstärke geladen wird, Timer stoppen.
                elif self.data["control_parameter"]["timestamp_auto_phase_switch"] != "0" and any(current > self.ev_template.data["min_current"] for current in current_get):
                    self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
                    pub.pub("openWB/set/vehicle/"+str(self.ev_num) + "/control_parameter/timestamp_auto_phase_switch", "0")
                    log.message_debug_log("info", "Umschaltverzoegerung von 3 auf 1 Phase abgebrochen.")
                    data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.ev_template.data["max_current_one_phase"] * 230 - self.ev_template.data["min_current"] * 3 * 230
            return phases_to_use, current
        except Exception as e:
            log.exception_logging(e) 
            return phases_to_use, current

    def reset_phase_switch(self):
        """ Zurücksetzen der Zeitstempel und reservierten Leistung.

        Die Phasenumschaltung kann nicht abgebrochen werden!
        """
        if self.data["control_parameter"]["timestamp_auto_phase_switch"] != "0":
            self.data["control_parameter"]["timestamp_auto_phase_switch"] = "0"
            pub.pub("openWB/set/vehicle/"+str(self.ev_num)+"/control_parameter/timestamp_auto_phase_switch", "0")
            # Wenn der Timer läuft, ist den Control-Paranetern die alte Phasenzahl hinterlegt.
            if self.data["control_parameter"]["phases"] == 3:
                data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.ev_template.data["max_current_one_phase"] * 230 - self.ev_template.data["min_current"] * 3 * 230
            else:
                data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.ev_template.data["min_current"] * 3 * 230 - self.ev_template.data["max_current_one_phase"] * 230
        elif self.data["control_parameter"]["timestamp_perform_phase_switch"] != "0":
            self.data["control_parameter"]["timestamp_perform_phase_switch"] = "0"
            pub.pub("openWB/set/vehicle/"+str(self.ev_num)+"/control_parameter/timestamp_perform_phase_switch", "0")
            # Leistung freigeben, wird dann neu zugeteilt
            if self.data["control_parameter"]["phases"] == 3:
                data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.ev_template.data["min_current"] * 3 * 230
            else:
                data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.ev_template.data["max_current_one_phase"] * 230

    def load_default_profile(self):
        """ prüft, ob nach dem Abstecken das Standardprofil geladen werden soll und lädt dieses ggf..
        """
        pass

    def lock_cp(self):
        """prüft, ob nach dem Abstecken der LP gesperrt werden soll und sperrt diesen ggf..
        """
        pass


class evTemplate():
    """ Klasse mit den EV-Daten
    """

    def __init__(self, index):
        self.data = {}
        self.et_num = index

class chargeTemplate():
    """ Klasse der Lademodus-Vorlage
    """

    def __init__(self, index):
        self.data = {}
        self.ct_num = index

    def time_charging(self):
        """ prüft, ob ein Zeitfenster aktiv ist und setzt entsprechend den Ladestrom
        """
        message = None
        try:
            # Ein Eintrag gibt an, ob aktiv/inaktiv, alle weiteren sind Zeitpläne.
            if len(self.data["time_charging"]) > 1:
                plan = timecheck.check_plans_timeframe(self.data["time_charging"])
                if plan != None:
                    self.data["time_charging"]["current_plan"] = plan
                    return self.data["time_charging"][plan]["current"], "time_charging", message
                else:
                    self.data["time_charging"]["current_plan"] = ""
                    message = "kein Zeitfenster aktiv ist."
                    return 0, "stop", message
            else:
                self.data["time_charging"]["current_plan"] = ""
                message = "keine Zeitfenster konfiguriert sind."
                return 0, "stop", message
        except Exception as e:
            log.exception_logging(e)
            return 0, "stop", "da ein interner Fehler aufgetreten ist."

    def instant_charging(self, soc, amount):
        """ prüft, ob die Lademengenbegrenzung erreicht wurde und setzt entsprechend den Ladestrom.

        Parameter
        ---------
        soc: int
            SoC des EV

        amount: int
            geladende Energiemenge seit das EV angesteckt wurde
        """
        message = None
        try:
            instant_charging = self.data["chargemode"]["instant_charging"]
            if data.optional_data["optional"].data["et"]["active"] == True:
                if data.optional_data["optional"].et_price_lower_than_limit() == False:
                    message = "der aktuelle Strompreis über dem maximalen Strompreis liegt."
                    return 0, "stop", message
            if instant_charging["limit"]["selected"] == "none":
                return instant_charging["current"], "instant_charging", message
            elif instant_charging["limit"]["selected"] == "soc":
                if soc < instant_charging["limit"]["soc"]:
                    return instant_charging["current"], "instant_charging", message
                else:
                    message = "der Soc bereits erreicht wurde."
                    return 0, "stop", message
            elif instant_charging["limit"]["selected"] == "amount":
                if amount < instant_charging["limit"]["amount"]:
                    return instant_charging["current"], "instant_charging", message
                else:
                    message = "die Energiemenge bereits geladen wurde."
                    return 0, "stop", message
        except Exception as e:
            log.exception_logging(e)
            return 0, "stop", "da ein interner Fehler aufgetreten ist."

    def pv_charging(self, soc):
        """ prüft, ob Min-oder Max-Soc erreicht wurden und setzt entsprechend den Ladestrom.

        Parameter
        ---------
        soc: int
            SoC des EV

        Return
        ------
        Required Current, Chargemode: int, str
            Therotisch benötigter Strom, Ladmodus(soll geladen werden, auch wenn kein PV-Strom zur Verfügung steht)
        """
        message = None
        try:
            pv_charging = self.data["chargemode"]["pv_charging"]
            if soc < pv_charging["max_soc"]:
                if pv_charging["min_soc"] != 0:
                    if soc < pv_charging["min_soc"]:
                        return pv_charging["min_soc_current"], "instant_charging", message
                if pv_charging["min_current"] == 0:
                    return 1, "pv_charging", message  # nur PV; Ampere darf nicht 0 sein, wenn geladen werden soll
                else:
                    return pv_charging["min_current"], "instant_charging", message # Min PV
            else:
                message = "der maximale Soc bereits erreicht wurde."
                return 0, "stop", message
        except Exception as e:
            log.exception_logging(e)
            return 0, "stop", "da ein interner Fehler aufgetreten ist."

    def scheduled_charging(self, soc, ev_template):
        """ prüft, ob der Ziel-SoC erreicht wurde und stellt den zur Erreichung nötigen Ladestrom ein.

        Parameter
        ---------
        soc: int
            Akkustand

        ev_template: dict
            Daten des EV, das geladen werden soll.

        Return
        ------
            Required Current, Chargemode: int, str
                Therotisch benötigter Strom, Ladmodus(soll geladen werden, auch wenn kein PV-Strom zur Verfügung steht)
        """
        try:
            smallest_remaining_time = 0
            plan_data = {"start": -1}
            message = None
            battery_capacity = ev_template.data["battery_capacity"]
            max_phases = ev_template.data["max_phases"]
            start = -1 # Es wurde noch kein Plan geprüft.
            for plan in self.data["chargemode"]["scheduled_charging"]:
                if self.data["chargemode"]["scheduled_charging"][plan]["active"] == True:
                    try:
                        if soc < self.data["chargemode"]["scheduled_charging"][plan]["soc"]:
                            phases_scheduled_charging = data.general_data["general"].get_phases_chargemode(
                                "scheduled_charging")
                            if max_phases <= phases_scheduled_charging:
                                usable_phases = max_phases
                            else:
                                usable_phases = phases_scheduled_charging

                            if usable_phases == 1:
                                max_current = ev_template.data["max_current_one_phase"]
                            else:
                                max_current = ev_template.data["max_current_multi_phases"]
                            available_current = 0.8*max_current*usable_phases
                            required_wh = (
                                (self.data["chargemode"]["scheduled_charging"][plan]["soc"] - soc)/100) * battery_capacity*1000
                            duration = required_wh/(available_current*230)
                            start, remaining_time = timecheck.check_duration(
                                self.data["chargemode"]["scheduled_charging"][plan], duration)
                            # Erster Plan
                            if (start == plan_data["start"] and remaining_time <= smallest_remaining_time) or start > plan_data["start"]:
                                smallest_remaining_time = remaining_time
                                plan_data["plan"] = plan
                                plan_data["available_current"] = available_current
                                plan_data["start"] = start
                                plan_data["required_wh"] = required_wh
                                plan_data["max_current"] = max_current
                        else:
                            message = "da der Ziel-Soc bereits erreicht wurde."
                            return 0, "stop", message
                    except Exception as e:
                        log.exception_logging(e)
            else:
                if start == -1:
                    self.data["chargemode"]["scheduled_charging"]["current_plan"] = ""
                    message = "da keine Ziel-Termine konfiguriert sind."
                    return 0, "stop", message
                else:
                    self.data["chargemode"]["scheduled_charging"]["current_plan"] = plan_data["plan"]
                    if plan_data["start"] == 1: # Ladung sollte jetzt starten
                        return plan_data["available_current"], "instant_charging", message
                    elif plan_data["start"] == 2:  # weniger als die berechnete Zeit verfügbar
                        required_current = plan_data["required_wh"]/(smallest_remaining_time*230)
                        if required_current >= plan_data["max_current"]:
                            plan_data["available_current"] = plan_data["max_current"]
                        else:
                            plan_data["available_current"] = required_current
                        return plan_data["available_current"], "instant_charging", message
                    else:
                        # Liegt der Zieltermin innerhalb der nächsten 24h?
                        if timecheck.check_timeframe(self.data["chargemode"]["scheduled_charging"][plan_data["plan"]], 24) == True:
                            # Wenn Elektronische Tarife aktiv sind, prüfen, ob jetzt ein günstiger Zeitpunkt zum Laden ist.
                            if data.optional_data["optional"].data["et"]["active"] == True:
                                hourlist = data.optional_data["optional"].et_get_loading_hours(
                                    duration)
                                if timecheck.is_list_valid(hourlist) == True:
                                    return plan_data["available_current"], "instant_charging", message
                                else:
                                    message = "da kein günstiger Zeitpunkt zum preisbasierten Laden ist. Falls vorhanden, wird mit EVU-Überschuss geladen."
                                    return ev_template.data["min_current"], "pv_charging", message
                            else:
                                message = "da noch Zeit bis zum Zieltermmin ist. Falls vorhanden, wird mit EVU-Überschuss geladen."
                                return ev_template.data["min_current"], "pv_charging", message
                        else:
                            message = "da noch mehr als ein Tag bis zum Zieltermmin ist. "
                            return 0, "stop", message
        except Exception as e:
            log.exception_logging(e)
            return 0, "stop", "da ein interner Fehler aufgetreten ist."

    def standby(self):
        """ setzt den benötigten Strom auf 0.

        Return
        ------
            Required Current, Chargemode: int, str
                Therotisch benötigter Strom, Ladmodus
        """
        message = "der Lademodus Standby aktiv ist."
        return 0, "standby", message

    def stop(self):
        """ setzt den benötigten Strom auf 0.

        Return
        ------
            Required Current, Chargemode: int, str
                Therotisch benötigter Strom, Ladmodus
        """
        message = "der Lademdus Stop aktiv ist."
        return 0, "stop", message