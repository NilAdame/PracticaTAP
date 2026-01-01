# --- strategies/mining/VerticalSearch.py ---
# Ara importem la interfície des del mateix subdirectori
from .MiningStrategy import MiningStrategy 
import asyncio
import mcpi.block as block

class VerticalSearch(MiningStrategy):
    """Estratègia de perforació vertical (Vertical Search)[cite: 90]."""
    
    # __init__ hereta de MiningStrategy. No cal reescriure'l.
    
    async def mine(self, inventory, requirements):
        self.logger.info("Estratègia VerticalSearch iniciada.")
        
        # Implementa la lògica de perforar cap avall (Y decreixent)
        pos = self.mc.player.getPos()
        start_y = pos.y - 1
        depth = 10 
        
        for y in range(start_y, start_y - depth, -1):
            # Simulació de picar un bloc
            # self.mc.setBlock(pos.x, y, pos.z, block.AIR.id)
            self.logger.debug(f"Picar a Y:{y}")
            await asyncio.sleep(0.1)
            
        return inventory