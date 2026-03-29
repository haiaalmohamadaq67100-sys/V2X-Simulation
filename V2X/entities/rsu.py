"""
Classe RSU (Road Side Unit) - Unità stradale fissa.
"""

import logging
from typing import Optional, List, Dict, Any
from network_stats import network_stats
from .base import Entity
from utils import sumo_to_geo
from config import RSU_CONFIG, STATION_TYPE_RULES

logger = logging.getLogger(__name__)

class RSU(Entity):
    
    def __init__(self, station_id: int, position: tuple[float, float], name: Optional[str] = None, broadcast_interval: float = 1.0, enabled_messages: Optional[list[str]] = None):
        super().__init__(station_id, name or f"RSU_{station_id}")
        self._x, self._y = position
        self._lat, self._lon = sumo_to_geo(self._x, self._y)
        self.broadcast_interval = broadcast_interval
        self.enabled_messages = enabled_messages or ["cam"]
        
        self._last_send_time: dict[str, float] = {}
        self._current_mcm_executants: List[Dict[str, Any]] = []
        
        # --- NUOVO: Tracciamento sessione attiva per Termination ---
        self._active_manoeuvre_ids: List[int] = [] 
        
        logger.info(f"RSU {self.name} inizializzata a ({self._x}, {self._y})")
    
    @classmethod
    def from_config(cls, station_id: int) -> "RSU":
        config = RSU_CONFIG.get(station_id)
        if not config: raise ValueError(f"RSU {station_id} non trovata")
        return cls(station_id=station_id, position=config["position"], name=config.get("name"), broadcast_interval=config.get("broadcast_interval", 1.0), enabled_messages=config.get("enabled_messages", ["cam"]))
    
    def update(self, sim_time: float, **kwargs) -> None: pass

    def set_mcm_targets(self, targets_data: List[Dict[str, Any]]) -> None:
        """Imposta i target per Request e salva gli ID per la futura Termination."""
        self._current_mcm_executants = []
        
        # Reset della lista attiva con i nuovi ID
        self._active_manoeuvre_ids = []
        
        for t in targets_data:
            strategy = t.get("advised_strategy", "stayInLane")
            executant_entry = {
                "executant_id": t["station_id"],
                "advised_strategy": strategy,
                "submanoeuvres": [{"submanoeuvre_id": 1}]
            }
            self._current_mcm_executants.append(executant_entry)
            
            # Salviamo l'ID per il trigger di termination
            self._active_manoeuvre_ids.append(t["station_id"])
        
        logger.debug(f"RSU {self.station_id}: Target impostati. Attivi: {self._active_manoeuvre_ids}")

    def should_send_message(self, message_type: str, sim_time: float) -> bool:
        if not self.is_message_enabled(message_type): return False
        last_time = self._last_send_time.get(message_type, -float('inf'))
        return (sim_time - last_time) >= self.broadcast_interval
    
    def mark_message_sent(self, message_type: str, sim_time: float) -> None:
        self._last_send_time[message_type] = sim_time
        
        # Se inviamo una Request, puliamo i dati temporanei di costruzione (ma non la sessione attiva)
        if message_type == "mcm_request":
            self._current_mcm_executants = []
            
        # --- NUOVO: Se inviamo Termination, chiudiamo la sessione ---
        if message_type == "mcm_termination":
            logger.info(f"RSU {self.station_id}: Sessione terminata per veicoli {self._active_manoeuvre_ids}")
            self._active_manoeuvre_ids = []

    def _resolve_station_type(self, message_type: str) -> int:
        rules = STATION_TYPE_RULES.get("RSU", {})
        if message_type.startswith("mcm"): return rules.get("mcm", 2) 
        return rules.get(message_type, rules.get("cam", 15))
    
    def get_message_data(self, message_type: str) -> dict:
        current_station_type = self._resolve_station_type(message_type)
        data = { "station_id": self.station_id, "station_type": current_station_type, "lat": self._lat, "lon": self._lon, "speed": 0, "heading": 0, "acceleration": 0 }

        if message_type == "mcm_request":
            manoeuvre_id = 10
            data.update({ "manoeuvre_id": manoeuvre_id, "cost": 50, "executants": self._current_mcm_executants })
            # record request time
            network_stats.record_request(manoeuvre_id)
        # --- NUOVO: Dati per Termination ---
        if message_type == "mcm_termination":
            manoeuvre_id = 10
            data.update({ "manoeuvre_id": manoeuvre_id }) # ID fisso o dinamico
            # record session termination time
            network_stats.record_termination(manoeuvre_id)
        return data

    def get_state_snapshot(self) -> dict:
        return {
            "x": self._x,
            "y": self._y,
            # Passiamo al Trigger l'elenco degli ID sotto coordinamento
            "active_manoeuvre_ids": self._active_manoeuvre_ids 
        }
