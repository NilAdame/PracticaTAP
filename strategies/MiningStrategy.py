from abc import ABC, abstractmethod

class MiningStrategy(ABC):
    @abstractmethod
    def execute(self, mc, bot):
        """
        Mètode que tota estratègia de mineria ha d'implementar.
        :param mc: Connexió a Minecraft (mcpi)
        :param bot: Instància del bot que executa l'estratègia
        """
        pass