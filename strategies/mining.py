from BaseAgent import BaseAgent, State
import asyncio
import mcpi.block as block
import json

# --- Dependències del MinerBot ---

# Patró Strategy: Defineix una interfície per a totes les estratègies
class MiningStrategy(object):
    """Interfície base per a les estratègies de mineria."""
    def __init__(self, agent_id, mc, logger):
        self.agent_id = agent_id
        self.mc = mc
        self.logger = logger
    
    # El mètode abstracte de cada estratègia (ha de ser asíncron)
    async def mine(self, inventory, requirements):
        raise NotImplementedError("El mètode 'mine' ha de ser implementat per l'estratègia.")
    
# Importació simulada de les estratègies (Patró Strategy + Reflexió)
# NOTA: En el teu projecte final, AQUESTA PART S'HA DE FER AMB REFLEXIÓ DINÀMICA!
STRATEGIES = {
    'vertical': None,  # Mapeig de noms de comanda a les classes
    'grid': None
}

class MinerBot(BaseAgent):
    
    def __init__(self, agent_id: str, message_bus, input_queue: asyncio.Queue, mc_connection):
        super().__init__(agent_id, message_bus, input_queue, mc_connection)
        
        self.inventory = {}              # Inventari actual de recursos recollits
        self.requirements = {}           # Bill of Materials (BOM) del BuilderBot
        self.current_strategy = 'grid'   # Estratègia activa per defecte
        self.mining_lock = asyncio.Lock() # Lock per regions espacials (evitar solapament)
        
        # Inicialitzar les classes d'estratègia un cop es defineixin (es pot fer de manera lazy)
        # self.strategy_executor = self._load_strategy(self.current_strategy) 
        self.strategy_executor = GridSearch(self.agent_id, self.mc, self.logger) 


    # --- Mètode Auxiliar per a Estratègia (Usat per /miner set strategy) ---
    def _load_strategy(self, strategy_name):
        # NOTA: Aquesta lògica es la que s'ha de fer amb la Programació Reflectiva
        if strategy_name not in STRATEGIES:
            self.logger.error(f"Estratègia '{strategy_name}' desconeguda.")
            return None
        
        # Simula la instanciació de l'estratègia carregada
        # strategy_class = STRATEGIES[strategy_name] 
        # return strategy_class(self.agent_id, self.mc, self.logger)
        pass # Per ara, ho gestionarem amb un if/else a act()


    # --- 1. PERCEIVE: Recepció de Dades ---
    async def perceive(self):
        # 1. Comprova si hi ha missatges de la cua de BaseAgent
        message = self.context.get('latest_message')
        
        if message and message['type'] == 'materials.requirements.v1':
            # Nou BOM rebut del BuilderBot
            self.requirements = message['payload']
            self.logger.info(f"BOM rebut. Necessari: {self.requirements}")
            
            # Valida l'inventari i comença a minar si cal
            if not self._is_fulfillment_complete():
                self._set_state(State.RUNNING, "Requisits rebuts, iniciant mineria.")
            
            # Neteja el missatge processat
            self.context['latest_message'] = None


    # --- 2. DECIDE: Lògica de l'Agent ---
    async def decide(self):
        if self.state == State.RUNNING:
            if self._is_fulfillment_complete():
                self._set_state(State.IDLE, "Requisits complerts, aturant mineria.")
                # Notificar al BuilderBot que ja tenim tot el material
                await self._publish_inventory(status="COMPLETED")
                return
            
            # En una implementació real, aquí es decidiria la propera regió a minar
            self.logger.debug(f"Decisió: Continuar minant amb estratègia {self.current_strategy}.")


    # --- 3. ACT: Execució de la Mineria ---
    async def act(self):
        if self.state == State.RUNNING:
            
            # 3.1. Adquirir el Lock per a la regió (simulació)
            # En la realitat, es bloquejaria una regió (x, z) específica
            async with self.mining_lock: 
                self.logger.debug(f"LOCK adquirit per a la mineria.")
                
                # 3.2. Executar l'estratègia escollida (Patró Strategy)
                self.logger.info(f"Executant mineria amb {self.current_strategy}...")
                
                # Aquí utilitzaries self.strategy_executor.mine(self.inventory, self.requirements)
                
                # ************ SIMULACIÓ D'ACCIÓ REAL DE MINERIA ************
                
                # Incrementa un recurs simulat (ej: pedra)
                material_mined = 'stone'
                if material_mined in self.requirements:
                    
                    # Simulem que minem 1 bloc
                    if self.inventory.get(material_mined, 0) < self.requirements[material_mined]:
                         self.inventory[material_mined] = self.inventory.get(material_mined, 0) + 1 
                         self.logger.info(f"Minat 1x {material_mined}. Total: {self.inventory[material_mined]}")
                    
                    # Simulem la interacció amb Minecraft
                    # self.mc.setBlock(self.mc.player.getPos().x, self.mc.player.getPos().y -1, self.mc.player.getPos().z, block.AIR.id)
                
                # Pausa per simular el temps de mineria (asyncio.sleep)
                await asyncio.sleep(0.5) 
                
                # 3.3. Publicar l'estat de l'inventari (Requisit inventory.v1)
                await self._publish_inventory(status="RUNNING")
            
            self.logger.debug(f"LOCK alliberat.")


    # --- 4. Mètodes de Suport ---

    def _is_fulfillment_complete(self):
        """Comprova si l'inventari satisfà els requisits del BOM."""
        for material, required_count in self.requirements.items():
            if self.inventory.get(material, 0) < required_count:
                return False
        return True

    async def _publish_inventory(self, status: str):
        """Publica el missatge inventory.v1 al BuilderBot[cite: 94]."""
        inventory_message = {
            "type": "inventory.v1",
            "source": self.agent_id,
            "target": "BuilderBot", # Hauria de ser l'ID del BuilderBot que va demanar el BOM
            "timestamp": "2025-10-21T15:30:00Z", # Cal generar l'hora ISO 8601
            "payload": self.inventory,
            "status": status,
            "context": {"task_id": "MNR-001"}
        }
        await self.message_bus.publish(inventory_message)

    def _release_locks(self):
        """Allibera tots els locks espacials (Requisit del projecte)[cite: 122, 148]."""
        if self.mining_lock.locked():
            # Aquesta línia només es pot cridar si s'és l'amo del lock
            # self.mining_lock.release() # No fer-ho així directament fora del 'async with'
            self.logger.warning("LOCK forçat a alliberar-se durant STOPPED/ERROR.")
        super()._release_locks()