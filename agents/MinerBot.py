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
        # Registre dinàmic d'estratègies
        self.strategies = self._discover_strategies()
        self.current_strategy = self.strategies.get("VerticalMining")
        self.inventory = {}
        self.target_bom = {}
        # Coordenades de treball fixes per no dependre de la posició del jugador
        self.mine_x, self.mine_y, self.mine_z = 0, 0, 0
        self.state = "IDLE" 

    def _discover_strategies(self):
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

        if "command.stop" in m_type: 
            self.transition_to("STOPPED")
        
        # Comando: Iniciar minado des de posició actual
        elif "command.start" in m_type:
            self.target_bom = {"stone": 64}
            logger.info(f"MinerBot: Iniciant minat des de la posició actual.")
            self.transition_to("RUNNING")
        
        # Cooperació: Rebre requeriments del BuilderBot
        elif "materials.requirements" in m_type:
            self.target_bom = payload
            self.mine_x = payload.get("x", 120)
            self.mine_y = payload.get("y", 60)
            self.mine_z = payload.get("z", 120)
            logger.info(f"MinerBot: Rebut objectiu a ({self.mine_x}, {self.mine_z}).")
            self.transition_to("RUNNING")

    def decide(self):
        """IMPLEMENTACIÓ OBLIGATÒRIA."""
        if self.state == "RUNNING" and not self.target_bom:
            logger.info("MinerBot: No hi ha més requeriments. Tornant a IDLE.")
            self.transition_to("IDLE")

    # ERROR CORREGIT: El mètode 'act' ara està DINS de la classe (indentat)
    async def act(self):
        if self.state == "RUNNING" and self.current_strategy:
            # Executa el minat (omple bot.inventory["stone"] amb una llista)
            result = self.current_strategy.execute(self.mc, self)
            
            # Objectiu i recompte real
            pedra_objectiu = self.target_bom.get("stone", 30)
            inventari_pedra = self.inventory.get("stone", [])
            pedra_actual = len(inventari_pedra) if isinstance(inventari_pedra, list) else 0
            
            logger.info(f"MinerBot: Estat de minat {pedra_actual}/{pedra_objectiu}")
            
            if pedra_actual >= pedra_objectiu:
                logger.info("MinerBot: Objectiu assolit. Notificant BuilderBot...")
                await self.send_message(
                    target="BuilderBot-1",
                    msg_type="mining.complete.v1",
                    payload={"stone": pedra_actual}
                )
                self.target_bom = {}
                self.transition_to("IDLE")
            else:
                # Enviem l'inventari actualitzat mentre minem
                await self.send_message(
                    target="BuilderBot-1",
                    msg_type="inventory.v1",
                    payload=self.inventory
                )
                
            await asyncio.sleep(0.5)