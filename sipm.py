import time

from sipm_class import *

# Settiamo i parametri per la ricerca dei picchi, da dare in pasto al metodo
n_points_baseline = 500
peak_height = 0.001
peak_prominence = 0.0001

tempo_init = 0.0
tempo_analisi = 0.0
tempo_picchi = 0.0
tempo_dcr = 0.0

group_name = "gruppo_r"
folder = './source'
filenames = {"r203ov.csv": "r203ovwav.csv",
            "r204ov.csv": "r204ovwav.csv",
            "r205ov.csv": "r205ovwav.csv"}
#filenames = {"r203ov.csv": "r203ovwav.csv"}
#filenames = {"Timestamp.csv": "Waveform.csv"}

begin = time.time()

for key in filenames:
    pic_name = key.split(".")


    # Creiamo un oggetto sipm_wf
    filename_wave = folder + "/" + filenames[key]
    filename_time = folder + "/" + key
    print("ER")
    init1 = time.time()
    print(filename_wave)
    _sipm_wf_ = sipm_wf(filename_wave=filename_wave,
                        filename_time=filename_time)
    print("ER")
    init2 = time.time()
    tempo_init += (init2-init1)
    print("ER")
    # Cerchiamo i picchi
    analisi1 = time.time()

    _sipm_wf_.analyze_wfs_no_png(n_points_baseline, pic_name[0], peak_height,
                          peak_prominence)

    analisi2 = time.time()
    tempo_analisi += (analisi2-analisi1)

    # Plottiamo i picchi
    picchi1 = time.time()

    _sipm_wf_.plot_peaks(pic_name[0])

    picchi2 = time.time()
    tempo_picchi += (picchi2-picchi1)

    # E stampiamo su terminale i valori ottenuti
    # NB la funzione richiede in ingresso una qualsiasi stringa che contenga il valore di OV (e nessun altro numero)
    dcr1 = time.time()

    _sipm_wf_.calculate_dcr(filenames[key], group_name)
    
    dcr2 = time.time()
    tempo_dcr += (dcr2-dcr1)

draw_tot_graphs(group_name)

end = time.time()
print("Tempo inizializzazione: " + str(tempo_init))
print("Tempo analisi: " + str(tempo_analisi))
print("Tempo plot picchi: " + str(tempo_picchi))
print("Tempo calcolo DCR: " + str(tempo_dcr))
print(f"Total runtime of the program is {end - begin}")