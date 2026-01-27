from agents.BaseAgent import BaseAgent
import asyncio
import logging

logger = logging.getLogger("BuilderBot")

class BuilderBot(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = "IDLE"
        self.current_inventory = {}
        self.required_materials = {}
        self.selected_blueprint = "base_pedra"
        self.build_x, self.build_y, self.build_z = 0, 70, 0
        
        # Plànol de prova
        self.blueprints = {
            "base_pedra": [
                [0, 0, 0, 1], [1, 0, 0, 1], [2, 0, 0, 1],
                [0, 0, 1, 1], [1, 0, 1, 1], [2, 0, 1, 1]
            ],
            "creu": [
                [0, 0, 0, 1], 
                [0, 1, 0, 1], 
                [0, 2, 0, 1],
                # Braços (a l'alçada del segon bloc, y=1)
                [-1, 1, 0, 1], 
                [1, 1, 0, 1],
                [0, 1, -1, 1],
                [0, 1, 1, 1]
            ]
            
        }

    async def perceive(self, message):
        """Processa missatges del bus."""
        msg_type = message.get("type")
        payload = message.get("payload", {}) 

        if msg_type == "command.start.v1":
            # MILLORA 2: Comprovem si l'usuari ha especificat l'estructura
            selected = payload.get("structure")
            
            if not selected:
                self.mc.postToChat(" Has d'especificar: structure=creu o structure=base_pedra")
                return # Atura l'execució si no hi ha tria

            self.selected_blueprint = selected
            
            # Verificació de seguretat
            if self.selected_blueprint not in self.blueprints:
                self.mc.postToChat(f" Error: No conec l'estructura '{self.selected_blueprint}'")
                return

            # MILLORA 1: Calcular la posició "davant" segons la direcció del jugador
            pos = self.mc.player.getTilePos()
            direction = self.mc.player.getDirection()
            
            # Multipliquem la direcció per 3 per posar-ho una mica allunyat
            # Fem servir round() per convertir el vector de direcció a enters de quadrícula
            self.build_x = int(pos.x + (direction.x * 4))
            self.build_y = pos.y
            self.build_z = int(pos.z + (direction.z * 4))
            
            self.mc.postToChat(f" Triat planol: {self.selected_blueprint}")
            await self.generate_bom(None)

        elif msg_type == "map.v1":
            # Aquí mantenim un valor per defecte per si ve de l'Explorer
            center = payload.get("center", {})
            self.selected_blueprint = payload.get("structure", "base_pedra")
            self.build_x, self.build_y, self.build_z = center.get("x"), center.get("y"), center.get("z")
            await self.generate_bom(None)
            
        elif msg_type in ["inventory.v1", "mining.complete.v1"]:
            self.current_inventory = payload
    def decide(self):
        """Mètode obligatori per BaseAgent."""
        if self.state == "WAITING":
            # Comptem la pedra rebuda (pot ser llista o número)
            data = self.current_inventory.get("stone", 0)
            pedra_actual = len(data) if isinstance(data, list) else data
            pedra_necessaria = self.required_materials.get("stone", 0)
            
            if pedra_necessaria > 0 and pedra_actual >= pedra_necessaria:
                logger.info("Materials llestos!")
                self.transition_to("RUNNING")

    async def act(self):
        """Mètode ASÍNCRON obligatori."""
        if self.state == "RUNNING":
            plan = self.blueprints.get(self.selected_blueprint, [])
            for b in plan:
                # Col·loquem el bloc
                self.mc.setBlock(self.build_x + b[0], self.build_y + b[1], self.build_z + b[2], b[3])
                await asyncio.sleep(0.1)
            
            self.mc.postToChat("Construcció acabada!")
            self.transition_to("IDLE")

    async def generate_bom(self, _):
        """Calcula materials i demana al Miner."""
        plan = self.blueprints.get(self.selected_blueprint, [])
        pedra_req = len([b for b in plan if b[3] == 1])
        self.required_materials = {"stone": pedra_req}
        
        payload_miner = {
            "stone": pedra_req,
            "x": self.build_x, "y": self.build_y, "z": self.build_z
        }
        self.transition_to("WAITING")
        await self.send_message("MinerBot-1", "materials.requirements.v1", payload_miner)