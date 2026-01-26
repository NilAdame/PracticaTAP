from .MiningStrategy import MiningStrategy

class VerticalMining(MiningStrategy):
    def execute(self, mc, bot):
        # 1. ERROR CORREGIT: No usem la posició del jugador (mc.player)
        # Usem les coordenades de treball que l'agent ha guardat al rebre el missatge
        start_x = bot.mine_x
        start_y = bot.mine_y
        start_z = bot.mine_z
        
        # 2. Simular perforació cap avall en la posició de la mina
        # Minem 3 blocs per sota de l'altura objectiu
        for dy in range(0, 3):
            target_y = start_y - dy
            block_id = mc.getBlock(start_x, target_y, start_z)
            
            if block_id != 0:  # Si no és aire
                # Fem l'acció física al Minecraft
                mc.setBlock(start_x, target_y, start_z, 0)
                
                # Actualitzem inventari de l'agent (això ho llegirà el Builder)
                bot.inventory["stone"] = bot.inventory.get("stone", 0) + 1
        
        # 3. Baixem la coordenada Y de l'agent per a que la propera vegada piqui més avall
        # Així el bot va fent un forat vertical real
        bot.mine_y -= 3
        
        return "SUCCESS"