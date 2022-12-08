from Utils.utility import *


class Simp:

    def __init__(self, filename_wave: str = "Waveform.csv", filename_time: str = "Timestamp.csv") -> None:
        """
        Costruttore della classe SiPM ovvero del Silicon Photomultiplier, è un tipo di fotomoltiplicatore al silicio.
        La classe contiene diversi metodi per analizzare i vari file generati dalla lettura di moduli SiPM.

        :param string filename_wave: Nome del file csv contenente i dati letti dal modulo. Se il parametro non viene fornito
            cerca il File 'Waveform.csv' nella cartella corrente.
        :type filename_wave: str

        :param filename_time: Nome del file csv contente i vari timestamp relativi alle varie letture.Se il parametro
            non viene fornito cerca il File 'Timestamp.csv' nella cartella corrente.
        :type filename_time: str
        """
        try:
            self.wave_front_table = read_table_from_file(filename_wave, 'TIME')
            self.time_table = read_table_from_file(filename_time, 'X: (s)')
        except FileNotFoundError as err:
            print(err.strerror)
            sys.exit(-1)

            # Rinomina le colonne della tabella dei tempi, sostituendole con nomi piu' sensati
        self.time_table.rename(columns={'X: (s)': 'ev', 'Y: (Hits)': 'dt'}, inplace=True)
        # Calcola i punti per waveform e il numero totale di eventi, e li salva nella classe
        self.wave_front_n_points = len(self.wave_front_table) / len(self.time_table)
        self.number_of_events = len(self.time_table)
        # Calcola i tempi assoluti dei singoli trigger dell'oscilloscopio a partire dai Dt
        self.time_table['t'] = np.r_[0, self.time_table['dt'].iloc[1:]].cumsum()
        # Crea un DataFrame (vuoto) per poi salvare i picchi trovati
        self.wave_front_peaks = pd.DataFrame()

    def analyze_ev_wf(self, event, n_bsl, pic_name=None, plot=False, peak_height=0.001, peak_prominences=0.0001,
                      compact=False):

        loop_max = 9 if compact else 1
        peaks_temp = pd.DataFrame()
        if compact:
            fig, ax = plt.subplots(nrows=3, ncols=3)
            fig.text(0.5, 0.01, 'Time (s)', ha='center', va='center')
            fig.text(0.02, 0.5, 'Amplitude (V)', ha='center', va='center', rotation='vertical')
            plt.ticklabel_format(axis='x', style='sci', scilimits=(0, 0))

        for i in range(loop_max):
            if event < len(self.time_table):
                # Creo un np.array con gli indici della singola waveform..
                wf_idx = [event * self.wave_front_n_points, event * self.wave_front_n_points + self.wave_front_n_points]

                # ..i tempi di ciascun punto..
                # a=input()
                wf_time = self.time_table['t'].iloc[event] + self.wave_front_table['TIME'][
                                                             int(wf_idx[0]):int(wf_idx[1])]
                # ..e i valori del segnale di ciascun ppunto
                wf_ch = - \
                    self.wave_front_table['CH1'][int(wf_idx[0]):int(wf_idx[1])]

                # Per trovare la baseline, faccio un fit polinomiale di grado 0..
                # ..su un numero finito di punti iniziali, specificato dall'utente..
                # ..poi la salvo internamente alla classe
                self.baseline = np.polyfit(wf_time[0:n_bsl], wf_ch[0:n_bsl], 0)[0]
                # Voglio anche disegnarla sui plot, quindi mi creo una lista di x e di y..
                # ..nello spazio della waveform
                bsl_ch = [self.baseline] * n_bsl
                bsl_time = wf_time[0:n_bsl]
                # Per trovare i picchi, uso la funzione find_peaks di scipy.signal
                # I valori di height e prominence sono specificati dall'utente..
                # ..e scelti per selezionare tutti i picchi senza prendere rumore
                peaks, _ = sp.find_peaks(wf_ch, height=peak_height, prominence=peak_prominences)

                peaks_temp = pd.concat(
                    [peaks_temp, pd.DataFrame({'t': wf_time.iloc[peaks], 'A': wf_ch.iloc[peaks] - self.baseline})],
                    ignore_index=True)
                if compact:
                    event += 1
                    if plot:
                        ax[int(i / 3)][i % 3].plot(wf_time, wf_ch, linestyle='-', linewidth=1)
                        # ..la baseline..
                        ax[int(i / 3)][i % 3].plot(bsl_time, bsl_ch, linestyle='-', linewidth=1, c='darkgreen')
        if plot:

            peak_plot(event, wf_time, wf_ch, bsl_time, bsl_ch, peaks, pic_name)
            if compact:
                folder_name = './sipm/plot'
                plot_name = '{0}/wf_analysis_compact/{1}_ev{2}.png'.format(folder_name, pic_name, event)
                fig.savefig(plot_name)
                plt.close(fig)

        # La funzione restituisce i valori di tempo e ampiezza (ottenuta come Ch1-baseline)..
        # ..agli indici dei massimi trovati da find_peaks
        return peaks_temp

    def waveform_analyzer(self, n_bsl: int, pic_name: str = None, peak_height: float = 0.001,
                          peak_prominences: float = 0.0001,
                          compact: bool = False,
                          plot: bool = False) -> None:
        """
        Funzione che analizza le waveforms lette dai file in input nel costruttore. Dispone di varie ottimizzazioni per
        decidere se generare i vari grafici e come generarli.

        :param n_bsl: numero di punti della baseline da considerare per le analisi, questo parametro puo' essere modificato nel file do configurazione.
        :type n_bsl: int
        :param pic_name: Nome del file da cui il dato deriva da usare eventualmente come parte del titolo per salvare il relativo grafico. (Default: None)
        :type pic_name: str
        :param peak_height: Valore minimo del picco da trovare nella analisi dei picchi. Vedi: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html (Default: 0.001)
        :type peak_height: float
        :param peak_prominences: Valore minimo del rislato del picco da trovare nella analisi dei picchi. Vedi: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html (Default: 0.0001)
        :type peak_prominences: float
        :param compact: Parametro per decidere se visualizzare i grafici singolarmente (False) oppure in gruppi di 9 (True). (Default: False)
        :type compact: bool
        :param plot: Parametro per decidere se generarei vari plot oppure eseguire sono l'analisi senza visualizzazione. Questo parametro ha priorita' sul parametro 'compact'. (Default: False)
        :type plot: bool
        """
        print("---------------------------------")
        print("Analyzing waveforms to get maxima")
        print("---------------------------------")
        # ToDo: make il more original
        increment = 9 if compact else 1
        with alive_bar(self.number_of_events, bar="bubbles", dual_line=True, title='Analyzing Waveforms') as bar:
            for event in range(0, len(self.time_table['ev']), increment):
                self.wave_front_peaks = pd.concat([self.wave_front_peaks,
                                                   self.analyze_ev_wf(event, n_bsl, pic_name, plot, peak_height,
                                                                      peak_prominences, compact)], ignore_index=True)
                bar(increment)
        print("Events: " + str(len(self.time_table['ev'])))
        print("---------------------------------")
        print("Waveform analysis completed!")
        # Devo ora ricavare di nuovo i Dt dai tempi assoluti, utilizzando la funzione diff()..
        self.wave_front_peaks['dt'] = self.wave_front_peaks['t'].diff()
        # ..e scartando il primo valore (che non ha un Dt)
        self.wave_front_peaks = self.wave_front_peaks.iloc[1:]
        print('Found {:d} peaks in waveforms\n'.format(len(self.wave_front_peaks)))

    def plot_peaks(self, filename: str) -> None:
        """
        Funzione dedita alla generazione e al salvataggio dei picchi rappresentati graficamente tramite uno scatter e un
istogramma. La funzione genera dei pdf.

        :param filename: Path del file per cui plottare i picchi. Esso conterrà piu righe e rappresentera' tanti picchi
            quante sono le righe del file

        :type filename: str
        """
        print("---------------------------------")
        print("Plotting peak amplitudes vs dt")
        print("---------------------------------")

        # Creo una figura dummy (che poi distruggo) per ottenere i valori centrali dei bin di Dt
        fig_dummy, ax_dummy = plt.subplots()

        _, bins, _ = ax_dummy.hist(self.wave_front_peaks['dt'], alpha=0, bins=100)
        plt.close(fig_dummy)

        OV = numberfromstring(filename)

        # Ora creo la figura vera e propria, con rapporto 2:1 tra i plot..
        fig, ax = plt.subplots(2, sharex=True, gridspec_kw={"height_ratios": [2, 1]})
        # ..e scala log sulle x,..
        plt.xscale('log')
        # ..e gli do un titolo
        figure_title = "Dark current plot - OV = " + str(OV - 200)
        ax[0].set_title(figure_title)
        # Comincio con lo scatter plot di amplitude vs Dt in alto
        ax[0].scatter(self.wave_front_peaks['dt'], self.wave_front_peaks['A'], marker='.', facecolors='none',
                      edgecolors='black')
        ax[0].set_xlim([1e-10, 10])
        # ax[0].set_ylim([0, 0.01])
        ax[0].set_ylabel("Amplitudes (V)")
        # Poi creo il binning logaritmico per il plot di Dt..
        log_bins = np.logspace(np.log10(bins[0]), np.log10(bins[-1]), len(bins))
        # ..e il plot stesso
        ax[1].hist(self.wave_front_peaks['dt'], bins=log_bins, histtype='step')
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
        print("Plot saved as: " + fig_name + "\n")

    def calculate_dcr(self, str_OV: str, group_name: str = "DCR_GRAPH") -> None:
        """
        Funzione per calcolare DCR, CTR, APR. Disegna un grafico con i 3 punti.

        :param str_OV: Stringa contenente il valore di OV.
        :type str_OV: str
        :param group_name: Parametro per specifiare il nome del gruppo dal quale i dati derivano per avere una visione piu specifica delle differenze tra gruppi. (Default: DCR_GRAPH).
        :type group_name: str
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
        dcr = len(self.wave_front_peaks[(self.wave_front_peaks['dt'] > 1e-5)])
        dcr_err = np.sqrt(dcr)
        # La rate dei cross-talk sara' uguale al numero di punti a ampiezza superiore a 1 pe..
        ctr = len(self.wave_front_peaks[(self.wave_front_peaks['A'] > 0.01)])
        ctr_err = np.sqrt(ctr)
        # la rate dei after-pulse sara' uguale al numero di punti Dt piccolo..
        apr = len(self.wave_front_peaks[(self.wave_front_peaks['dt'] < 1e-6) & (self.wave_front_peaks['A'] < 0.006)])
        apr_err = np.sqrt(apr)
        # ..divisi per la lunghezza del run..
        # ..che approssimativamente corrisponde al tempo dell'ultimo evento
        run_time = self.wave_front_peaks['t'].iloc[-1]
        dcr = dcr / run_time
        dcr_err = dcr_err / run_time
        ctr = ctr / run_time
        ctr_err = ctr_err / run_time
        apr = apr / run_time
        apr_err = apr_err / run_time
        # Stampo i valori su terminale
        print(r"Dark count rate = {:.2f} +/- {:.2f} s^(-1)".format(dcr, dcr_err))
        print(r"Cross-talk rate = {:.2f} +/- {:.2f} s^(-1)".format(ctr, ctr_err))
        print(r"After-pulse rate = {:.2f} +/- {:.2f} s^(-1)".format(apr, apr_err))

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
        print(os.getcwd())
        folder_name = './sipm/plot'
        plot_name = '{0}/dcr/OV_dcr_{1}.png'.format(folder_name, str_OV)
        fig.savefig(plot_name)
        plt.close(fig)

        with open("dcr_graph_" + group_name + ".txt", "at") as group_file:
            group_file.write(
                str(dcr) + " " + str(dcr_err) + " " + str(OV) + " " + str(ctr) + " " + str(ctr_err) + " " + str(
                    apr) + " " + str(apr_err) + "\n")
