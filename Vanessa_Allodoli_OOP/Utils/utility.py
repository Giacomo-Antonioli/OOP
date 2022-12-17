import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy.ma as ma
import numpy as np
from scipy import optimize
import scipy.signal as sp
import os.path
from alive_progress import alive_bar
import subprocess
from scipy import special


class Config:

    def __init__(self, dictionary: dict) -> object:
        """
        Costruttore della classe Config. Contiene tutte le informazioni per eseguire l'analisi delle wave form dei moduli SiPM.
        Questa classe viene popolata con le informazioni prese dal file do configurazione JSON nella cartella 'include'.
        :param dictionary: Dizionario generate dal parsing del file condif.json
        :type dictionary: dict
        """
        self.start_time = 0.0
        self.end_time = 0.0
        self.init_time = 0.0
        self.analysis_time = 0.0
        self.peak_time = 0.0
        self.Dcr_time = 0.0
        self.n_points_baseline = dictionary['n_points_baseline']
        self.peak_height = dictionary['peak_height']
        self.peak_prominence = dictionary['peak_prominence']
        self.group_name = dictionary['group_name']
        self.folder_name = dictionary['folder_name']
        self.filenames = dictionary['filenames']

    def print_times(self):
        """
        Funzione di stampa dei tempi di computazione vari della analisi delle waveform dei moduli SiPM.
        """
        print("Tempo inizializzazione: " + str(self.init_time))
        print("Tempo analisi: " + str(self.analysis_time))
        print("Tempo plot picchi: " + str(self.peak_time))
        print("Tempo calcolo DCR: " + str(self.Dcr_time))
        print(f"Total runtime of the program is {self.end_time - self.start_time}")


def read_table_from_file(filename: str, keyword: str) -> pd.DataFrame:
    """
    Funzione che trasforma un file csv in un DataFrame di pands
    :param filename: path del file da convertire
    :type filename:str
    :param keyword: keyword da cercare per discriminare da quale riga del file iniziale a leggere per convertire solo le
     informazioni utili
    :type keyword: str
    :return: Dataframe contenenti i dati letti dal csv
    :rtype: pd.DataFrame
    """
    if not os.path.exists(filename):
        raise FileNotFoundError("File " + filename + "not found")

    file = open(filename)

    # ..con readlines (funzione base di python) ne leggiamo le linee,
    # lines e' una lista di stringhe, ciascuna contenente una linea del file
    file_lines = file.readlines(300 * 8)
    # ..e chiudiamo il file
    file.close()

    line_counter = 0
    # Andiamo a fare un loop sulle linee del file, contenute in lines
    while line_counter != len(file_lines) - 1:
        # Se la linea inizia con "Index", cioe' e' la nostra linea di header
        # ovvero la linea che contiene i nomi delle colonne..
        if file_lines[line_counter].startswith(keyword):
            # procediamo ad creare il DataFrame di pandas, che diamo come output
            return pd.read_csv(filename, header=line_counter)

        line_counter += 1
    # Altrimenti, se non abbiamo trovato la linea di header, diamo un messaggio di errore
    print("Error, header not found!")
    sys.exit(1)


def numberfromstring(string_a: str) -> int:
    """
    Funzione che tasforma un numero letto come stringa  a intero
    :param string_a: numero in input
    :type string_a: str
    :return: numero in output
    :rtype: int
    """
    n = list(string_a)
    number = ''
    for i in n:
        if i.isdigit():
            number += str(i)
    return int(number)


def peak_plot(event: int, wf_time:float, wf_ch: int, bsl_time: float, bsl_ch: int, peaks: float,
              pic_name: str = "Default") -> None:
    """
    Funzione che genera i grafici dei vari picchi trovati per l'evento dato in input
    :param event: event index
    :type event: int
    :param wf_time: Array dei timestamps
    :type wf_time:float
    :param wf_ch: canale dei chip dai quali il wavefront è letto
    :type wf_ch: float
    :param bsl_time: array dei tempi di lettura associati ai vari punti del wavefront
    :type bsl_time: float
    :param bsl_ch: canale del chip dalla quale è letta la baseline
    :type bsl_ch: float
    :param peaks: picchi calcolati con la funzione di scipy.signal find_peaks
    :type peaks: float
    :param pic_name: nome del file di provenienza con cui salvare il grafico
    :type pic_name: str
    """
    # Ora posso plottare tutto:
    fig, ax = plt.subplots()
    plt.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
    # la waveform..
    ax.plot(wf_time, wf_ch, linestyle='-', linewidth=1)
    # ..la baseline..

    # a=input()
    ax.plot(bsl_time, bsl_ch, linestyle='-', linewidth=1, c='darkgreen')
    # ..e i picchi (se ci sono)
    if len(peaks) > 0:
        ax.scatter(wf_time.iloc[peaks], wf_ch.iloc[peaks], c='darkred')
    # Do un nome agli assi..
    ax.set_ylabel('Amplitude (V)')
    ax.set_xlabel('Time (s)')
    # plt.show()
    # ..e salvo il plot in una cartella a parte

    folder_name = './sipm/plot/wf_analysis'
    plot_name = '{0}/{1}_ev{2}.png'.format(folder_name, pic_name, event)
    fig.savefig(plot_name)
    plt.close(fig)


def plot_graphs_DCR_CTR_APR(group_name: str = 'DCR_GRAPH') -> None:
    """
    Funzione che disegna il grafico relativo a: DCR, CTR, APR in relazione a OV.
    Richiede in ingresso il "nome del gruppo", lo stesso che è stato passato alla funzione calculate_dcr().
    :param group_name: Nome del gruppo per il quale si sta generando il grafico (Defalut: DCR_GRAPH)
    :type group_name: str
    """
    colors = {0: "black", 1: "magenta", 2: "green", 3: "orange", 4: "yellow", 5: "red", 6: "blue"}
    legend_labels = {"x1": "DCR", "x2": "CTR", "x3": "APR"}
    i = 0
    fig, ax = plt.subplots()

    with open("dcr_graph_" + group_name + ".txt", "rt") as f:
        lines = f.readlines()  # lines = lista con una riga come elemento

    for l in lines:  # line = dcr, dcr_err, ov, ctr, ctr_err, apr, apr_err
        line = l.split()
        ax.scatter(float(line[2]), float(line[0]), c=colors[i % 7], marker='o', label=legend_labels["x1"])
        ax.errorbar(float(line[2]), float(line[0]), yerr=float(line[1]))
        ax.scatter(float(line[2]), float(line[3]), c=colors[i % 7], marker='1', label=legend_labels["x2"])
        ax.errorbar(float(line[2]), float(line[3]), yerr=float(line[4]))
        ax.scatter(float(line[2]), float(line[5]), c=colors[i % 7], marker='*', label=legend_labels["x3"])
        ax.errorbar(float(line[2]), float(line[5]), yerr=float(line[6]))
        legend_labels["x1"] = "_nolegend_"
        legend_labels["x2"] = "_nolegend_"
        legend_labels["x3"] = "_nolegend_"
        i += 1

    folder_name = './sipm/plot'
    plot_name = '{0}/total_graphs/OV_dcr_{1}.png'.format(folder_name, group_name)
    ax.legend()
    ax.set_xlabel('OV (Hz)')
    ax.set_ylabel('(Hz)')
    fig.savefig(plot_name)
    plt.close(fig)

def find_files():
    """
    Questa funzione esegue il file bash 'analisi_file.sh' che attraverso una find cerca tutti i file nelle da
    caricare eseguendo una ricerca ricorsiva nelle cartelle e sotto cartelle del file path specificato        """
    print("_____________________________")
    dirname = os.getcwd()
    print(dirname)

    try:

        subprocess.call("./Utils/analisi_file.sh")
    except Exception as e:
        print(e)
        print("An error occurred trying to generate path_file.\n" +
              "Please check if you have permission to execute 'analisi_file.sh'.")
