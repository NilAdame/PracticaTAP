from mcpi.minecraft import Minecraft, CmdEvents, Connection
import mcpi.block as block
import asyncio

from mcpi.minecraft import Minecraft
import mcpi.block as block
import time
#Dades per conectarme al servidor
SERVER_HOST = 'localhost'
ADDRES = 25565


mc = Minecraft.create()
while True:
    for i in mc.events.pollChatPosts():
        print(i)
 
   