import time
import json
import time

from ClaroModule.claro import Claro
from SimpModule.sipm import Sipm
from Utils.utility import *


def main():
    mode = sys.argv[1]

    if mode == "sipm":
        print("SiPM ANALYZER")
        with open("./include/config.json") as json_data_file:
            data = json.load(json_data_file)

        config = Config(data)
        config.start_time = time.time()

        for key in config.filenames:
            pic_name = key.split(".")

            # Creiamo un oggetto sipm_wf
            filename_wave = config.folder_name + "/" + config.filenames[key]
            filename_time = config.folder_name + "/" + key

            init1 = time.time()
            print("Initializing Simp Module for file: " + config.filenames[key])
            wave_front_simp = Sipm(filename_wave, filename_time)
            init2 = time.time()
            config.init_time += init2 - init1

            analisi1 = time.time()
            print("Analyzing waveforms...")
            wave_front_simp.waveform_analyzer(config.n_points_baseline, pic_name[0], config.peak_height,
                                              config.peak_prominence, plot=True, compact=True)

            analisi2 = time.time()
            config.analysis_time += analisi2 - analisi1

            # Plottiamo i picchi
            picchi1 = time.time()
            print("Plotting peaks...")
            wave_front_simp.plot_peaks(pic_name[0])

            picchi2 = time.time()
            config.peak_time += picchi2 - picchi1

            # E stampiamo su terminale i valori ottenuti
            # NB la funzione richiede in ingresso una qualsiasi stringa che contenga il valore di OV (e nessun altro numero)
            dcr1 = time.time()
            print("Computing DCR...")
            wave_front_simp.calculate_dcr(config.filenames[key], config.group_name)

            dcr2 = time.time()
            config.Dcr_time += dcr2 - dcr1
        print("Plotting")
        print(config.group_name)
        plot_graphs_DCR_CTR_APR(config.group_name)
        config.end_time = time.time()
        config.print_times()
        # Plottiamo i picchi
        # picchi1 = time.time()

        # wave_front_simp.plot_peaks(pic_name[0])

        # picchi2 = time.time()
        # tempo_picchi += (picchi2-picchi1)

    if mode == "claro":
        elementi = 6000
        chip = 50

        claro = Claro()
        find_files()
        print("Starting Fitting...")
        t1 = time.time()
        claro.fit(elementi, chip,plot=False)
        t2 = time.time()

        print("Tempo fit per " + str(elementi) +
              " elementi e " + str(chip) + " chip: " + str(round(t2 - t1, 4)))

        # claro.err_fit_for_chips(elementi, chip)
        # claro.find_chips_threshold(elementi, chip)

        # t1 = time.time()
        # claro.fit(elementi, chip)
        # t2 = time.time()

        # claro.err_fit_for_chips(elementi, chip)
        # claro.find_chips_threshold(elementi, chip)

        # claro.sintesi_errori()

        # print("Tempo fit per "+str(elementi) +
        #     " elementi e "+str(chip)+" chip: "+str(round(t2-t1, 4)))


#     _sipm_wf_ = sipm_wf(filename_wave=filename_wave,
#                         filename_time=filename_time)

#     init2 = time.time()
#     tempo_init += (init2-init1)

#     # Cerchiamo i picchi
#     analisi1 = time.time()

#     _sipm_wf_.analyze_wfs_no_png(n_points_baseline, pic_name[0], peak_height,
#                           peak_prominence)

#     analisi2 = time.time()
#     tempo_analisi += (analisi2-analisi1)

#     # Plottiamo i picchi
#     picchi1 = time.time()

#     _sipm_wf_.plot_peaks(pic_name[0])

#     picchi2 = time.time()
#     tempo_picchi += (picchi2-picchi1)

#     # E stampiamo su terminale i valori ottenuti
#     # NB la funzione richiede in ingresso una qualsiasi stringa che contenga il valore di OV (e nessun altro numero)
#     dcr1 = time.time()

#     _sipm_wf_.calculate_dcr(filenames[key], group_name)

#     dcr2 = time.time()
#     tempo_dcr += (dcr2-dcr1)

# plot_graphs_DCR_CTR_APR(group_name)

# end = time.time()
# print("Tempo inizializzazione: " + str(tempo_init))
# print("Tempo analisi: " + str(tempo_analisi))
# print("Tempo plot picchi: " + str(tempo_picchi))
# print("Tempo calcolo DCR: " + str(tempo_dcr))
# print(f"Total runtime of the program is {end - begin}")


if __name__ == "__main__":
    main()
