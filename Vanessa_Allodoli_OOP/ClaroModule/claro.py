import os

import numpy as np
from Utils.utility import *


class Claro:

    def __init__(self):
        self.linear_difference_list = []
        self.difference_error_list = []

    def find_files(self):
        """
        Questa funzione esegue lo script 'analisi_file.sh', 
        generando il file path_file con i path di tutti i file .txt 
        che contengono i valori da analizzare.
        """
        print("_____________________________")
        dirname = os.getcwd()
        print(dirname)

        try:

            subprocess.call("./Utils/analisi_file.sh")
        except Exception as e:
            print(e)
            print("An error occurred trying to generate path_file.\n" +
                  "Please check if you have permission to execute 'analisi_file.sh'.")

    def linear_fit(self, number_of_files=20, number_of_chips=0, plot=True, inner_function=False, figure=None):
        """
        Funzione per il fit lineare.
        Parametri:
        - number_of_files: default 20, indica quanti file analizzare.
        - number_of_chips: default 0, indica quanti chip analizzare.
        Se 'number_of_chips' è 0, viene ignorato.
        Se 'number_of_chips' è diverso da 0, vengono analizzati 'number_of_files' file e 
        vengono considerati solo quelli con un numero di chip minore o uguale a 'number_of_chips'.
        """
        results = None
        if inner_function == True:
            plot = True
            if figure == None:
                Exception("Figure not Valid!")

        list_of_paths = self.read_pathfile(number_of_files, number_of_chips)
        if not plot:
            results = open("pythonResults.txt", "w")
        with alive_bar(len(list_of_paths), bar="bubbles", dual_line=True, title='Analyzing Waveforms') as bar:

            for i in range(0, len(list_of_paths)):
                x, y, true_threshold, chip_id, channel_number = self.read_single_file(
                    list_of_paths[i].strip())

                # In caso nel file ci siano valori non corretti, salta il ciclo
                if x == 0 and y == 0 and true_threshold == 0 and chip_id == 0:
                    continue
                self.linear_fit_function(x, y, true_threshold=true_threshold, chip_id=chip_id,
                                         channel_number=channel_number, plot=plot, i=i, inner_function=inner_function,
                                         results=results, figure=figure)
                bar(1)
        if not plot:
            results.close()

    def linear_fit_function(self, x, y, true_threshold=0, chip_id=0, channel_number=0, plot=True, i=0,
                            inner_function=False, results=None, figure=None):
        """

        @param x:
        @type x:
        @param y:
        @type y:
        @param true_threshold:
        @type true_threshold:
        @param chip_id:
        @type chip_id:
        @param channel_number:
        @type channel_number:
        @param plot:
        @type plot:
        @param i:
        @type i:
        @param inner_function:
        @type inner_function:
        @param results:
        @type results:
        @param figure:
        @type figure:
        """
        y_linearFit = np.array(y)
        y_linearFit = y_linearFit[y_linearFit > int(1 if (len(y_linearFit) == 1) else 5)]
        y_linearFit = y_linearFit[y_linearFit < int(999 if (len(y_linearFit) == 1) else 999)]

        # Se c'è un solo punto, l'intervallo è espanso sperando di trovarne almeno un altro

        mask_array = np.in1d(y, y_linearFit)
        # True solo i valori scelti per il fit
        mask_array = np.invert(mask_array)
        # Usando una maschera ricavo i valori x utili
        x_fit = ma.masked_array(x, mask=mask_array).compressed()

        linearCoefficient = np.polyfit(x_fit, y_linearFit, 1)

        x_threshold = (500 - linearCoefficient[1]) / linearCoefficient[0]

        self.linear_difference_list.append((true_threshold - x_threshold) ** 2)

        if plot:
            plt.scatter(x, y, marker='o')
            plt.grid()
            plt.xscale('linear')
            plt.yscale('linear')
            x_plot = x_fit
            # Aggiunti due punti in più per allungare la retta
            x_plot = np.insert(x_plot, 0, x_fit[0] - 2)
            x_plot = np.append(x_plot, x_fit[-1] + 2)
            y_plot = x_plot * linearCoefficient[0] + linearCoefficient[1]
            plt.text(x[0], y_plot[-2 if not inner_function else 900],
                     "Soglia calcolata " + "(lin):" if inner_function else ":" + " x=" + str(
                         round(x_threshold, 2)) + "V\nSoglia vera: x=" +
                                                                           str(round(true_threshold,
                                                                                     2)) + "V\nDifferenza: " + str(
                         round(true_threshold - x_threshold, 2)) + "V", fontsize=8)

            if not inner_function:
                plt.plot(x_plot, y_plot)
                plt.savefig("./claro/plot/fig" + str(i) + "_chip_" + str(chip_id) + ".png")
                plt.close()
            else:
                plt.plot(x_plot, y_plot, linestyle='--')
        else:
            results.write(
                "Chip: " + str(chip_id) + "\tCh: " + str(channel_number) + "\tReal Thres: " + str(true_threshold) +
                "\tThresh Found:" + str(x_threshold) + "\tDiff: " + str(abs(x_threshold - true_threshold)) + "\n")

    def fit(self, number_of_files=20, number_of_chips=0):
        """
        Funzione per il fit dei dati. Unisce le funzioni 'fit_lineare' 
        e 'err_fit' disegnando una sola figure_number con entrambe le curve 
        di approssimazione. Salva ogni curva come png.
        """

        list_of_paths = self.read_pathfile(number_of_files, number_of_chips)
        figure_number = 0
        last_chip = 1
        with alive_bar(len(list_of_paths), bar="classic", dual_line=True, title='Analyzing Waveforms') as bar:

            for i in range(0, len(list_of_paths)):
                x, y, true_threshold, chip_id, channel_number = self.read_single_file(
                    list_of_paths[i].strip())

                if x == 0 and y == 0 and true_threshold == 0 and chip_id == 0:
                    continue
                f = plt.figure()
                self.error_fitting_function(x, y, true_threshold=true_threshold, chip_id=chip_id,
                                            figure_number=figure_number, last_chip=last_chip, inner_function=True,
                                            figure=f)
                self.error_fitting_function(x, y, true_threshold=true_threshold, chip_id=chip_id,
                                            channel_number=channel_number, figure_number=figure_number,
                                            last_chip=last_chip, inner_function=True, figure=f)
                plt.savefig("./claro/plot_test/fit_fig" + str(i) + "_chip_" + str(chip_id) + ".jpg")
                plt.close()
                bar(1)
            # plt.scatter(x, y, marker='o')
            # plt.grid()
            # plt.xscale('linear')
            # plt.yscale('linear')

            # # Fit lineare
            # y_linearFit = np.array(y)
            # y_linearFit = y_linearFit[y_linearFit > 5]
            # y_linearFit = y_linearFit[y_linearFit < 990]

            # # Se c'è un solo punto, l'intervallo è espanso sperando di trovarne almeno un altro
            # if (len(y_linearFit) == 1):
            #     y_linearFit = np.array(y)
            #     y_linearFit = y_linearFit[y_linearFit > 1]
            #     y_linearFit = y_linearFit[y_linearFit < 999]

            # mask_array = np.in1d(y, y_linearFit)
            # # True solo i valori scelti per il fit
            # mask_array = np.invert(mask_array)
            # # Usando una maschera ricavo i valori x utili
            # x_linearFit = ma.masked_array(x, mask=mask_array).compressed()

            # linearCoefficient = np.polyfit(x_linearFit, y_linearFit, 1)
            # x_linearPlot = x_linearFit
            # # Aggiunti due punti in più per allungare la retta
            # x_linearPlot = np.insert(x_linearPlot, 0, x_linearFit[0]-2)
            # x_linearPlot = np.append(x_linearPlot, x_linearFit[-1]+2)
            # x_linearPlot = x_linearPlot*linearCoefficient[0] + linearCoefficient[1]

            # x_linearThreshold = (500 - linearCoefficient[1]) / linearCoefficient[0]

            # plt.text(x[0], 900, "Soglia calcolata (lin): x="+str(round(x_linearThreshold, 2))+"V\nSoglia vera: x=" +
            #          str(round(true_threshold, 2))+"V\nDifferenza: "+str(round(true_threshold-x_linearThreshold, 2))+"V", fontsize=8)

            # self.linear_difference_list.append((true_threshold-x_linearThreshold)**2)

            # plt.plot(x_linearPlot, x_linearPlot,linestyle="--")

            # Fit err function
            # x = np.array(x)
            # x_norm = [float(i) for i in x]  # Cast a float
            # x_norm -= np.mean(x_norm)

            # x_ERFplot = np.linspace(x_norm[0], x_norm[-1], len(x_norm)*100)
            # y_ERFplot = (special.erf(x_ERFplot)+1) * \
            #     500  # Adattamento verticale
            # x_ERFplot += x[0]  # Adattamento orizzontale

            # y_Junk = np.array(y)
            # y_Junk = y_Junk[y_Junk < 50]
            # index = len(y_Junk)  # Indice del primo elemento utile

            # # Indice dell'elemento della funzione con stessa y
            # extraFunctionIndex = np.argmin(abs(y_ERFplot - y[index]))
            # extra = abs(x[index]-(x_ERFplot[extraFunctionIndex]))

            # # Se ci sono due punti centrali, la curva è traslata in modo da essere
            # # il più vicina possibile ad entrambi i punti
            # if y[index+1] < 950:
            #     extraFunctionIndex_2 = np.argmin(abs(y_ERFplot - y[index+1]))
            #     extra2 = abs(x[index+1]-(x_ERFplot[extraFunctionIndex_2]))
            #     # Secondo adattamento orizzontale
            #     x_ERFplot += ((extra+extra2)/2)
            # else:
            #     x_ERFplot += extra  # Secondo adattamento orizzontale

            # indexThreshold = np.argmin(abs(y_ERFplot-500))
            # xERFthrehsold = x_ERFplot[indexThreshold]

            # plt.scatter(x_ERFplot[indexThreshold],
            #             y_ERFplot[indexThreshold], marker='o', color="black")

            # plt.text(x[0], 500, "Soglia calcolata (erf): x="+str(round(xERFthrehsold, 2))+"V\nSoglia vera: x=" +
            #          str(round(true_threshold, 2))+"V\nDifferenza: "+str(round(true_threshold-xERFthrehsold, 2))+"V", fontsize=8)

            # self.difference_error_list.append((true_threshold-xERFthrehsold)**2)
            # plt.plot(x_ERFplot, y_ERFplot)

    def err_fit_for_chips(self, number_of_files=200, minumum_number_of_chips_per_file=27, inner_function=False,
                          figure=None):
        """
        Funzione per il fit tramite la 'err_function()'.
        La funzione crea un unico plot per ciascun chip, contenente tutte le curve dei diversi canali.
        Se il numero di chip è ripetuto in stazioni diverse, 
        i grafici creati sono diversi (in ciascun grafico ci sono
        al più 8 curve relative agli 8 canali).

        Parametri:
        - number_of_files: default 200, indica quanti file analizzare.
        - minumum_number_of_chips_per_file: default 27, indica quanti chip analizzare.
        Se 'minumum_number_of_chips_per_file' è 0, viene ignorato.
        Se 'minumum_number_of_chips_per_file' è diverso da 0, vengono analizzati 'number_of_files' file e 
        vengono considerati solo quelli con un numero di chip minore o uguale a 'minumum_number_of_chips_per_file'.
        """

        if inner_function == True and figure == None:
            Exception("Figure not Valid!")

        list_of_paths = self.read_pathfile(number_of_files, minumum_number_of_chips_per_file)
        last_chip = 1
        figure_number = 0
        colors = ['blue', 'yellow', 'darkred', 'magenta',
                  'orange', 'red', 'green', 'lightblue']
        with alive_bar(len(list_of_paths), bar="bubbles", dual_line=True, title='Analyzing Waveforms') as bar:
            for i in range(0, len(list_of_paths)):
                x, y, true_threshold, chip_id, channel_number = self.read_single_file(
                    list_of_paths[i].strip())

                # In caso nel file ci siano valori non corretti, salta il ciclo
                if x == 0 and y == 0 and true_threshold == 0 and chip_id == 0:
                    continue
                self.error_fitting_function(x, y, true_threshold, chip_id=chip_id, channel_number=channel_number,
                                            figure_number=figure_number, last_chip=last_chip, colors=colors,
                                            inner_function=inner_function, figure=figure)
                bar(1)

    def error_fitting_function(self, x: np.array, y: np.array, true_threshold: float, chip_id: int = None,
                               channel_number: int = 0, figure_number: int = 0,
                               last_chip: int = 1,
                               colors: list = None, inner_function: bool = False, figure: object = None):
        """

        :param x:
        :type x:
        :param y:
        :type y:
        :param true_threshold:
        :type true_threshold:
        :param chip_id:
        :type chip_id:
        :param channel_number:
        :type channel_number:
        :param figure_number:
        :type figure_number:
        :param last_chip:
        :type last_chip:
        :param colors:
        :type colors:
        :param inner_function:
        :type inner_function:
        :param figure:
        :type figure:
        """
        if not inner_function:
            # Se si inizia il plot di un nuovo chip, serve chiudere la figure_number vecchia
            if chip_id != last_chip:
                figure_number += 1
                plt.yticks(np.arange(0, 1000, step=100))
                plt.title("Chip " + str(last_chip))
                last_chip = chip_id

            plt.scatter(x, y, marker='o', color=colors[channel_number])
            plt.xscale('linear')
            plt.yscale('linear')

        x = np.array(x)
        x_norm = [float(i) for i in x]  # Cast a float
        x_norm -= np.mean(x_norm)

        x_plot = np.linspace(x_norm[0], x_norm[-1], len(x_norm) * 200)
        y_plot = (special.erf(x_plot) + 1) * 500  # Adattamento verticale
        x_plot += x[0]  # Adattamento orizzontale

        yJunk = np.array(y)
        yJunk = yJunk[yJunk < 50]
        index = len(yJunk)  # Indice del primo elemento utile

        # Indice dell'elemento della funzione con stessa y
        extraFunctionIndex = np.argmin(abs(y_plot - y[index]))
        extra = abs(x[index] - (x_plot[extraFunctionIndex]))

        # Se ci sono due punti centrali, la curva è traslata in modo da essere
        # il più vicina possibile ad entrambi i punti
        if y[index + 1] < 950:
            extraFunctionIndex2 = np.argmin(abs(y_plot - y[index + 1]))
            extra2 = abs(x[index + 1] - (x_plot[extraFunctionIndex2]))
            x_plot += ((extra + extra2) / 2)  # Secondo adattamento orizzontale
        else:
            x_plot += extra  # Secondo adattamento orizzontale

        index_Threshold = np.argmin(abs(y_plot - 500))
        xThreshold = x_plot[index_Threshold]

        plt.scatter(x_plot[index_Threshold],
                    y_plot[index_Threshold], marker='o', color="black")
        if not inner_function:
            plt.plot(x_plot, y_plot,
                     color=colors[channel_number], label='Ch. ' + str(channel_number))
        else:
            plt.plot(x_plot, y_plot)
            plt.text(x[0], 500, "Soglia calcolata (erf): x=" + str(round(xThreshold, 2)) + "V\nSoglia vera: x=" +
                     str(round(true_threshold, 2)) + "V\nDifferenza: " + str(
                round(true_threshold - xThreshold, 2)) + "V", fontsize=8)

        self.difference_error_list.append((true_threshold - xThreshold) ** 2)

        if not inner_function:
            plt.yticks(np.arange(0, 1000, step=100))
            plt.grid()
            plt.legend()
            plt.savefig("./claro/plot/err_fit_chip_" + str(figure_number + 1) + ".png")
            plt.close()

    def find_chips_threshold(self, number_of_files=400, number_of_chips=259):
        """
        Questa funzione trova il valore di soglia per ciascun canale di ciascun chip,
        li salva su file e li disegna in uno scatter plot (uno per ciascun chip).
        Non salva i grafici dei fit.

        Parametri:
        - number_of_files: default 400, indica quanti file analizzare.
        - number_of_chips: default 259, indica quanti chip analizzare.

        NB: "number_of_files" verrà convertito automaticamente al successivo multiplo di 9
        """

        list_of_paths = self.read_pathfile(number_of_files, number_of_chips)
        chips_values = {}
        number_of_files += (9 - number_of_files % 9)

        for i in range(0, len(list_of_paths)):
            x, y, _, chip_id, channel_number = self.read_single_file(
                list_of_paths[i].strip())

            if x == 0 and y == 0 and chip_id == 0 and channel_number == 0:
                continue

            x = np.array(x)
            x_norm = [float(i) for i in x]  # Cast a float
            x_norm -= np.mean(x_norm)
            x_plot = np.linspace(x_norm[0], x_norm[-1], len(x_norm) * 200)
            y_plot = (special.erf(x_plot) + 1) * 500  # Adattamento verticale
            x_plot += x[0]  # Adattamento orizzontale

            # Ricerca valore di soglia (per commenti più dettagliati
            # si rimanda alla funzione "err_fit()")
            yJunk = np.array(y)
            yJunk = yJunk[yJunk < 50]
            index = len(yJunk)  # Indice del primo elemento utile
            extraFunctionIndex = np.argmin(abs(y_plot - y[index]))
            extra = abs(x[index] - (x_plot[extraFunctionIndex]))
            if y[index + 1] < 950:
                extraFunctionIndex_2 = np.argmin(abs(y_plot - y[index + 1]))
                extra2 = abs(x[index + 1] - (x_plot[extraFunctionIndex_2]))
                x_plot += ((extra + extra2) / 2)  # Secondo adattamento orizzontale
            else:
                x_plot += extra  # Secondo adattamento orizzontale
            thresholdIndex = np.argmin(abs(y_plot - 500))
            xThreshold = x_plot[thresholdIndex]

            # Aggiunta del valore soglia al dizionario
            if chip_id * 10 + channel_number not in chips_values:
                chips_values[chip_id * 10 + channel_number] = [xThreshold]
            else:
                chips_values[chip_id * 10 + channel_number].append(xThreshold)

        self.draw_dict(chips_values, number_of_chips)

    def read_pathfile(self, number_of_files, number_of_chips):
        """
        Dato il numero di file da analizzare, restituisce i rispettivi X path.
        Questi vengono filtrati se il valore 'number_of_chips' è diverso da 0,
        in modo da contenere i path relativi ai file con numero di chip
        minore o uguale a 'number_of_chips'.
        """

        try:
            file_path = open('file_path.txt', 'r')
        except:
            print("Errore nella lettura del file")

        list_of_paths = []
        number_of_chips = min(number_of_chips, 259)

        # In caso l'utente specifichi un numero X di chip
        if number_of_chips != 0:
            for _ in range(0, number_of_files):
                pathfile = file_path.readline().strip()
                chip_string = pathfile.split("/")
                chip_string = chip_string[4].split("_")  # "Chip_001"
                chip_number = int(chip_string[1])  # Trovato il numero del chip

                # Si aggiunge il path solo se il chip è tra i primi X
                if chip_number <= number_of_chips:
                    list_of_paths.append(pathfile)

        # In caso l'utente specifichi un numero X di file
        else:
            for _ in range(0, number_of_files):
                pathfile = file_path.readline().strip()
                list_of_paths.append(pathfile)

        file_path.close()
        return list_of_paths

    def read_single_file(self, path):
        """
        Dato il path di un file, restituisce una lista di x, una lista di y,
        il valore di soglia, il numero del chip e il numero del canale.
        """

        f = open(path, "r")

        x = []
        y = []

        chip_string = path.split("/")
        chip_string = chip_string[6].split("_")  # "Chip_001"
        chip_id = int(chip_string[5].split(".")[0])
        chip_channel = int(chip_string[1])

        line = f.readline()
        if line.startswith("error") or line.startswith("Non") or line.startswith("Troppi"):
            return 0, 0, 0, 0, 0

        line = line.split()
        true_threshold = float(line[1])
        line = f.readline()
        line = f.readline()

        while True:
            # Get next line from file
            line = f.readline()

            if not line:
                break

            values = line.split()
            x.append(int(values[0]))
            y.append(int(values[1]))

        f.close()
        return x, y, true_threshold, chip_id, chip_channel

    def draw_dict(self, dictionary, number_of_chips_to_draw):
        """
        Funzione per creare un grafico a partire da un dictionary.
        Crea immagini con 9 subplot in modo da ottimizzare i tempi.

        Parametri:
        - dictionary: dictionary da disegnare.
        - number_of_chips_to_draw: numero di chip di cui fare il grafico.

        """

        if (len(dictionary) / 8) < (number_of_chips_to_draw * 8 + 1.4 * len(dictionary)):
            print("dictionary: " + str(len(dictionary)) + " number_of_chips_to_draw: " + str(number_of_chips_to_draw))
            print("WARNING: you may required too many chips or too few file to read." +
                  " You may find blank graphs.")

        number_of_chips_to_draw = min(number_of_chips_to_draw, 259)
        print("Processing " + str(number_of_chips_to_draw) + " elements...")
        number_of_chips_to_draw += 1
        numer_of_figures = number_of_chips_to_draw // 9
        remainder = number_of_chips_to_draw % 9
        number_of_chips_to_draw -= 1

        if remainder != 0:
            numer_of_figures += 1

        with alive_bar(((number_of_chips_to_draw) % 9) + 1, bar="bubbles", dual_line=True,
                       title='Analyzed Chips Progress') as bar:

            for i in range(1, number_of_chips_to_draw, 9):

                fig, ax = plt.subplots(nrows=3, ncols=3, figsize=(15, 10))
                colors = ['blue', 'yellow', 'darkred', 'magenta',
                          'orange', 'red', 'green', 'lightblue']

                # Itera 9 volte, una per ogni chip in fig
                for chip_id in range(i, 9 + i):

                    if chip_id > number_of_chips_to_draw:
                        break

                    # g è il numero del grafico che si sta disegnando
                    gextra_funct_index = ((chip_id - 1) % 9)

                    for ch in range(0, 8):  # Itera 8 volte, una per ogni canale del chip
                        try:
                            x_plot = dictionary[chip_id * 10 + ch]
                        except:
                            # print("chip "+str(chip_id)+" vuoto")
                            ax[gextra_funct_index // 3][gextra_funct_index % 3].title.set_text(
                                "Chip " + str(chip_id) + " (missing data on some ch)")
                            break
                        y_plot = np.ones(len(x_plot)) * 500

                        ax[gextra_funct_index // 3][gextra_funct_index % 3].scatter(x_plot, y_plot,
                                                                                    label="Ch. " + str(ch), marker='o',
                                                                                    color=colors[ch])
                        ax[gextra_funct_index // 3][gextra_funct_index % 3].title.set_text("Chip " + str(chip_id))

                fig.savefig("./claro/plot/soglie" + str(i) + ".png")
                plt.close(fig)
                bar(1)
