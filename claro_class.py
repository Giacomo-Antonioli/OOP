import subprocess
from matplotlib import pyplot as plt
import numpy as np
import numpy.ma as ma
from scipy import special
import math
import progressbar


class claro_class:

    def __init__(self):
        self.lista_diff_lineare = []
        self.lista_diff_err = []

    def find_files(self):
        """
        Questa funzione esegue lo script 'analisi_file.sh', 
        generando il file path_file con i path di tutti i file .txt 
        che contengono i valori da analizzare.
        """
        try:
            subprocess.call("./analisi_file.sh")
        except:
            print("An error occurred trying to generate path_file.\n" +
                  "Please check if you have permission to execute 'analisi_file.sh'.")

    def linear_fit(self, how_many=20, how_many_chips=0):
        """
        Funzione per il fit lineare.
        Parametri:
        - how_many: default 20, indica quanti file analizzare.
        - how_many_chips: default 0, indica quanti chip analizzare.
        Se 'how_many_chips' è 0, viene ignorato.
        Se 'how_many_chips' è diverso da 0, vengono analizzati 'how_many' file e 
        vengono considerati solo quelli con un numero di chip minore o uguale a 'how_many_chips'.
        """

        list_of_paths = self.read_pathfile(how_many, how_many_chips)

        for i in range(0, len(list_of_paths)):
            x, y, soglia_vera, num_chip, _ = self.read_single_file(
                list_of_paths[i].strip())

            # In caso nel file ci siano valori non corretti, salta il ciclo
            if x == 0 and y == 0 and soglia_vera == 0 and num_chip == 0:
                continue

            y_lin_fit = np.array(y)
            y_lin_fit = y_lin_fit[y_lin_fit > 5]
            y_lin_fit = y_lin_fit[y_lin_fit < 990]

            # Se c'è un solo punto, l'intervallo è espanso sperando di trovarne almeno un altro
            if (len(y_lin_fit) == 1):
                y_lin_fit = np.array(y)
                y_lin_fit = y_lin_fit[y_lin_fit > 1]
                y_lin_fit = y_lin_fit[y_lin_fit < 999]

            mask_array = np.in1d(y, y_lin_fit)
            # True solo i valori scelti per il fit
            mask_array = np.invert(mask_array)
            # Usando una maschera ricavo i valori x utili
            x_fit = ma.masked_array(x, mask=mask_array).compressed()

            plt.scatter(x, y, marker='o')
            plt.grid()
            plt.xscale('linear')
            plt.yscale('linear')

            coeff = np.polyfit(x_fit, y_lin_fit, 1)
            x_plot = x_fit
            # Aggiunti due punti in più per allungare la retta
            x_plot = np.insert(x_plot, 0, x_fit[0]-2)
            x_plot = np.append(x_plot, x_fit[-1]+2)
            y_plot = x_plot*coeff[0] + coeff[1]

            x_soglia = (500 - coeff[1]) / coeff[0]

            plt.text(x[0], y_plot[-2], "Soglia calcolata: x="+str(round(x_soglia, 2))+"V\nSoglia vera: x=" +
                     str(round(soglia_vera, 2))+"V\nDifferenza: "+str(round(soglia_vera-x_soglia, 2))+"V", fontsize=8)

            self.lista_diff_lineare.append((soglia_vera-x_soglia)**2)
            plt.plot(x_plot, y_plot)
            plt.savefig("plot/fig"+str(i)+"_chip_"+str(num_chip)+".png")
            plt.close()

    def linear_fit_no_png(self, how_many=20, how_many_chips=0):
        """
        Funzione per il fit lineare senza png.
        Parametri:
        - how_many: default 20, indica quanti file analizzare.
        - how_many_chips: default 0, indica quanti chip analizzare.
        Se 'how_many_chips' è 0, viene ignorato.
        Se 'how_many_chips' è diverso da 0, vengono analizzati 'how_many' file e 
        vengono considerati solo quelli con un numero di chip minore o uguale a 'how_many_chips'.

        Essenzialmente serve per confrontare i tempi tra Py e C++.
        """

        list_of_paths = self.read_pathfile(how_many, how_many_chips)
        risultati = open("risultati_py.txt", "w")

        for i in range(0, len(list_of_paths)):
            x, y, soglia_vera, num_chip, num_ch = self.read_single_file(
                list_of_paths[i].strip())

            # In caso nel file ci siano valori non corretti, salta il ciclo
            if x == 0 and y == 0 and soglia_vera == 0 and num_chip == 0:
                continue

            y_fit = np.array(y)
            y_fit = y_fit[y_fit > 1]
            y_fit = y_fit[y_fit < 999]

            mask_array = np.in1d(y, y_fit)
            # True solo i valori scelti per il fit
            mask_array = np.invert(mask_array)
            # Usando una maschera ricavo i valori x utili
            x_fit = ma.masked_array(x, mask=mask_array).compressed()

            coeff = np.polyfit(x_fit, y_fit, 1)

            x_soglia = (500 - coeff[1]) / coeff[0]
            risultati.write("Chip: "+str(num_chip)+"\tCh: "+str(num_ch)+"\tReal Thres: "+str(soglia_vera) +
                            "\tThresh Found:"+str(x_soglia)+"\tDiff: "+str(abs(x_soglia-soglia_vera))+"\n")

            self.lista_diff_lineare.append((soglia_vera-x_soglia)**2)
        risultati.close()

    def err_fit(self, how_many=20, how_many_chips=0):
        """
        Funzione per il fit tramite la 'err_function()'.
        Parametri:
        - how_many: default 20, indica quanti file analizzare.
        - how_many_chips: default 0, indica quanti chip analizzare.
        Se 'how_many_chips' è 0, viene ignorato.
        Se 'how_many_chips' è diverso da 0, vengono analizzati 'how_many' file e 
        vengono considerati solo quelli con un numero di chip minore o uguale a 'how_many_chips'.
        """

        list_of_paths = self.read_pathfile(how_many, how_many_chips)

        for i in range(0, len(list_of_paths)):

            x, y, soglia_vera, num_chip, _ = self.read_single_file(
                list_of_paths[i].strip())

            if x == 0 and y == 0 and soglia_vera == 0 and num_chip == 0:
                continue

            plt.scatter(x, y, marker='o')
            plt.grid()
            plt.xscale('linear')
            plt.yscale('linear')

            x = np.array(x)
            x_norm = [float(i) for i in x]  # Cast a float
            x_norm -= np.mean(x_norm)

            x_plot = np.linspace(x_norm[0], x_norm[-1], len(x_norm)*100)
            y_plot = (special.erf(x_plot)+1)*500  # Adattamento verticale
            x_plot += x[0]  # Adattamento orizzontale

            y_inutili = np.array(y)
            y_inutili = y_inutili[y_inutili < 50]
            index = len(y_inutili)  # Indice del primo elemento utile

            # Indice dell'elemento della funzione con stessa y
            extra_funct_index = np.argmin(abs(y_plot - y[index]))
            extra = abs(x[index]-(x_plot[extra_funct_index]))

            # Se ci sono due punti centrali, la curva è traslata in modo da essere
            # il più vicina possibile ad entrambi i punti
            if y[index+1] < 950:
                extra_funct_index2 = np.argmin(abs(y_plot - y[index+1]))
                extra2 = abs(x[index+1]-(x_plot[extra_funct_index2]))
                x_plot += ((extra+extra2)/2)  # Secondo adattamento orizzontale
            else:
                x_plot += extra  # Secondo adattamento orizzontale

            index_soglia = np.argmin(abs(y_plot-500))
            x_soglia = x_plot[index_soglia]

            plt.scatter(x_plot[index_soglia],
                        y_plot[index_soglia], marker='o', color="black")

            plt.plot(x_plot, y_plot)

            plt.text(x[0], y_plot[index_soglia], "Soglia calcolata: x="+str(round(x_soglia, 2))+"V\nSoglia vera: x=" +
                     str(round(soglia_vera, 2))+"V\nDifferenza: "+str(round(soglia_vera-x_soglia, 2))+"V", fontsize=8)

            self.lista_diff_err.append((soglia_vera-x_soglia)**2)
            plt.savefig("plot/err_fig"+str(i)+"_chip_"+str(num_chip)+".jpg")
            plt.close()

    def fit(self, how_many=20, how_many_chips=0):
        """
        Funzione per il fit dei dati. Unisce le funzioni 'fit_lineare' 
        e 'err_fit' disegnando una sola figura con entrambe le curve 
        di approssimazione. Salva ogni curva come png.
        """

        list_of_paths = self.read_pathfile(how_many, how_many_chips)

        for i in range(0, len(list_of_paths)):
            x, y, soglia_vera, num_chip, _ = self.read_single_file(
                list_of_paths[i].strip())

            if x == 0 and y == 0 and soglia_vera == 0 and num_chip == 0:
                continue

            plt.scatter(x, y, marker='o')
            plt.grid()
            plt.xscale('linear')
            plt.yscale('linear')

            # Fit lineare
            y_lin_fit = np.array(y)
            y_lin_fit = y_lin_fit[y_lin_fit > 5]
            y_lin_fit = y_lin_fit[y_lin_fit < 990]

            # Se c'è un solo punto, l'intervallo è espanso sperando di trovarne almeno un altro
            if (len(y_lin_fit) == 1):
                y_lin_fit = np.array(y)
                y_lin_fit = y_lin_fit[y_lin_fit > 1]
                y_lin_fit = y_lin_fit[y_lin_fit < 999]

            mask_array = np.in1d(y, y_lin_fit)
            # True solo i valori scelti per il fit
            mask_array = np.invert(mask_array)
            # Usando una maschera ricavo i valori x utili
            x_lin_fit = ma.masked_array(x, mask=mask_array).compressed()

            coeff = np.polyfit(x_lin_fit, y_lin_fit, 1)
            x_lin_plot = x_lin_fit
            # Aggiunti due punti in più per allungare la retta
            x_lin_plot = np.insert(x_lin_plot, 0, x_lin_fit[0]-2)
            x_lin_plot = np.append(x_lin_plot, x_lin_fit[-1]+2)
            y_lin_plot = x_lin_plot*coeff[0] + coeff[1]

            x_lin_soglia = (500 - coeff[1]) / coeff[0]

            plt.text(x[0], 900, "Soglia calcolata (lin): x="+str(round(x_lin_soglia, 2))+"V\nSoglia vera: x=" +
                     str(round(soglia_vera, 2))+"V\nDifferenza: "+str(round(soglia_vera-x_lin_soglia, 2))+"V", fontsize=8)

            self.lista_diff_lineare.append((soglia_vera-x_lin_soglia)**2)
            plt.plot(x_lin_plot, y_lin_plot, linestyle='--')

            # Fit err function
            x = np.array(x)
            x_norm = [float(i) for i in x]  # Cast a float
            x_norm -= np.mean(x_norm)

            x_erf_plot = np.linspace(x_norm[0], x_norm[-1], len(x_norm)*100)
            y_erf_plot = (special.erf(x_erf_plot)+1) * \
                500  # Adattamento verticale
            x_erf_plot += x[0]  # Adattamento orizzontale

            y_inutili = np.array(y)
            y_inutili = y_inutili[y_inutili < 50]
            index = len(y_inutili)  # Indice del primo elemento utile

            # Indice dell'elemento della funzione con stessa y
            extra_funct_index = np.argmin(abs(y_erf_plot - y[index]))
            extra = abs(x[index]-(x_erf_plot[extra_funct_index]))

            # Se ci sono due punti centrali, la curva è traslata in modo da essere
            # il più vicina possibile ad entrambi i punti
            if y[index+1] < 950:
                extra_funct_index2 = np.argmin(abs(y_erf_plot - y[index+1]))
                extra2 = abs(x[index+1]-(x_erf_plot[extra_funct_index2]))
                # Secondo adattamento orizzontale
                x_erf_plot += ((extra+extra2)/2)
            else:
                x_erf_plot += extra  # Secondo adattamento orizzontale

            index_soglia = np.argmin(abs(y_erf_plot-500))
            x_erf_soglia = x_erf_plot[index_soglia]

            plt.scatter(x_erf_plot[index_soglia],
                        y_erf_plot[index_soglia], marker='o', color="black")

            plt.text(x[0], 500, "Soglia calcolata (erf): x="+str(round(x_erf_soglia, 2))+"V\nSoglia vera: x=" +
                     str(round(soglia_vera, 2))+"V\nDifferenza: "+str(round(soglia_vera-x_erf_soglia, 2))+"V", fontsize=8)

            self.lista_diff_err.append((soglia_vera-x_erf_soglia)**2)
            plt.plot(x_erf_plot, y_erf_plot)
            plt.savefig("plot/fit_fig"+str(i)+"_chip_"+str(num_chip)+".jpg")
            plt.close()

    def err_fit_for_chips(self, how_many=200, how_many_chips=27):
        """
        Funzione per il fit tramite la 'err_function()'.
        La funzione crea un unico plot per ciascun chip, contenente tutte le curve dei diversi canali.
        Se il numero di chip è ripetuto in stazioni diverse, 
        i grafici creati sono diversi (in ciascun grafico ci sono
        al più 8 curve relative agli 8 canali).

        Parametri:
        - how_many: default 200, indica quanti file analizzare.
        - how_many_chips: default 27, indica quanti chip analizzare.
        Se 'how_many_chips' è 0, viene ignorato.
        Se 'how_many_chips' è diverso da 0, vengono analizzati 'how_many' file e 
        vengono considerati solo quelli con un numero di chip minore o uguale a 'how_many_chips'.
        """

        list_of_paths = self.read_pathfile(how_many, how_many_chips)
        last_chip = 1
        figura = 0
        colors = ['blue', 'yellow', 'darkred', 'magenta',
                  'orange', 'red', 'green', 'lightblue']

        for i in range(0, len(list_of_paths)):
            x, y, soglia_vera, num_chip, num_ch = self.read_single_file(
                list_of_paths[i].strip())

            # In caso nel file ci siano valori non corretti, salta il ciclo
            if x == 0 and y == 0 and soglia_vera == 0 and num_chip == 0:
                continue

            # Se si inizia il plot di un nuovo chip, serve chiudere la figura vecchia
            if num_chip != last_chip:
                figura +=1
                plt.yticks(np.arange(0, 1000, step=100))
                plt.grid()
                plt.legend()
                plt.title("Chip "+str(last_chip))
                plt.savefig("plot/err_fit_"+str(figura)+".png")
                last_chip = num_chip
                plt.close()

            plt.scatter(x, y, marker='o', color=colors[num_ch])
            plt.xscale('linear')
            plt.yscale('linear')

            x = np.array(x)
            x_norm = [float(i) for i in x]  # Cast a float
            x_norm -= np.mean(x_norm)

            x_plot = np.linspace(x_norm[0], x_norm[-1], len(x_norm)*200)
            y_plot = (special.erf(x_plot)+1)*500  # Adattamento verticale
            x_plot += x[0]  # Adattamento orizzontale

            y_inutili = np.array(y)
            y_inutili = y_inutili[y_inutili < 50]
            index = len(y_inutili)  # Indice del primo elemento utile

            # Indice dell'elemento della funzione con stessa y
            extra_funct_index = np.argmin(abs(y_plot - y[index]))
            extra = abs(x[index]-(x_plot[extra_funct_index]))

            # Se ci sono due punti centrali, la curva è traslata in modo da essere
            # il più vicina possibile ad entrambi i punti
            if y[index+1] < 950:
                extra_funct_index2 = np.argmin(abs(y_plot - y[index+1]))
                extra2 = abs(x[index+1]-(x_plot[extra_funct_index2]))
                x_plot += ((extra+extra2)/2)  # Secondo adattamento orizzontale
            else:
                x_plot += extra  # Secondo adattamento orizzontale

            index_soglia = np.argmin(abs(y_plot-500))
            x_soglia = x_plot[index_soglia]

            plt.scatter(x_plot[index_soglia],
                        y_plot[index_soglia], marker='o', color="black")

            plt.plot(x_plot, y_plot,
                     color=colors[num_ch], label='Ch. '+str(num_ch))
            self.lista_diff_err.append((soglia_vera-x_soglia)**2)

        plt.yticks(np.arange(0, 1000, step=100))
        plt.grid()
        plt.legend()
        plt.savefig("plot/err_fit_chip_"+str(figura+1)+".png")
        plt.close()

    def find_chips_threshold(self, how_many=400, how_many_chips=259):
        """
        Questa funzione trova il valore di soglia per ciascun canale di ciascun chip,
        li salva su file e li disegna in uno scatter plot (uno per ciascun chip).
        Non salva i grafici dei fit.

        Parametri:
        - how_many: default 400, indica quanti file analizzare.
        - how_many_chips: default 259, indica quanti chip analizzare.

        NB: "how_many" verrà convertito automaticamente al successivo multiplo di 9
        """

        list_of_paths = self.read_pathfile(how_many, how_many_chips)
        chips_values = {}
        how_many += (9 - how_many % 9)

        for i in range(0, len(list_of_paths)):
            x, y, _, num_chip, num_ch = self.read_single_file(
                list_of_paths[i].strip())

            if x == 0 and y == 0 and num_chip == 0 and num_ch == 0:
                continue

            x = np.array(x)
            x_norm = [float(i) for i in x]  # Cast a float
            x_norm -= np.mean(x_norm)
            x_plot = np.linspace(x_norm[0], x_norm[-1], len(x_norm)*200)
            y_plot = (special.erf(x_plot)+1)*500  # Adattamento verticale
            x_plot += x[0]  # Adattamento orizzontale

            # Ricerca valore di soglia (per commenti più dettagliati
            # si rimanda alla funzione "err_fit()")
            y_inutili = np.array(y)
            y_inutili = y_inutili[y_inutili < 50]
            index = len(y_inutili)  # Indice del primo elemento utile
            extra_funct_index = np.argmin(abs(y_plot - y[index]))
            extra = abs(x[index]-(x_plot[extra_funct_index]))
            if y[index+1] < 950:
                extra_funct_index2 = np.argmin(abs(y_plot - y[index+1]))
                extra2 = abs(x[index+1]-(x_plot[extra_funct_index2]))
                x_plot += ((extra+extra2)/2)  # Secondo adattamento orizzontale
            else:
                x_plot += extra  # Secondo adattamento orizzontale
            index_soglia = np.argmin(abs(y_plot-500))
            x_soglia = x_plot[index_soglia]

            # Aggiunta del valore soglia al dizionario
            if num_chip*10+num_ch not in chips_values:
                chips_values[num_chip*10+num_ch] = [x_soglia]
            else:
                chips_values[num_chip*10+num_ch].append(x_soglia)

        self.draw_dict(chips_values, how_many_chips)

    def read_pathfile(self, how_many, how_many_chips):
        """
        Dato il numero di file da analizzare, restituisce i rispettivi X path.
        Questi vengono filtrati se il valore 'how_many_chips' è diverso da 0,
        in modo da contenere i path relativi ai file con numero di chip
        minore o uguale a 'how_many_chips'.
        """

        try:
            file_path = open('file_path.txt', 'r')
        except:
            print("Errore nella lettura del file")

        list_of_paths = []
        how_many_chips = min(how_many_chips, 259)

        # In caso l'utente specifichi un numero X di chip
        if how_many_chips != 0:
            for _ in range(0, how_many):
                pathfile = file_path.readline().strip()
                chip_string = pathfile.split("/")
                chip_string = chip_string[4].split("_")  # "Chip_001"
                chip_number = int(chip_string[1])  # Trovato il numero del chip

                # Si aggiunge il path solo se il chip è tra i primi X
                if chip_number <= how_many_chips:
                    list_of_paths.append(pathfile)

        # In caso l'utente specifichi un numero X di file
        else:
            for _ in range(0, how_many):
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
        num_chip = int(chip_string[5].split(".")[0])
        num_ch = int(chip_string[1])

        line = f.readline()
        if line.startswith("error") or line.startswith("Non") or line.startswith("Troppi"):
            return 0, 0, 0, 0, 0

        line = line.split()
        soglia_vera = float(line[1])
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
        return x, y, soglia_vera, num_chip, num_ch

    def draw_dict(self, d, how_many_to_draw):
        """
        Funzione per creare un grafico a partire da un dictionary.
        Crea immagini con 9 subplot in modo da ottimizzare i tempi.

        Parametri:
        - d: dictionary da disegnare.
        - how_many_to_draw: numero di chip di cui fare il grafico.

        """

        if (len(d) / 8) < (how_many_to_draw * 8 + 1.4 * len(d)):
            print("d: "+str(len(d))+" how_many_to_draw: "+str(how_many_to_draw))
            print("WARNING: you may required too many chips or too few file to read." +
                  " You may find blank graphs.")

        how_many_to_draw = min(how_many_to_draw, 259)
        print("Processing "+str(how_many_to_draw)+" elements...")
        how_many_to_draw += 1
        how_many_graph = how_many_to_draw // 9
        resto = how_many_to_draw % 9
        how_many_to_draw -= 1

        if resto != 0:
            how_many_graph += 1

        bar = progressbar.ProgressBar(maxval=how_many_to_draw,
                                      widgets=[progressbar.Bar("=", "[", "]"), " ", progressbar.Percentage()])
        bar.start()

        for i in range(1, how_many_to_draw, 9):

            fig, ax = plt.subplots(nrows=3, ncols=3, figsize=(15, 10))
            colors = ['blue', 'yellow', 'darkred', 'magenta',
                      'orange', 'red', 'green', 'lightblue']

            # Itera 9 volte, una per ogni chip in fig
            for num_chip in range(i, 9+i):

                if num_chip > how_many_to_draw:
                    break

                # g è il numero del grafico che si sta disegnando
                g = ((num_chip-1) % 9)

                for ch in range(0, 8):  # Itera 8 volte, una per ogni canale del chip
                    try:
                        x_plot = d[num_chip * 10 + ch]
                    except:
                        #print("chip "+str(num_chip)+" vuoto")
                        ax[g // 3][g % 3].title.set_text(
                            "Chip "+str(num_chip)+" (missing data on some ch)")
                        break
                    y_plot = np.ones(len(x_plot))*500

                    ax[g // 3][g % 3].scatter(x_plot, y_plot,
                                              label="Ch. "+str(ch), marker='o', color=colors[ch])
                    ax[g // 3][g % 3].title.set_text("Chip "+str(num_chip))

            fig.savefig("plot/soglie"+str(i)+".png")
            plt.close(fig)
            bar.update(i)

        bar.finish()

    def sintesi_errori(self):
        """
        Funzione da chiamare in caso si voglia una stima dell'errore totale sui dati.
        La stima è calcolata a partire dalle differenze tra il valore "vero" di soglia letto dai file .txt
        e i valori di soglia trovati con fit lineare e fit con err_function().

        """

        arr_lineare = np.array(self.lista_diff_lineare)
        arr_lineare = arr_lineare[arr_lineare > -100]
        arr_lineare = arr_lineare[arr_lineare < 100]

        media_errori_lineare = np.mean(arr_lineare)
        media_errori_lineare = math.sqrt(media_errori_lineare)
        media_errori_err_funct = np.mean(np.array(self.lista_diff_err))
        media_errori_err_funct = math.sqrt(media_errori_err_funct)

        print("\nIn media, la differenza tra le soglie 'vere' e quelle trovate con il fit lineare è: " +
              str(round(media_errori_lineare, 4)))
        print("In media, la differenza tra le soglie 'vere' e quelle trovate con il fit migliore è: " +
              str(round(media_errori_err_funct, 4))+"\n")
