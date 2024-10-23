from backend.dmx.dmx_player import DmxPlayer

player = DmxPlayer("backend/dmx/dmx.bin")
player.run()
player.play()

print("Done")