import abc
import json
import logging
import os
import asyncio
from datetime import datetime

# Configuració de logs obligatòria [cite: 214]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BaseAgent")

class BaseAgent(abc.ABC):
    # CORRECCIÓ: Afegim 'input_queue' als arguments del constructor
    def __init__(self, agent_id, mc_connection, message_bus, input_queue):
        self.agent_id = agent_id
        self.mc = mc_connection
        self.bus = message_bus
        self.input_queue = input_queue  # Necessari per rebre missatges asíncrons
        self.state = "IDLE"  # Estat inicial [cite: 107]
        self.inventory = {}
        
        # Intentem carregar un estat previ en iniciar [cite: 124]
        self.load_checkpoint()

    def transition_to(self, next_state):
        """Gestiona els canvis d'estat de forma segura i loguejada [cite: 121, 125]"""
        old_state = self.state
        self.state = next_state
        logger.info(f"TRANSITION: {self.agent_id} from {old_state} to {next_state}")
        
        # Si l'agent s'atura o falla, alliberem els locks (ex: zones de mineria) 
        if next_state in ["STOPPED", "ERROR"]:
            self.bus.release_locks(self.agent_id)
            
        # Guardem l'estat en cada transició important per a la recuperació [cite: 124, 126]
        self.save_checkpoint()

    @abc.abstractmethod
    async def perceive(self):
        """Cicle de percepció: llegir l'entorn o missatges [cite: 30]"""
        pass

    @abc.abstractmethod
    def decide(self):
        """Cicle de decisió: processar dades i triar acció [cite: 30]"""
        pass

    @abc.abstractmethod
    async def act(self):
        """Cicle d'acció: execució física en Minecraft [cite: 30]"""
        pass

    async def run(self):
        """Bucle millorat integrant idees del teu company."""
        while self.state != "STOPPED":
            # 1. Esperem un missatge de la cua (sempre, encara que estiguem IDLE)
            # Això evita el problema de quedar-se bloquejat en IDLE
            try:
                # Fem un timeout petit per poder gestionar canvis d'estat
                message = await asyncio.wait_for(self.input_queue.get(), timeout=1.0)
                if message:
                    await self.perceive(message) # Passa el missatge al perceive!
            except asyncio.TimeoutError:
                pass

            # 2. Només si estem actius, executem la lògica física
            if self.state == "RUNNING":
                self.decide()
                await self.act()
                
            await asyncio.sleep(0.1)
    
    async def send_message(self, target, msg_type, payload, status="SUCCESS", context=None):
        """Envia missatges seguint l'esquema JSON estàndard [cite: 35, 37]"""
        message = {
            "type": msg_type,
            "source": self.agent_id,
            "target": target,
            "timestamp": datetime.utcnow().isoformat() + "Z", 
            "payload": payload,
            "status": status,
            "context": context or {"state": self.state} 
        }
        await self.bus.publish(message) 
        logger.info(f"SENT [{msg_type}]: {self.agent_id} -> {target}")

    def handle_control(self, command):
        if command == "pause":
            self.transition_to("PAUSED") 
        elif command == "resume":
            self.transition_to("RUNNING")
        elif command == "stop":
            self.transition_to("STOPPED") 


    def save_checkpoint(self):
        """Guarda l'estat actual de l'agent en un fitxer JSON."""
        checkpoint_data = {
            "agent_id": self.agent_id,
            "state": self.state,
            "inventory": self.inventory,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        os.makedirs('checkpoints', exist_ok=True)
        filename = f"checkpoints/{self.agent_id}.json"
        with open(filename, 'w') as f:
            json.dump(checkpoint_data, f, indent=4)
        logger.debug(f"Checkpoint guardat: {filename}")

    def load_checkpoint(self):
        path = f"checkpoints/{self.agent_id}.json"
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                # Forcem l'estat IDLE per evitar que el bot estigui "mort" d'entrada
                self.state = "IDLE" 
                self.inventory = data.get("inventory", {})
                logger.info(f"Estat restaurat (IDLE) per a {self.agent_id}")