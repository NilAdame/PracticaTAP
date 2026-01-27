from .MiningStrategy import MiningStrategy
from mcpi.block import STONE, AIR
import logging

logger = logging.getLogger("VerticalMining")

class VerticalMining(MiningStrategy):
    def __init__(self):
        self.mined_positions = set()  # Guardem les posicions ja minades
        self.mining_started = False   # Control si ja hem començat
        super().__init__()
    
    def execute(self, mc, bot):
        # 1. La primera vegada, obtenim la posició del jugador
        if not self.mining_started:
            if bot.mine_x == 0 and bot.mine_z == 0: # Si estan buides
                player_pos = mc.player.getPos()
                bot.mine_x, bot.mine_y, bot.mine_z = int(player_pos.x), int(player_pos.y)-1, int(player_pos.z)
        
        self.mining_started = True
        logger.info(f"VerticalMining: Començant a ({bot.mine_x}, {bot.mine_y}, {bot.mine_z})")
        
        start_x = bot.mine_x
        start_y = bot.mine_y
        start_z = bot.mine_z
        
        blocs_minats = 0
        
        # 2. Minem cap avall des de la posició del jugador
        # Busquem 10 blocs cap avall
        for dy in range(0, 10):
            target_y = start_y - dy
            
            # Evitem bedrock (y < 1)
            if target_y < 1:
                logger.warning(f"VerticalMining: Hem arribat a bedrock!")
                break
                
            pos_tuple = (start_x, target_y, start_z)
            if pos_tuple in self.mined_positions:
                logger.debug(f"VerticalMining: Posició ja minada: {pos_tuple}")
                continue
            
            block_id = mc.getBlock(start_x, target_y, start_z)
            
            logger.info(f"VerticalMining: Comprovant bloc a ({start_x}, {target_y}, {start_z}): block_id={block_id}")
            
            if block_id == STONE.id:  # Només mina STONE
                # Obtenim el bloc complet amb dades
                block_with_data = mc.getBlockWithData(start_x, target_y, start_z)
                
                # Guardem el bloc a l'inventari (com a llista de blocs)
                if "stone" not in bot.inventory:
                    bot.inventory["stone"] = []
                bot.inventory["stone"].append(block_with_data)
                
                # Esborra el bloc del Minecraft
                mc.setBlock(start_x, target_y, start_z, AIR)
                
                # Marcar com minada
                self.mined_positions.add(pos_tuple)
                
                blocs_minats += 1
                logger.info(f"VerticalMining: Bloc minat! Inventory total: {len(bot.inventory['stone'])} pedres")
        
        # 3. Baixem la posició per a la propera iteració
        bot.mine_y -= 10
        logger.info(f"VerticalMining: S'han minat {blocs_minats} blocs. Noves coordenades: ({start_x}, {bot.mine_y}, {start_z})")
        
        return "SUCCESS"