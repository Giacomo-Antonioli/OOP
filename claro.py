import time

from claro_class import claro_class

elementi = 6000
chip = 2

claro = claro_class()

t1 = time.time()
claro.fit(elementi, chip)
t2 = time.time()

claro.err_fit_for_chips(elementi, chip)
claro.find_chips_threshold(elementi, chip)

claro.sintesi_errori()

print("Tempo fit per "+str(elementi) +
      " elementi e "+str(chip)+" chip: "+str(round(t2-t1, 4)))
