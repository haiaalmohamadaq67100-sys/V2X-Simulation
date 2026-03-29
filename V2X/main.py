#!/usr/bin/env python3
"""
V2X Simulator - Entry Point (Batch Mode Enabled)
"""

import sys
import time
import logging
import json
import argparse  # <--- AGGIUNTO
from typing import Optional

import traci
import sumolib

# Configurazione
import config # Importiamo il modulo intero per modificarlo runtime
from config import (
    SUMO_CFG, SUMO_STEP_LENGTH, SUMO_GUI,
    RSU_CONFIG, LOGGING, STATIONS, MQTT_TOPICS
)

# Moduli interni
from utils import get_station_id_from_veh, get_generation_delta_time, euclidean_distance
from mqtt_manager import mqtt_manager
from network_stats import network_stats
from entities import RSU, Vehicle
from messages import MessageFactory
from triggers import TriggerRegistry
from triggers.mcm_trigger import RSUMCMRequestTrigger

logging.basicConfig(
    level=getattr(logging, LOGGING.get("level", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("V2X_Simulator")


class V2XSimulator:
    
    def __init__(self, route_override=None):
        self.route_override = route_override  # <--- Salva il file rotte personalizzato
        
        self.rsus: dict[int, RSU] = {}
        self.vehicles: dict[str, Vehicle] = {}
        self.vehicle_trigger_states: dict[str, dict[str, dict]] = {}
        self.triggers = {}
        self._running = False
        self._incoming_mcm_queue = []
    
    def initialize(self):
        # 1. Avvia SUMO
        self._start_sumo()
        
        # --- CONTROLLO MODALITÀ ---
        # Leggiamo direttamente dal modulo config che è stato aggiornato nel main()
        if config.SIMULATION_MODE == "BASELINE":
            logger.info("Modalità BASELINE attiva: Logica V2X disabilitata.")
            return
        
        # 2. Crea RSU e Trigger (Solo V2X)
        self._initialize_rsus()
        self._initialize_triggers()
        self._setup_mqtt_listeners()

        logger.info("Simulatore inizializzato (V2X Attivo)")

    def _setup_mqtt_listeners(self):
        listener_client = mqtt_manager.get_client(0) 
        if listener_client:
            listener_client.on_message = self._on_mqtt_message
            topic = "vanetza/in/mcm"
            listener_client.subscribe(topic)
            logger.info(f"Ascolto attivo su topic MQTT: {topic}")

    def _on_mqtt_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            # detect CAM
            if "camParameters" in payload:
                network_stats.record_cam_received(0)
                return
            self._incoming_mcm_queue.append(payload)
        except Exception as e:
            logger.error(f"Errore parsing MQTT: {e}")
    
    def _start_sumo(self):
        """Avvia la simulazione SUMO con parametri dinamici."""
        binary = "sumo-gui" if config.SUMO_GUI else "sumo"
        sumo_binary = sumolib.checkBinary(binary)
        
        cmd = [
            sumo_binary,
            "-c", SUMO_CFG,
            "--step-length", str(SUMO_STEP_LENGTH),
            "--seed", str(config.SUMO_SEED) # Usa il seed aggiornato
        ]

        # --- MODIFICA QUI: Gestione Automatica GUI ---
        if config.SUMO_GUI:
            cmd.extend([
                "--start",       # Premi "Play" automaticamente
                "--quit-on-end"  # Chiudi la finestra alla fine
            ])
        
        # --- OVERRIDE FILE ROTTE ---
        if self.route_override:
            cmd.extend(["--route-files", self.route_override])
            logger.info(f"Override Rotte: {self.route_override}")
        
        # Aggiunge argomenti statistiche (aggiornati nel main)
        cmd.extend(config.get_sumo_output_args())
        
        traci.start(cmd)
        logger.info(f"SUMO avviato - Mode: {config.SIMULATION_MODE} - Seed: {config.SUMO_SEED}")
    
    def _initialize_rsus(self):
        for rsu_id, cfg in RSU_CONFIG.items():
            try:
                rsu = RSU(rsu_id, cfg["position"], broadcast_interval=cfg.get("broadcast_interval", 1.0), enabled_messages=cfg.get("enabled_messages", ["cam"]))
                self.rsus[rsu_id] = rsu
            except Exception as e:
                logger.error(f"Errore RSU {rsu_id}: {e}")
    
    def _initialize_triggers(self):
        for msg_type in MessageFactory.get_available_types():
            trigger = TriggerRegistry.get(msg_type)
            if trigger: self.triggers[msg_type] = trigger
    
    def run(self):
        self._running = True
        try:
            while self._running and traci.simulation.getMinExpectedNumber() > 0:
                self._process_incoming_messages()
                traci.simulationStep()
                
                sim_time = traci.simulation.getTime()
                gen_delta_time = get_generation_delta_time(sim_time)
                
                self._process_rsus(sim_time, gen_delta_time)
                self._process_vehicles(sim_time, gen_delta_time)
                self._cleanup_vehicles()

                # --- MODIFICA QUI: GESTIONE VELOCITÀ ---
                if config.SUMO_GUI:
                    # Se c'è la grafica, rallenta per simulare il tempo reale (0.1s = 100ms)
                    # Questo permette anche a Vanetza di "stare al passo"
                    time.sleep(0.01) 
                else:
                    # Se siamo in batch (senza grafica), vai alla massima velocità possibile
                    time.sleep(0.01)    # se minore, il container di vanetza_nap, esclude un elemento dello scenario, obu's, rsu's(randomicamente)

        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def _process_incoming_messages(self):
        while self._incoming_mcm_queue:
            payload = self._incoming_mcm_queue.pop(0)
            basic = payload.get("basicContainer", {})
            mcm_type = basic.get("mcmType")
            
            if mcm_type == 1: self._dispatch_mcm_request(payload)
            elif mcm_type == 4: self._dispatch_mcm_termination(payload)

    def _dispatch_mcm_termination(self, payload):
        for vehicle_obj in self.vehicles.values():
            if vehicle_obj.managed_by_python:
                vehicle_obj.handle_mcm_termination(payload)

    def _dispatch_mcm_request(self, payload):
        container = payload.get("mcmContainer", {}).get("advisedManoeuvreContainer", [])
        target_ids = [item["executantID"] for item in container if "executantID" in item]
        if not target_ids: return

        for vehicle_obj in self.vehicles.values():
            if vehicle_obj.station_id in target_ids:
                vehicle_obj.handle_mcm_request(payload)
    
    def _process_rsus(self, sim_time: float, gen_delta_time: int):
        # Snapshot semplificato per performance
        world_vehicles = []
        for v in self.vehicles.values():
            snap = v.get_state_snapshot()
            snap.update({"id": v.sumo_id, "station_id": v.station_id, "light_left_turn": v._light_left_turn, "light_right_turn": v._light_right_turn})
            world_vehicles.append(snap)

        for rsu in self.rsus.values():
            for msg_type in rsu.enabled_messages:
                should_send = False
                if msg_type == "cam":
                    should_send = rsu.should_send_message(msg_type, sim_time)
                elif msg_type in self.triggers:
                    should_send = self._evaluate_rsu_trigger(rsu, msg_type, sim_time, world_vehicles)

                if should_send:
                    self._send_message(rsu, msg_type, gen_delta_time)
                    rsu.mark_message_sent(msg_type, sim_time)
    
    def _evaluate_rsu_trigger(self, rsu, msg_type, sim_time, world_vehicles):
        trigger = self.triggers.get(msg_type)
        if not trigger: return False

        rsu_neighbors = []
        for v in world_vehicles:
            dist = euclidean_distance(rsu._x, rsu._y, v["x"], v["y"])
            if dist <= 100: # Ottimizzazione: passa solo veicoli vicini
                v_copy = v.copy()
                v_copy["distance_to_rsu"] = dist
                rsu_neighbors.append(v_copy)

        current_state = rsu.get_state_snapshot()
        current_state["neighbors"] = rsu_neighbors
        
        key = f"rsu_{rsu.station_id}"
        if key not in self.vehicle_trigger_states: self.vehicle_trigger_states[key] = {}
        prev_state = self.vehicle_trigger_states[key].get(msg_type)

        result = trigger.evaluate(str(rsu.station_id), sim_time, current_state, prev_state)

        if result.new_state: self.vehicle_trigger_states[key][msg_type] = result.new_state
        if result.should_send:
            if result.new_state and "current_targets" in result.new_state:
                rsu.set_mcm_targets(result.new_state["current_targets"])
            return True
        return False
    
    def _process_vehicles(self, sim_time, gen_delta_time):
        for veh_id in traci.vehicle.getIDList():
            if veh_id not in self.vehicles: self._register_vehicle(veh_id)
            v = self.vehicles[veh_id]
            x, y = traci.vehicle.getPosition(veh_id)
            v.update(sim_time, x=x, y=y, speed=traci.vehicle.getSpeed(veh_id), heading=traci.vehicle.getAngle(veh_id), acceleration=traci.vehicle.getAcceleration(veh_id), light_left_turn=(traci.vehicle.getSignals(veh_id) & 2) != 0, light_right_turn=(traci.vehicle.getSignals(veh_id) & 1) != 0)
            
            for msg in v.enabled_messages:
                self._evaluate_and_send(v, msg, sim_time, gen_delta_time)
    
    def _register_vehicle(self, sumo_id):
        v = Vehicle.from_sumo(sumo_id)
        self.vehicles[sumo_id] = v
        self.vehicle_trigger_states[sumo_id] = {}
    
    def _evaluate_and_send(self, vehicle, msg_type, sim_time, gen_delta_time):
        trigger = self.triggers.get(msg_type)
        if not trigger: return
        
        prev = self.vehicle_trigger_states.get(vehicle.sumo_id, {}).get(msg_type)
        res = trigger.evaluate(vehicle.sumo_id, sim_time, vehicle.get_state_snapshot(), prev)
        
        if res.should_send:
            self._send_message(vehicle, msg_type, gen_delta_time)
            if res.new_state: self.vehicle_trigger_states[vehicle.sumo_id][msg_type] = res.new_state
    
    def _send_message(self, entity, msg_type, gen_delta_time):
        msg = MessageFactory.create(msg_type, gen_delta_time)
        if msg: 
            payload = msg.build_payload(entity.get_message_data(msg_type))
            # record CAM send timestamp
            if msg_type == "cam":
                network_stats.record_cam_sent(entity.station_id)

            mqtt_manager.publish(entity.station_id, msg_type, payload)
    
    def _cleanup_vehicles(self):
        active = set(traci.vehicle.getIDList())
        for vid in list(self.vehicles.keys()):
            if vid not in active:
                del self.vehicles[vid]
                if vid in self.vehicle_trigger_states: del self.vehicle_trigger_states[vid]
    
    def shutdown(self):
        self._running = False
        try: traci.close()
        except: pass
        mqtt_manager.close_all()
        # Print MCM delay statistics
        network_stats.print_summary()
def main():
    print("=" * 60)
    print("V2X Simulator - Batch Mode")
    print("=" * 60)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, help="Override Seed")
    parser.add_argument("--route-file", type=str, help="Override file rotte")
    parser.add_argument("--mode", type=str, choices=["BASELINE", "V2X"], help="Override Mode")
    parser.add_argument("--prefix", type=str, default="run", help="Prefisso output")
    parser.add_argument("--nogui", action="store_true", help="Disabilita la GUI di SUMO per esecuzione veloce")
    args = parser.parse_args()

    # 1. Override Configurazione
    if args.seed is not None: config.SUMO_SEED = args.seed
    if args.mode is not None: config.SIMULATION_MODE = args.mode

    if args.nogui:
        config.SUMO_GUI = False  # Forza l'uso di "sumo" (console) invece di "sumo-gui"

    # 2. Patch Output
    def get_dynamic_output_args():
        return [
            "--statistic-output", f"{args.prefix}_stats.xml",
            "--tripinfo-output", f"{args.prefix}_tripinfo.xml",
            "--duration-log.statistics", "true",
            "--no-step-log", "true"
        ]
    config.get_sumo_output_args = get_dynamic_output_args

    # 3. Avvio
    sim = V2XSimulator(route_override=args.route_file)
    try:
        sim.initialize()
        sim.run()
    except Exception as e:
        logger.error(f"Errore: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
