import logging
from agents.BaseAgent import BaseAgent

# Configuració del logger per a aquest agent
logger = logging.getLogger("ExplorerBot")

class ExplorerBot(BaseAgent):
    def __init__(self, agent_id, mc_connection, message_bus, input_queue):
        super().__init__(agent_id, mc_connection, message_bus, input_queue)
        # Variables per emmagatzemar la missió actual
        self.target_x = 0
        self.target_y = 0 # Altura afegida
        self.target_z = 0
        self.scan_range = 10

    async def perceive(self, message):
        """
        Rep els missatges de la cua asíncrona.
        Escolta ordres de l'usuari (command.start.v1).
        """
        msg_type = message.get("type")
        payload = message.get("payload", {})

        if msg_type == "command.start.v1":
            logger.info(f"{self.agent_id} | Ordre de xat rebuda: {payload}")
            
            # Extreure coordenades X, Y, Z del xat
            self.target_x = payload.get('x', 0)
            self.target_y = payload.get('y', 63) # Nivell del mar per defecte
            self.target_z = payload.get('z', 0)
            self.scan_range = payload.get('range', 10)
            
            # Canvi d'estat a RUNNING per iniciar act()
            self.transition_to("RUNNING")

    def decide(self):
        """
        Cicle de decisió.
        """
        pass

    async def act(self):
        """
        Executa l'escaneig i envia el mapa al BuilderBot.
        """
        if self.state == "RUNNING":
            logger.info(f"{self.agent_id} | Iniciant anàlisi a X:{self.target_x} Y:{self.target_y} Z:{self.target_z}")
            
            # Executem l'anàlisi de terreny asíncron fent servir la Y
            await self.analyze_terrain(self.target_x, self.target_y, self.target_z, self.scan_range)
            
            # Un cop enviat el mapa, tornem a IDLE
            self.transition_to("IDLE")

    async def analyze_terrain(self, x_start, y_start, z_start, size):
        """
        Analitza el terreny usant programació funcional i envia map.v1.
        """
        # 1. Generem la rejilla de coordenades (x, z) 
        grid = [(x, z) for x in range(x_start, x_start + size) 
                        for z in range(z_start, z_start + size)]
        
        # 2. Obtenim les altures amb map, però ara guardem també la referència Y
        terrain_data = list(map(lambda pos: {
            'x': pos[0], 
            'z': pos[1], 
            'y': self.mc.getHeight(pos[0], pos[1])
        }, grid))
        
        # 3. Filtrem zones segures o d'interès respecte a la Y demanada
        dry_land = list(filter(lambda tile: tile['y'] >= y_start, terrain_data))
        
        # 4. Calculem l'altura mitjana de la zona filtrada
        avg_height = sum(t['y'] for t in dry_land) / len(dry_land) if dry_land else y_start
        
        # 5. Enviem el missatge al BuilderBot-1
        await self.send_message("BuilderBot-1", "map.v1", {
            "center": {"x": x_start, "y": y_start, "z": z_start},
            "size": size,
            "avg_height": avg_height,
            "data": dry_land
        })
        logger.info(f"{self.agent_id} | Mapa complet enviat a BuilderBot-1")