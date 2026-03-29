<<<<<<< HEAD
# WorkInProgress_MCM

## Software
- SUMO (Version 1.12.0)
- python3 (Version 3.10.12)
- vanetza-nap (https://github.com/nap-it/vanetza-nap)
- WSL (Version: 2.6.3.0) - Ubuntu-22.04
- Docker (Version 29.2.1)

## Getting Started

### Prerequisites

1. **WSL** (Windows Subsystem for Linux)  
   [Install Guide](https://learn.microsoft.com/en-us/windows/wsl/install)

2. **SUMO** (Simulation of Urban MObility)  
   [Install Guide](https://sumo.dlr.de/docs/Installing/index.html)

3. **Docker + Vanetza-NAP**  
   See the `README.md` file in the `vanetza-nap` repository.
   > **Note:** Currently, please ensure you use the **`main`** branch (not `master`) to ensure compatibility.

### Usage

1. **Clone this repository.**

2. **Configure vanetza-nap:**
   Navigate to your local `vanetza-nap` repository and replace the following files with the versions provided in this repository:
   * Replace `vanetza-nap/docker-compose.yml`  
   * Replace `vanetza-nap/tools/socktap/config.ini`

3. **Start the environment:**
   Go back to the `vanetza-nap` root directory and run:
   ```bash
   docker-compose up
   ```
   
4. **Run a Single Simulation** -> navigate to the V2X folder and run:
   ```bash
   python3 main.py
   ```
   > Note: Edit config.py to:  
   > * Switch SIMULATION_MODE between BASELINE (default SUMO) and V2X (Python interaction).  
   > * Change the seed parameter.
   
5. **Run Multiple Simulations**-> navigate to the V2X folder and run:
   ```bash
   python3 batch_run.py
   ```
   > Note: Inside this file, it is possible to change the random seed and the number of vehicles.

## Project Structure

The Python simulation logic is organized as follows:

```text
v2x_simulator/
├── main.py                  # Entry point of the simulation
├── config.py                # Configuration parameters (Scenario, MQTT, etc.)
├── mqtt_manager.py          # Handles MQTT connection and publishing
├── utils.py                 # Utility functions
├── compare_results.py       # Compare results between BASELINE and V2X genereted in the results folder
├── batch_run.py             # Multiple Simulations with different seed, number of vehicles and BASELINE - V2X
├── analyze_batch.py         # Compare results obtained from batch_run.py
├── camCars.rou.xml          # SUMO files
├── camMap.net.xml
├── camMap.sumo.cfg
|
├── results/
│   ├── baseline_stats.xml
│   ├── baseline_tripinfo.xml
│   ├── v2x_stats.xml
│   └── v2x_tripinfo.xml
│
├── entities/                # Simulation entities
│   ├── __init__.py
│   ├── base.py
│   ├── rsu.py
│   └── vehicle.py
│
├── triggers/                # Logic for triggering messages based on events
│   ├── __init__.py
│   ├── base.py
│   ├── etsi_cam_trigger.py
│   └── mcm_trigger.py
│
└── messages/                # V2X Message definitions and encoding
    ├── __init__.py          # Exposes MessageFactory
    ├── base.py              # Base Message class
    │
    ├── cam/                 # Cooperative Awareness Message (CAM)
    │   ├── __init__.py
    │   └── message.py
    │
    └── mcm/                 # Maneuver Coordination Message (MCM)
        ├── __init__.py
        ├── base.py
        ├── intent.py        # NOT tested, NOT implemented
        ├── request.py
        ├── response.py
        └── termination.py
```
## ToDo
- Implement all MCM messages
- python requirements.txt

## References
- ETSI EN 302 637-2 V1.3.1 (2014-09)
- ETSI TR 103 578 V2.1.1 (2024-04)
- Vanetza-NAP: 
  R. Rosmaninho, A. Figueiredo, P. Almeida, P. Rito, D. Raposo and S. Sargento, *"Vanetza-NAP: Vehicular Communications and Services in MicroServices Architectures,"* 2024 IEEE Vehicular Networking Conference (VNC), Kobe, Japan, 2024, pp. 297-304.  
  [DOI: 10.1109/VNC61989.2024.10575959](https://doi.org/10.1109/VNC61989.2024.10575959)

### Tools & Libraries
* **[Vanetza](https://github.com/nap-it/vanetza-nap)** - The open-source implementation of the ETSI C-ITS protocol suite used in this project.
* **[Eclipse SUMO](https://www.eclipse.org/sumo/)** - Simulation of Urban MObility, used for traffic generation.

### Documentation & Standards
* **[ETSI ITS Standards](https://www.etsi.org/technologies/automotive-intelligent-transportation)** - Standards for Intelligent Transport Systems (V2X).
* **[Docker Documentation](https://docs.docker.com/)** - Reference for container deployment.

=======
# V2X-Simulation
>>>>>>> 2fc18a751e4cb34aa03c55b8187140f791c41947
