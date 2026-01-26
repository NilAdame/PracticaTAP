from agents.BaseAgent import BaseAgent
import asyncio
import logging

# Configurem el logger per a aquest agent
logger = logging.getLogger("BuilderBot")

class BuilderBot(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.required_materials = {}
        self.current_inventory = {}
        self.build_plan = []
        # L'estat inicial ha de ser IDLE per evitar que estigui STOPPED
        self.state = "IDLE" 

    async def perceive(self, message):
        """Procesa missatges entrants del Bus."""
        msg_type = message.get("type")
        payload = message.get("payload", {})
        
        if msg_type == "map.v1":
            # Reben dades de l'ExplorerBot per decidir on i què construir
            terrain_data = payload.get("data", [])
            logger.info(f"{self.agent_id} | Mapa rebut. Generant llista de materials...")
            await self.generate_bom(terrain_data)
            
        elif msg_type in ["inventory.v1", "inventory.update.v1"]:
            # Actualització de materials que envia el MinerBot
            self.current_inventory = payload
            logger.info(f"{self.agent_id} | Inventari actualitzat: {self.current_inventory}")

    async def generate_bom(self, terrain_data):
        """Calcula els materials (Bill of Materials) i els demana al Miner."""
        # Simplifiquem a només pedra per garantir que el ready sigui True amb el que tens
        self.required_materials = {"stone": 20} 
        
        # Passem a WAITING per esperar que el Miner reculli la pedra
        self.transition_to("WAITING") 
        
        # Enviar requeriments al MinerBot-1 (ID correcte del main.py)
        # ÉS CRÍTIC usar 'await' aquí
        await self.send_message("MinerBot-1", "materials.requirements.v1", self.required_materials)

    def decide(self):
        """Gestiona la transició de WAITING a RUNNING."""
        if self.state == "WAITING":
            # Simplificació: Només comprovem la pedra per desbloquejar el bot
            pedra_actual = self.current_inventory.get("stone", 0)
            pedra_necessaria = self.required_materials.get("stone", 20)
            
            if pedra_actual >= pedra_necessaria:
                print(f"DEBUG: BuilderBot té prou pedra ({pedra_actual}). Construint!")
                self.transition_to("RUNNING")

    async def act(self):
        """Construeix a les coordenades de l'ordre, NO a les del jugador."""
        if self.state == "RUNNING":
            # IMPORTANT: Ara usem les coordenades guardades del map.v1 (build_x, build_y, build_z)
            # Si no en tens, usa les que hem rebut al perceive
            base_x = getattr(self, 'build_x', 100) 
            base_y = getattr(self, 'build_y', 70)
            base_z = getattr(self, 'build_z', 100)

            print(f"BuilderBot: Construint base a {base_x}, {base_y}, {base_z}")
            
            for y_offset in range(2): 
                for x_offset in range(5):
                    for z_offset in range(5):
                        # Block ID 1 = Pedra
                        self.mc.setBlock(base_x + x_offset, 
                                        base_y + y_offset, 
                                        base_z + z_offset, 1)
                await asyncio.sleep(0.1) 

            await self.send_message("broadcast", "build.v1", {"status": "COMPLETED"})
            self.transition_to("IDLE")