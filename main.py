from mcpi.minecraft import Minecraft, CmdEvents, Connection
import mcpi.block as block

from mcpi.minecraft import Minecraft
import mcpi.block as block
import time

global mc
mc = Minecraft.create('localhost', 25565)
while True:
    for event in mc.events.pollChatPosts():
        print(event)