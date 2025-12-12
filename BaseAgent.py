from enum import Enum
import asyncio

from abc import ABC, abstractmethod

from mcpi.minecraft import Minecraft, CmdEvents
import mcpi.block as block




class State(Enum):
    #Aqui tenim el que serien els estats en els que pot estar cada agent
    IDLE = 'IDLE'
    RUNNING = 'RUNNING'
    PAUSED = 'PAUSED'
    WAITING = 'WAITING' 
    STOPPED = 'STOPPED'
    ERROR = 'ERROR'



class BaseAgent(ABC):
    #Aquest constructor es per a poguer diferenciar entre un mateix tipus de agent, per si tinc 2 Miners, aixi un es pot dir Miner1 i l'altre Miner2
    
    def __init__(self, agent_id: str): #Dos punts entre agent_id i str ja que el que espera el agent id es un String(str)
        self.agent_id = agent_id
        self._state = State.IDLE
        self.context = {} #De aaquesta manera sabem si entra en el estat de PAUSED en quin punt ens haurem quedat
        self.is_running = True

        pass


    @property
    def state(self) -> State: #es un getter
        return self._state
    

    def _set_state(self, new_state: State, reason: str=""):
        #Nomes procedirem si el estat es nou
        if new_state != self.state:
            prev_state = self._state
            self._state = new_state

            #Mirar
            self.logger.info(f"TRANSITION | {prev_state.value} -> {new_state.value} | Reason: {reason}")
            if new_state in (State.STOPPED, State.ERROR):
                self._release_locks()
    

    def _release_locks(self):
        self.logger.debug("Locks alliberats")
        pass    


    def perceive(self):
        raise NotImplementedError("El mètode perceive() ha de ser implementat per la subclasse.")

    
    def decide(self):
        raise NotImplementedError("El mètode decide() ha de ser implementat per la subclasse.")


    def act(self):
        raise NotImplementedError("El mètode act() ha de ser implementat per la subclasse.")
    
    
    #A partir de aqui el que hem de fer es saber gestionar el nostre agent
    def start(self):
        mc = CmdEvents.pollChatPosts
        #Previament hauria de haberse introduit un missatge al chat del minecraft que es vol que es pari
        self._state = State.RUNNING

    def paused(self):
        #Previament hauria de haberse introduit un missatge al chat del minecraft que es vol que es pari
        self._state = State.PAUSED

    def stop(self):
        #Previament hauria de haberse introduit un missatge al chat del minecraft que es vol que es pari
        self._state = State.STOPPED

    def resume(self):
        if self._state == State.STOPPED:
            #Aqui se hauria de gestionar el que se ha dit despres, pero com es un resume STOPPED -> RUNNING
            self._state = State.RUNNING

    
    

