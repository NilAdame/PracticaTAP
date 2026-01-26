from .MiningStrategy import MiningStrategy

class GridMining(MiningStrategy):
    def execute(self, mc, bot):
        # Lògica de Grid Search per a cobertura uniforme 
        pos = mc.player.getTilePos()
        size = 2  # Reixa de 2x2 al voltant
        
        for dx in range(-size, size + 1):
            for dz in range(-size, size + 1):
                # Minem el bloc just a sota de la reixa
                block_id = mc.getBlock(pos.x + dx, pos.y - 1, pos.z + dz)
                if block_id != 0:
                    mc.setBlock(pos.x + dx, pos.y - 1, pos.z + dz, 0)
                    bot.inventory["cobblestone"] = bot.inventory.get("cobblestone", 0) + 1
        
        return "SUCCESS"