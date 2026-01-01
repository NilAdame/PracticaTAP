# --- strategies/mining/MiningStrategy.py ---
from abc import ABC, abstractmethod

class MiningStrategy(ABC):
    """
    Interfície abstracta per a totes les estratègies de mineria (Patró Strategy).
    Defineix el contracte: totes han de tenir __init__ i un mètode mine() asíncron.
    """
    def __init__(self, agent_id, mc, logger):
        self.agent_id = agent_id
        self.mc = mc
        self.logger = logger

    @abstractmethod
    async def mine(self, inventory, requirements):
        """Executa la lògica de mineria i retorna l'inventari actualitzat."""
        pass