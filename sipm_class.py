import os.path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import progressbar
import scipy.signal as sp


class sipm_wf():

    """
    Come parametri accetta 'filename_wave=' e 'filename_time='.
    In caso non siano forniti, cerca i file 'Waveform.csv' e 'Timestamp.csv' nella stessa cartella.
    """

    # Inizializzatore della classe
    def __init__(self, filename_wave="Waveform.csv", filename_time="Timestamp.csv"):
        # Crea i DataFrame delle due tabelle, ottenute dai rispettivi file
        try:
            self.table_sipm_wf = read_table_sipm(filename_wave, 'TIME')
            self.table_sipm_time = read_table_sipm(filename_time, 'X: (s)')
        except FileNotFoundError as err:
            print(err.strerror)
            sys.exit(-1)

        # Rinomina le colonne della tabella dei tempi, sostituendole con nomi piu' sensati
        self.table_sipm_time.rename(
            columns={'X: (s)': 'ev', 'Y: (Hits)': 'dt'}, inplace=True)
        # Calcola i punti per waveform e il numero totale di eventi, e li salva nella classe
        self.points_per_wf = len(self.table_sipm_wf)/len(self.table_sipm_time)
        self.number_of_events = len(self.table_sipm_time)
        # Calcola i tempi assoluti dei singoli trigger dell'oscilloscopio a partire dai Dt
        self.table_sipm_time['t'] = np.r_[
            0, self.table_sipm_time['dt'].iloc[1:]].cumsum()
        # Crea un DataFrame (vuoto) per poi salvare i picchi trovati
        self.wf_peaks = pd.DataFrame()

    # Questa funzione calcola i picchi e i loro attributi su una singola waveform
    # Richiede il numero dell'evento, e i parametri della ricerca della baseline e dei picchi
    def analyze_ev_wf(self, event, n_bsl, pic_name, peak_height=0.001, peak_prominences=0.0001):

        # Creo un np.array con gli indici della singola waveform..
        wf_idx = [event*self.points_per_wf, event *
                  self.points_per_wf+self.points_per_wf]
        # ..i tempi di ciascun punto..
        wf_time = self.table_sipm_time['t'].iloc[event] + \
            self.table_sipm_wf['TIME'][int(wf_idx[0]):int(wf_idx[1])]
        # ..e i valori del segnale di ciascun ppunto
        wf_ch = - self.table_sipm_wf['CH1'][int(wf_idx[0]):int(wf_idx[1])]

        # Per trovare la baseline, faccio un fit polinomiale di grado 0..
        # ..su un numero finito di punti iniziali, specificato dall'utente..
        # ..poi la salvo internamente alla classe
        self.baseline = np.polyfit(wf_time[0:n_bsl], wf_ch[0:n_bsl], 0)[0]
        # Voglio anche disegnarla sui plot, quindi mi creo una lista di x e di y..
        # ..nello spazio della waveform
        bsl_time = wf_time[0:n_bsl]
        bsl_ch = [self.baseline] * n_bsl

        # Per trovare i picchi, uso la funzione find_peaks di scipy.signal
        # I valori di height e prominence sono specificati dall'utente..
        # ..e scelti per selezionare tutti i picchi senza prendere rumore
        peaks, _ = sp.find_peaks(
            wf_ch, height=peak_height, prominence=peak_prominences)

        # Ora posso plottare tutto:
        fig, ax = plt.subplots()
        plt.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
        # la waveform..
        ax.plot(wf_time, wf_ch, linestyle='-', linewidth=1)
        # ..la baseline..
        ax.plot(bsl_time, bsl_ch, linestyle='-',
                linewidth=1, c='darkgreen')
        # ..e i picchi (se ci sono)
        if len(peaks) > 0:
            ax.scatter(wf_time.iloc[peaks], wf_ch.iloc[peaks], c='darkred')
        # Do un nome agli assi..
        ax.set_ylabel('Amplitude (V)')
        ax.set_xlabel('Time (s)')
        # plt.show()
        # ..e salvo il plot in una cartella a parte
        folder_name = 'plot'
        plot_name = '{0}/{1}_ev{2}.png'.format(
            folder_name, pic_name, event)
        fig.savefig(plot_name)
        plt.close(fig)
        # La funzione restituisce i valori di tempo e ampiezza (ottenuta come Ch1-baseline)..
        # ..agli indici dei massimi trovati da find_peaks
        return wf_time.iloc[peaks], wf_ch.iloc[peaks]-self.baseline

    # Funzione che crea i png con 9 subplot, invece di 1
    def analyze_ev_wf_compact(self, event, n_bsl, pic_name, peak_height=0.001, peak_prominences=0.0001):
        """
        Funzione che analizza le waveform, salva i picchi e salva i png in figure 3x3.
        """

        fig, ax = plt.subplots(nrows=3, ncols=3)
        peaks_temp = pd.DataFrame()

        for i in range(0, 9):
            if event < len(self.table_sipm_time):
                # Creo un np.array con gli indici della singola waveform..
                wf_idx = [event*self.points_per_wf, event *
                          self.points_per_wf+self.points_per_wf]
                # ..i tempi di ciascun punto..
                wf_time = self.table_sipm_time['t'].iloc[event] + \
                    self.table_sipm_wf['TIME'][int(wf_idx[0]):int(wf_idx[1])]
                # ..e i valori del segnale di ciascun ppunto
                wf_ch = - \
                    self.table_sipm_wf['CH1'][int(wf_idx[0]):int(wf_idx[1])]

                # Per trovare la baseline, faccio un fit polinomiale di grado 0..
                # ..su un numero finito di punti iniziali, specificato dall'utente..
                # ..poi la salvo internamente alla classe
                self.baseline = np.polyfit(
                    wf_time[0:n_bsl], wf_ch[0:n_bsl], 0)[0]
                # Voglio anche disegnarla sui plot, quindi mi creo una lista di x e di y..
                # ..nello spazio della waveform
                bsl_time = wf_time[0:n_bsl]
                bsl_ch = [self.baseline] * n_bsl

                # Per trovre i picchi, uso la funzione find_peaks di scipy.signal
                # I valori di height e prominence sono specificati dall'utente..
                # ..e scalti per selezionare tutti i picchi senza prendere rumore
                peaks, _ = sp.find_peaks(
                    wf_ch, height=peak_height, prominence=peak_prominences)

                # Ora posso plottare tutto:
                plt.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
                # la waveform..
                ax[int(i / 3)][i % 3].plot(wf_time,
                                           wf_ch, linestyle='-', linewidth=1)
                # ..la baseline..
                ax[int(i / 3)][i % 3].plot(bsl_time, bsl_ch, linestyle='-',
                                           linewidth=1, c='darkgreen')
                # ..e i picchi (se ci sono)
                if len(peaks) > 0:
                    ax[int(i / 3)][i % 3].scatter(wf_time.iloc[peaks],
                                                  wf_ch.iloc[peaks], c='darkred')

                # Set common labels
                fig.text(0.5, 0.01, 'Time (s)', ha='center', va='center')
                fig.text(0.02, 0.5, 'Amplitude (V)', ha='center', va='center', rotation='vertical')
                
                
                # plt.show()
                peaks_temp = pd.concat([peaks_temp, pd.DataFrame(
                    {'t': wf_time.iloc[peaks], 'A': wf_ch.iloc[peaks]-self.baseline})], ignore_index=True)
                event += 1

        # ..e salvo il plot in una cartella a parte
        folder_name = 'plot'
        plot_name = '{0}/{1}_ev{2}.png'.format(
            folder_name, pic_name, event)
        fig.savefig(plot_name)
        plt.close(fig)

        # La funzione restituisce i valori di tempo e ampiezza (ottenuta come Ch1-baseline)..
        # ..agli indici dei massimi trovati da find_peaks
        return peaks_temp

    # Questa e' la funzione globale che calcola tutti i picchi
    # Voglio che chiami analyze_ev_wf per ogni evento, devo quindi dare in input anche qui i parametri del fit
    def analyze_wfs(self, n_bsl, pic_name, peak_height=0.001, peak_prominences=0.0001, compact=True):
        """
        Funzione originale che calcola i picchi e salva i png di tutte le waveforms.
        """

        print("---------------------------------")
        print("Analyzing waveforms to get maxima")
        print("---------------------------------")

        # Creo una progress bar per rendere piu' fruibile visivamente il programma
        bar = progressbar.ProgressBar(maxval=self.number_of_events,
                                      widgets=[progressbar.Bar("=", "[", "]"), " ", progressbar.Percentage()])
        bar.start()
        counter = 0
        # Ora faccio un loop sugli eventi..
        if compact:
            for event in range(0, len(self.table_sipm_time['ev']), 9):
                # ..e chiamo la funzione analyze_ev_wf per ogni evento
                peaks_dataframe = self.analyze_ev_wf_compact(
                    event, n_bsl, pic_name, peak_height, peak_prominences)

                # I parametri dei picchi sono quindi salvati nella tabella finale dei risultati
                self.wf_peaks = pd.concat(
                    [self.wf_peaks, peaks_dataframe], ignore_index=True)
                bar.update(counter+1)
                counter += 9
        else:
            for event in self.table_sipm_time['ev']:
                # ..e chiamo la funzione analyze_ev_wf per ogni evento
                peaks_time, peaks_ampl = self.analyze_ev_wf(
                    event, n_bsl, pic_name, peak_height, peak_prominences)

                # I parametri dei picchi sono quindi salvati nella tabella finale dei risultati
                self.wf_peaks = pd.concat([self.wf_peaks, pd.DataFrame(
                    {'t': peaks_time, 'A': peaks_ampl})], ignore_index=True)
                bar.update(counter+1)
                counter += 1

        bar.finish()
        print("Events: "+str(len(self.table_sipm_time['ev'])))
        print("---------------------------------")
        print("Waveform analysis completed!")
        # Devo ora ricavare di nuovo i Dt dai tempi assoluti, utilizzando la funzione diff()..
        self.wf_peaks['dt'] = self.wf_peaks['t'].diff()
        # ..e scartando il primo valore (che non ha un Dt)
        self.wf_peaks = self.wf_peaks.iloc[1:]
        print('Found {:d} peaks in waveforms\n'.format(len(self.wf_peaks)))

    # Funzione che fa i plot solo dei grafici significativi, in figure 3x3
    def analyze_wfs_fast(self, n_bsl, pic_name, peak_height=0.001, peak_prominences=0.0001):
        """
        Funzione che fa i plot (png) solo dei grafici più significativi, in figure 3x3
        """

        print("---------------------------------")
        print("Analyzing waveforms to get maxima")
        print("---------------------------------")

        # Creo una progress bar per rendere piu' fruibile visivamente il programma
        bar = progressbar.ProgressBar(maxval=self.number_of_events,
                                      widgets=[progressbar.Bar("=", "[", "]"), " ", progressbar.Percentage()])
        bar.start()
        counter = 0
        fig, ax = plt.subplots(nrows=3, ncols=3)
        peaks_temp = pd.DataFrame()
        num_fig = 0
        # Ora faccio un loop sugli eventi..
        for event in self.table_sipm_time['ev']:

            # Creo un np.array con gli indici della singola waveform..
            wf_idx = [event*self.points_per_wf, event *
                      self.points_per_wf+self.points_per_wf]
            # ..i tempi di ciascun punto..
            wf_time = self.table_sipm_time['t'].iloc[event] + \
                self.table_sipm_wf['TIME'][int(wf_idx[0]):int(wf_idx[1])]
            # ..e i valori del segnale di ciascun ppunto
            wf_ch = - \
                self.table_sipm_wf['CH1'][int(wf_idx[0]):int(wf_idx[1])]

            # Per trovare la baseline, faccio un fit polinomiale di grado 0..
            # ..su un numero finito di punti iniziali, specificato dall'utente..
            # ..poi la salvo internamente alla classe
            self.baseline = np.polyfit(
                wf_time[0:n_bsl], wf_ch[0:n_bsl], 0)[0]
            # Voglio anche disegnarla sui plot, quindi mi creo una lista di x e di y..
            # ..nello spazio della waveform
            bsl_time = wf_time[0:n_bsl]
            bsl_ch = [self.baseline] * n_bsl

            # Per trovre i picchi, uso la funzione find_peaks di scipy.signal
            # I valori di height e prominence sono specificati dall'utente..
            # ..e scalti per selezionare tutti i picchi senza prendere rumore
            peaks, _ = sp.find_peaks(
                wf_ch, height=peak_height, prominence=peak_prominences)

            if len(peaks) > 1:
                # Ora posso plottare tutto:
                plt.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))
                # la waveform..
                ax[int(num_fig / 3)][num_fig % 3].plot(wf_time,
                                                       wf_ch, linestyle='-', linewidth=1)
                # ..la baseline..
                ax[int(num_fig / 3)][num_fig % 3].plot(bsl_time, bsl_ch, linestyle='-',
                                                       linewidth=1, c='darkgreen')
                # ..e i picchi (se ci sono -> ci sono sicuramente, c'è il primo if)
                ax[int(num_fig / 3)][num_fig %
                                     3].scatter(wf_time.iloc[peaks], wf_ch.iloc[peaks], c='darkred')

                # Set common labels
                fig.text(0.5, 0.01, 'Time (s)', ha='center', va='center')
                fig.text(0.02, 0.5, 'Amplitude (V)', ha='center', va='center', rotation='vertical')

                peaks_temp = pd.concat([peaks_temp, pd.DataFrame(
                    {'t': wf_time.iloc[peaks], 'A': wf_ch.iloc[peaks]-self.baseline})], ignore_index=True)
                num_fig += 1

                if num_fig == 9:
                    # ..e salvo il plot in una cartella a parte
                    folder_name = 'plot'
                    plot_name = '{0}/{1}_ev{2}.png'.format(
                        folder_name, pic_name, event)
                    fig.savefig(plot_name)
                    plt.close(fig)
                    fig, ax = plt.subplots(nrows=3, ncols=3)
                    num_fig = 0

            bar.update(counter+1)
            counter += 1

        # I parametri dei picchi sono quindi salvati nella tabella finale dei risultati
        self.wf_peaks = pd.concat(
            [self.wf_peaks, peaks_temp], ignore_index=True)

        # Salvataggio ultima immagine, anche se non sono 9 grafici
        folder_name = 'plot'
        plot_name = '{0}/{1}_ev{2}.png'.format(
            folder_name, pic_name, event)
        fig.savefig(plot_name)
        plt.close(fig)

        bar.finish()
        print("---------------------------------")
        print("Waveform analysis completed!")
        # Devo ora ricavare di nuovo i Dt dai tempi assoluti, utilizzando la funzione diff()..
        self.wf_peaks['dt'] = self.wf_peaks['t'].diff()
        # ..e scartando il primo valore (che non ha un Dt)
        self.wf_peaks = self.wf_peaks.iloc[1:]
        print('Found {:d} peaks in waveforms\n'.format(len(self.wf_peaks)))

    # Funzione che trova i picchi ma non salva i png
    def analyze_wfs_no_png(self, n_bsl, pic_name, peak_height=0.001, peak_prominences=0.0001):
        """
        Funzione che trova i picchi ma non salva i png.
        """

        print("---------------------------------")
        print("Analyzing waveforms to get maxima")
        print("---------------------------------")

        # Creo una progress bar per rendere piu' fruibile visivamente il programma
        bar = progressbar.ProgressBar(maxval=self.number_of_events,
                                      widgets=[progressbar.Bar("=", "[", "]"), " ", progressbar.Percentage()])
        bar.start()
        counter = 0
        peaks_temp = pd.DataFrame()
        num_fig = 0
        print("Events: "+str(len(self.table_sipm_time['ev'])))
        # Ora faccio un loop sugli eventi..
        for event in self.table_sipm_time['ev']:

            # Creo un np.array con gli indici della singola waveform..
            wf_idx = [event*self.points_per_wf, event *
                      self.points_per_wf+self.points_per_wf]
            # ..i tempi di ciascun punto..
            wf_time = self.table_sipm_time['t'].iloc[event] + \
                self.table_sipm_wf['TIME'][int(wf_idx[0]):int(wf_idx[1])]
            # ..e i valori del segnale di ciascun ppunto
            wf_ch = - \
                self.table_sipm_wf['CH1'][int(wf_idx[0]):int(wf_idx[1])]

            # Per trovare la baseline, faccio un fit polinomiale di grado 0..
            # ..su un numero finito di punti iniziali, specificato dall'utente..
            # ..poi la salvo internamente alla classe
            self.baseline = np.polyfit(
                wf_time[0:n_bsl], wf_ch[0:n_bsl], 0)[0]
            # Voglio anche disegnarla sui plot, quindi mi creo una lista di x e di y..
            # ..nello spazio della waveform
            bsl_time = wf_time[0:n_bsl]
            bsl_ch = [self.baseline] * n_bsl

            # Per trovre i picchi, uso la funzione find_peaks di scipy.signal
            # I valori di height e prominence sono specificati dall'utente..
            # ..e scalti per selezionare tutti i picchi senza prendere rumore
            peaks, _ = sp.find_peaks(
                wf_ch, height=peak_height, prominence=peak_prominences)

            peaks_temp = pd.concat([peaks_temp, pd.DataFrame(
                {'t': wf_time.iloc[peaks], 'A': wf_ch.iloc[peaks]-self.baseline})], ignore_index=True)
            bar.update(counter+1)
            counter += 1

        # I parametri dei picchi sono quindi salvati nella tabella finale dei risultati
        self.wf_peaks = pd.concat(
            [self.wf_peaks, peaks_temp], ignore_index=True)

        bar.finish()
        print("---------------------------------")
        print("Waveform analysis completed!")
        # Devo ora ricavare di nuovo i Dt dai tempi assoluti, utilizzando la funzione diff()..
        self.wf_peaks['dt'] = self.wf_peaks['t'].diff()
        # ..e scartando il primo valore (che non ha un Dt)
        self.wf_peaks = self.wf_peaks.iloc[1:]
        print('Found {:d} peaks in waveforms\n'.format(len(self.wf_peaks)))

    # Funzione per plottare i picchi
    def plot_peaks(self, filename):
        """
        Funzione per salvare i picchi in un file pdf con 2 grafici: uno scatter e un istogramma.
        """

        print("---------------------------------")
        print("Plotting peak aplitudes vs dt")
        print("---------------------------------")

        # Creo una figura dummy (che poi distruggo) per ottenere i valori centrali dei bin di Dt
        fig_dummy, ax_dummy = plt.subplots()
        _, bins, _ = ax_dummy.hist(
            self.wf_peaks['dt'], alpha=0, bins=100)
        plt.close(fig_dummy)

        OV = numberfromstring(filename)

        # Ora creo la figura vera e propria, con rapporto 2:1 tra i plot..
        fig, ax = plt.subplots(2, sharex=True, gridspec_kw={
                               "height_ratios": [2, 1]})
        # ..e scala log sulle x,..
        plt.xscale('log')
        # ..e gli do un titolo
        figure_title = "Dark current plot - OV = "+str(OV-200)
        ax[0].set_title(figure_title)
        # Comincio con lo scatter plot di amplitude vs Dt in alto
        ax[0].scatter(self.wf_peaks['dt'], self.wf_peaks['A'],
                      marker='.', facecolors='none', edgecolors='black')
        ax[0].set_xlim([1e-10, 10])
        # ax[0].set_ylim([0, 0.01])
        ax[0].set_ylabel("Amplitudes (V)")
        # Poi creo il binning logaritmico per il plot di Dt..
        log_bins = np.logspace(
            np.log10(bins[0]), np.log10(bins[-1]), len(bins))
        # ..e il plot stesso
        ax[1].hist(self.wf_peaks['dt'], bins=log_bins, histtype='step')
        ax[1].set_yscale('log')
        ax[1].set_ylabel("counts")
        ax[1].set_xlabel(r"$\Delta$t (s)")
        # Aggiungo un paio di comandi per l'espetto
        plt.tight_layout()
        plt.subplots_adjust(hspace=0)
        # plt.show()

        # Infine, salvo il plot sul disco
        fig_name = filename + "_Amplitude_vs_Dt.pdf"
        fig.savefig(fig_name)
        plt.close(fig)
        print("Plot saved as: "+fig_name+"\n")

    # Funzione per stampare su terminale i risultati ottenuti
    def calculate_dcr(self, str_OV, group_name="dcr_graph"):
        """
        Funzione per calcolare DCR, CTR, APR. Disegna un grafico con i 3 punti.
        Richiede come argomenti:
        -OV_string: una stringa che contenga il valore di OV.
        -group_name - opzionale: se si desidera un plot con più valori (di diverse acquisizioni) a confronto,
                    si può specificare un nome per il gruppo di file e il grafico sarà unico.
                    NB: se il nome è già stato usato in precedenza, 
                    i 'vecchi' risultati saranno comunque conservati e sommati
        """

        print("---------------------------------")
        print("Plotting peak aplitudes vs dt")
        print("---------------------------------")
        try:
            OV = numberfromstring(str_OV)
            OV -= 200
        except ValueError:
            print("La stringa contenente il valore di OV non è corretta.")
            sys.exit(-2)

        # La dark count rate sara' uguale al numero di punti a Dt elevata..
        dcr = len(self.wf_peaks[(self.wf_peaks['dt'] > 1e-5)])
        dcr_err = np.sqrt(dcr)
        # La rate dei cross-talk sara' uguale al numero di punti a ampiezza superiore a 1 pe..
        ctr = len(self.wf_peaks[(self.wf_peaks['A'] > 0.01)])
        ctr_err = np.sqrt(ctr)
        # la rate dei after-pulse sara' uguale al numero di punti Dt piccolo..
        apr = len(self.wf_peaks[(self.wf_peaks['dt'] <
                                 1e-6) & (self.wf_peaks['A'] < 0.006)])
        apr_err = np.sqrt(apr)
        # ..divisi per la lunghezza del run..
        # ..che approssimativamente corrisponde al tempo dell'ultimo evento
        run_time = self.wf_peaks['t'].iloc[-1]
        dcr = dcr / run_time
        dcr_err = dcr_err/run_time
        ctr = ctr / run_time
        ctr_err = ctr_err/run_time
        apr = apr/run_time
        apr_err = apr_err/run_time
        # Stampo i valori su terminale
        print(
            r"Dark count rate = {:.2f} +/- {:.2f} s^(-1)".format(dcr, dcr_err))
        print(
            r"Cross-talk rate = {:.2f} +/- {:.2f} s^(-1)".format(ctr, ctr_err))
        print(
            r"After-pulse rate = {:.2f} +/- {:.2f} s^(-1)".format(apr, apr_err))

        fig, ax = plt.subplots(2)
        ax[0].plot(OV, dcr)
        ax[0].errorbar(OV, dcr, yerr=dcr_err, fmt='o')
        ax[0].set_ylabel('DCR')
        ax[0].set_xlabel('OV')

        ax[1].plot(apr, ctr)
        ax[1].errorbar(apr, ctr, yerr=ctr_err, fmt='o')
        ax[1].errorbar(apr, ctr, xerr=apr_err, fmt='o')
        ax[1].set_ylabel('CTR')
        ax[1].set_xlabel('APR')
        folder_name = 'plot'
        plot_name = '{0}/OV_dcr_{1}.png'.format(
            folder_name, str_OV)
        fig.savefig(plot_name)
        plt.close(fig)

        with open("dcr_graph_"+group_name+".txt", "at") as group_file:
            group_file.write(str(dcr)+" "+str(dcr_err)+" "+str(OV)+" "+str(ctr)+" "+str(ctr_err)+" "+str(apr)+" "+str(apr_err)+"\n")

def draw_tot_graphs(group_name):
    """
    Funzione che disegna il grafico relativo a: DCR, CTR, APR in relazione a OV.
    Richiede in ingresso il "nome del gruppo", lo stesso che è stato passato alla funzione calculate_dcr().
    TODO: capire dove va messa sta funzione (dentro la classe o fuori?)
    """
    colors = {0: "black", 1:"magenta", 2: "green", 3: "orange", 4: "yellow", 5: "red", 6: "blue"}
    legend_labels = {"x1" : "DCR", "x2" : "CTR", "x3": "APR"}
    i = 0
    fig, ax = plt.subplots()

    with open("dcr_graph_"+group_name+".txt", "rt") as f:
        lines = f.readlines() #lines = lista con una riga come elemento

    for l in lines: #line = dcr, dcr_err, ov, ctr, ctr_err, apr, apr_err
        line = l.split()
        ax.scatter(float(line[2]), float(line[0]), c=colors[i%7], marker='o', label=legend_labels["x1"])
        ax.errorbar(float(line[2]), float(line[0]), yerr=float(line[1]))
        ax.scatter(float(line[2]), float(line[3]), c=colors[i%7], marker='1', label=legend_labels["x2"])
        ax.errorbar(float(line[2]), float(line[3]), yerr=float(line[4]))
        ax.scatter(float(line[2]), float(line[5]), c=colors[i%7], marker='*', label=legend_labels["x3"])
        ax.errorbar(float(line[2]), float(line[5]), yerr=float(line[6]))
        legend_labels["x1"] = "_nolegend_"
        legend_labels["x2"] = "_nolegend_"
        legend_labels["x3"] = "_nolegend_"
        i += 1

    folder_name = 'plot'
    plot_name = '{0}/OV_dcr_{1}.png'.format(folder_name, group_name)
    ax.legend()
    ax.set_xlabel('OV (Hz)')
    ax.set_ylabel('(Hz)')
    fig.savefig(plot_name)
    plt.close(fig)

# Helper function (ovvero una funzione che aiuta un'altra funzione con un task specifico)..
# ..definita al di fuori della classe
# In questo caso, la funzione apre il file csv, ignorando l'incipit, e restituisce il DataFrame
def read_table_sipm(filename, keyword):

    if not os.path.exists(filename):
        raise FileNotFoundError("File "+filename+"not found")

    file_sipm = open(filename)
    print("ER_read")
    # ..con readlines (funzione base di python) ne leggiamo le linee,
    # lines e' una lista di stringhe, ciascuna contenente una linea del file
    lines = file_sipm.readlines(300*8)
    # ..e chiudiamo il file
    file_sipm.close()

    line_counter = 0
    # Andiamo a fare un loop sulle linee del file, contenute in lines
    while line_counter != len(lines)-1:
        # Se la linea inizia con "Index", cioe' e' la nostra linea di header
        # ovvero la linea che contiene i nomi delle colonne..
        if lines[line_counter].startswith(keyword):
            # procediamo ad creare il DataFrame di pandas, che diamo come output
            return pd.read_csv(filename, header=line_counter)

        line_counter += 1
    # Altrimenti, se non abbiamo trovato la linea di header, diamo un messaggio di errore
    print("Error, header not found!")
    sys.exit(1)

def numberfromstring(string_a):
    n = list(string_a)
    number = ''
    for i in n:
        if i.isdigit():
            number += str(i)
    return int(number)
