import asyncio
import importlib
import pkgutil
import logging
import strategies
from agents.BaseAgent import BaseAgent

logger = logging.getLogger("MinerBot")

class MinerBot(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.strategies = self._discover_strategies()
        self.current_strategy = self.strategies.get("VerticalMining")
        self.inventory = {}
        self.target_bom = {}
        # Afegim coordenades de treball per no dependre del jugador
        self.mine_x, self.mine_y, self.mine_z = 0, 0, 0
        self.state = "IDLE" 

    def _discover_strategies(self):
        """Escaneja el paquet 'strategies' i instancia les classes trobades."""
        found = {}
        for _, name, _ in pkgutil.iter_modules(strategies.__path__):
            module = importlib.import_module(f"strategies.{name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and attr_name not in ["MiningStrategy", "BaseAgent"]:
                    found[attr_name] = attr()
                    logger.info(f"MinerBot: Estratègia '{attr_name}' carregada.")
        return found

    async def perceive(self, message):
        """Processa missatges del Bus de dades."""
        m_type = message.get("type", "")
        payload = message.get("payload", {})

        # 1. Control de l'estat
        if "command.pause" in m_type: self.transition_to("PAUSED")
        elif "command.resume" in m_type: self.transition_to("RUNNING")
        elif "command.stop" in m_type: self.transition_to("STOPPED")
        
        # 2. Configuració dinàmica d'estratègia
        elif "command.set_strategy" in m_type:
            strat_name = payload.get("strategy")
            if strat_name in self.strategies:
                self.current_strategy = self.strategies[strat_name]
                logger.info(f"MinerBot: Estratègia canviada a {strat_name}")

        # 3. Cooperació: Rebre requeriments del BuilderBot
        elif "materials.requirements" in m_type:
            self.target_bom = payload
            # IMPORTANT: Guardem on hem de minar (si no ve al missatge, usem una posició segura)
            self.mine_x = payload.get("x", 120)
            self.mine_y = payload.get("y", 60)
            self.mine_z = payload.get("z", 120)
            
            logger.info(f"MinerBot: Rebuts requeriments i coordenades. Iniciant minat.")
            self.transition_to("RUNNING")

    def decide(self):
        """Decideix si l'objectiu s'ha complert."""
        if self.state == "RUNNING" and not self.target_bom:
            self.transition_to("IDLE")

    async def act(self):
        """Executa l'acció física delegant en l'estratègia."""
        if self.state == "RUNNING" and self.current_strategy:
            # IMPORTANT: Passem l'agent sencer per a que l'estratègia 
            # pugui llegir self.mine_x, self.mine_y, self.mine_z
            result = self.current_strategy.execute(self.mc, self)
            
            # Cada vegada que l'estratègia pica un bloc, hauria d'actualitzar self.inventory
            # Enviem l'estat actual de l'inventari al BuilderBot-1
            await self.send_message(
                target="BuilderBot-1",
                msg_type="inventory.v1",
                payload=self.inventory
            )
            
            # Si l'estratègia ha acabat la seva feina
            if result == "SUCCESS":
                logger.info("MinerBot: Objectiu de minat assolit.")
                # Opcional: self.transition_to("IDLE") si vols que s'aturi al acabar la BOM
            
            await asyncio.sleep(0.5)