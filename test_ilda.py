from backend.ilda.ilda_player import IldaPlayer

player = IldaPlayer("backend/ilda/test.ildx")
player.run()
player.play()

print("Done")