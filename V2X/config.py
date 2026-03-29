"""
Configurazione centralizzata del simulatore V2X.
Modifica questo file per aggiungere veicoli, RSU o cambiare parametri.
"""

# -----------------------------------------------------------
# SUMO Configuration
# -----------------------------------------------------------
SUMO_CFG = "camMap.sumo.cfg"
SUMO_STEP_LENGTH = 0.1  # 100ms - ideale per V2X 10Hz
SUMO_GUI = True  # True per sumo-gui, False per sumo (headless)
SUMO_SEED = 0  # Seed per la riproducibilità (es. posizioni iniziali, traffico)

# -----------------------------------------------------------
# MQTT Configuration
# -----------------------------------------------------------
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

# Topic per tipo di messaggio
MQTT_TOPICS = {
    "cam": "vanetza/in/cam_full",
    "mcm": "vanetza/in/mcm",  # Placeholder per MCM
    "mcm_request": "vanetza/in/mcm",
    "mcm_response": "vanetza/in/mcm",
    "mcm_termination": "vanetza/in/mcm",
    "denm": "vanetza/in/denm",  # Placeholder per DENM
}

# -----------------------------------------------------------
# Station Mapping (StationID -> IP Docker container)
# -----------------------------------------------------------
# Aggiungi qui nuovi veicoli/RSU con il loro ID e IP
STATIONS = {
    0: {
        "ip": "192.168.98.10",
        "type": "rsu",
        "name": "RSU_Central",
    },
    1: {
        "ip": "192.168.98.20",
        "type": "obu",
        "name": "OBU_1",
    },
    2: {
        "ip": "192.168.98.30",
        "type": "obu",
        "name": "OBU_2",
    },
    # Aggiungi altri veicoli qui:
    # 3: {
    #     "ip": "192.168.98.40",
    #     "type": "obu",
    #     "name": "OBU_3",
    # },
}

# -----------------------------------------------------------
# RSU Configuration
# -----------------------------------------------------------
RSU_CONFIG = {
    0: {
        "position": (500.00, 1500.00),  # Coordinate SUMO (x, y)
        "broadcast_interval": 1.0,  # Secondi (1 Hz)
        "enabled_messages": ["cam", "mcm_request", "mcm_termination"],  # Tipi di messaggio abilitati
    },
    # Aggiungi altre RSU qui:
    # 10: {
    #     "position": (200.00, 400.00),
    #     "broadcast_interval": 1.0,
    #     "enabled_messages": ["cam", "denm"],
    # },
}

# -----------------------------------------------------------
# Vehicle (OBU) Default Configuration
# -----------------------------------------------------------
VEHICLE_DEFAULTS = {
    "length": 8,  # metri
    "width": 2,  # metri
    "station_type": 5,  # 5 = Passenger Car (ETSI)
    "enabled_messages": ["cam", "mcm_response"],  # Tipi di messaggio abilitati
}

# -----------------------------------------------------------
# ETSI CAM Trigger Parameters (EN 302 637-2)
# -----------------------------------------------------------
CAM_TRIGGER_CONFIG = {
    "t_gen_cam_min": 0.1,  # 100ms - intervallo minimo
    "t_gen_cam_max": 1.0,  # 1000ms - intervallo massimo
    "n_gen_cam_default": 3,  # Numero messaggi a freq. elevata dopo trigger
    "delta_pos_threshold": 4.0,  # metri
    "delta_speed_threshold": 0.5,  # m/s
    "delta_heading_threshold": 4.0,  # gradi
}

# -----------------------------------------------------------
# MCM Configuration (Placeholder)
# -----------------------------------------------------------
MCM_CONFIG = {
    "enabled": False,
    "broadcast_interval": 0.1,  # 100ms
    # Aggiungi altri parametri MCM qui
}

# Struttura: { ENTITY_TYPE: { "protocol_prefix": station_id } }
# McmStationType: vruPortableDevice (0), vehicle (1), roadsideUnit (2), centralStation (3)
# CamStationType: DA AGGIUNGERE
STATION_TYPE_RULES = {
    "RSU": {
        "cam": 15,  # ETSI RSU
        "mcm": 2    # ETSI MCM RSU (qualsiasi mcm_*)
    },
    "VEHICLE": {
        "cam": 5,   # ETSI Passenger Car
        "mcm": 1    # ETSI MCM Vehicle/OBU (qualsiasi mcm_*)
    }
}

# -----------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------
LOGGING = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "show_cam_sends": False,  # Mostra ogni invio CAM
    "show_trigger_details": True,  # Mostra dettagli trigger
}

# -----------------------------------------------------------
# Simulation Mode & Statistics
# -----------------------------------------------------------
# Modalità disponibili: "BASELINE" (Solo SUMO), "V2X" (Con RSU e Python)
#SIMULATION_MODE = "V2X"  # <--- CAMBIA QUESTO PER I TEST
SIMULATION_MODE = "V2X"
# Configurazione Output
OUTPUT_DIR = "results" # Assicurati che questa cartella esista o creala
ENABLE_STATS = True
# -----------------------------------------------------------
# Network Emulation Parameters (Application-Level)
# -----------------------------------------------------------
NETWORK_EMULATION = {
    "enabled": True,
    "fixed_delay_ms": 50,       # constant delay
    "jitter_ms": 5,            # random variation ±
    "packet_loss_prob": 0.3    # % packet loss
}
def get_sumo_output_args():
    """Genera gli argomenti per le statistiche in base alla modalità."""
    if not ENABLE_STATS:
        return []
    
    prefix = f"{OUTPUT_DIR}/{SIMULATION_MODE.lower()}"
    return [
        "--statistic-output", f"{prefix}_stats.xml",
        "--tripinfo-output", f"{prefix}_tripinfo.xml",
        "--duration-log.statistics", "true",
        "--no-step-log", "true"
    ]
