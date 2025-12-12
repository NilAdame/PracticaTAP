from mcpi.event import ChatEvent
from mcpi.minecraft import Minecraft
import mcpi.block as block
import time

global mc
mc = Minecraft.create('localhost', 4711)
while True:
    for event in mc.events.pollChatPosts():
        print(event)