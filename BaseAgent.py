from enum import Enum
from mcpi import minecraft # Aquesta importació és correcta
import asyncio
from abc import ABC, abstractmethod
import logging 

# --- CORRECCIÓ CLAU 1: Importació de la classe Minecraft ---
# Per utilitzar 'Minecraft' com a tipus, cal importar-la directament.
# Amb 'from mcpi import minecraft', el nom de la classe és 'minecraft.Minecraft'.
from mcpi.minecraft import Minecraft 
# --------------------------------------------------------

# El logging no estava inicialitzat al codi proporcionat
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- 1. Definició d'Estats (Correcte) ---
class State(Enum):
    IDLE = 'IDLE'
    RUNNING = 'RUNNING'
    PAUSED = 'PAUSED'
    WAITING = 'WAITING' 
    STOPPED = 'STOPPED'
    ERROR = 'ERROR'

# Aquesta classe ha d'estar definida al teu projecte (src/core/message_bus.py)
class MessageBus: 
    def publish(self, message):
        pass 
    async def receive(self, agent_id):
        return {} 

# --- 2. Correcció del Constructor i la Capçalera ---
class BaseAgent(ABC): # L'ABC va a la definició de la classe
    
    # CORRECCIÓ CLAU 2: La classe base només s'ha de definir UNA vegada
    # CORRECCIÓ CLAU 3: El type hint no ha de cridar la funció .create()
    def __init__(self, agent_id: str, message_bus: MessageBus, input_queue: asyncio.Queue, mc_connection: Minecraft): 
        
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.input_queue = input_queue
        
        # Guardar la connexió per a ús futur a perceive/act
        self.mc = mc_connection  
        self.logger = logging.getLogger(self.agent_id)
        self._state = State.IDLE
        self.context = {} 
        
        self.logger.info(f"Agent '{self.agent_id}' inicialitzat.")


    @property
    def state(self) -> State:
        return self._state
    

    # --- 3. Mètode de Canvi d'Estat (Protegit) ---
    def _set_state(self, new_state: State, reason: str=""):
        if new_state != self.state:
            prev_state = self._state
            self._state = new_state
            
            # Registre de la transició (Requisit del projecte) [cite: 121, 125]
            self.logger.info(f"TRANSITION | {prev_state.value} -> {new_state.value} | Reason: {reason}")
            
            if new_state in (State.STOPPED, State.ERROR):
                self._release_locks() # [cite: 122]
            
            # NOTIFICAR a dependients (Requisit del projecte) 
            # Aquí aniria la lògica per enviar un missatge de notificació de canvi d'estat
            if self.message_bus:
                 # Ejemplo de notificación (necesita un schema de mensaje definido)
                 self.message_bus.publish({
                     "type": "state.update.v1", 
                     "source": self.agent_id,
                     "payload": {"new_state": new_state.value}
                 })


    def _release_locks(self):
        self.logger.debug("Locks alliberats")
        # Alliberar regions (MinerBot) [cite: 148]
        pass 
        

    # --- 4. Cicle Principal Asíncron (`run`) ---
    async def run(self):
        self._set_state(State.IDLE, "Iniciant bucle")
        self.logger.info("Bucle de l'agent iniciat.")
        while self.state != State.STOPPED and self.state != State.ERROR:
            try:
                await self._handle_incoming_messages()
                
                if self.state == State.RUNNING:
                    await self.perceive()
                    await self.decide()
                    await self.act()
                elif self.state == State.WAITING:
                    self.logger.debug("En mode WAITING, esperant missatges.")
                    await asyncio.sleep(0.5) 
                
                await asyncio.sleep(0.1) 
            
            except NotImplementedError:
                self._set_state(State.ERROR, "Mètode P/D/A no implementat.")
            except Exception as e:
                self._set_state(State.ERROR, f"Error crític: {e}")


    # --- 5. Implementació de P/D/A (Abstractes) ---
    @abstractmethod 
    async def perceive(self):
        pass

    @abstractmethod
    async def decide(self):
        pass

    @abstractmethod
    async def act(self):
        pass


    # --- 6. Maneig de Missatges Entrants (Crucial) ---
    async def _handle_incoming_messages(self):
        # Intentem obtenir un missatge de la nostra cua sense bloquejar-nos
        try:
            message = self.input_queue.get_nowait()
        except asyncio.QueueEmpty:
            return 

        # Aquí hauria d'anar la VALIDACIÓ JSON [cite: 36]
        
        msg_type = message.get("type", "")
        
        if msg_type.startswith("command."):
            await self._process_control_command(message)
    
        else:
            self.logger.info(f"Dades rebudes: {msg_type}")
            self.context['latest_message'] = message 
            

    # --- 7. Mètodes de Control (Asíncrons i amb Validació de FSM) ---
    async def _process_control_command(self, message):
        command = message.get("type").split('.')[1] # p. ex., 'start', 'pause'

        if command == "start" and self.state == State.IDLE:
            self._set_state(State.RUNNING, "Comanda de START rebuda.")
        
        elif command == "pause" and self.state == State.RUNNING:
            await self._save_checkpoint() # Requisit: context preserved [cite: 109, 124]
            self._set_state(State.PAUSED, "Comanda de PAUSE rebuda.")

        elif command == "resume" and self.state == State.PAUSED:
            await self._load_checkpoint() 
            self._set_state(State.RUNNING, "Comanda de RESUME rebuda.")
        
        elif command == "stop":
            self._set_state(State.STOPPED, "Comanda de STOP rebuda.") # Requisit: terminated safely [cite: 117]
        
        elif command == "update":
            # Si el BuilderBot rep un update, ha de reconfigurar-se [cite: 102, 118]
            self.logger.info(f"Comanda UPDATE rebuda. Dades: {message.get('payload')}")
            # El teu codi aquí per processar canvis de coordenades, estratègia o pla.
        
        else:
            self.logger.warning(f"Comanda '{command}' rebutjada o invàlida a l'estat {self.state.value}.")

    # Mètodes auxiliars (placeholder)
    async def _save_checkpoint(self):
        # Implementar serialització (JSON o pickle) 
        self.logger.debug("Guardant checkpoint...")
        pass

    async def _load_checkpoint(self):
        self.logger.debug("Carregant checkpoint...")
        pass