"""Offline operator guide for TestVLD."""

from html import escape

from PyQt5 import QtWidgets

from .dialog_style import POPUP_STYLESHEET


class HelpDialog(QtWidgets.QDialog):
    def __init__(self, parent, psu_host: str, initial_diode_offset: float):
        super().__init__(parent)
        self.setWindowTitle("Aiuto — Guida all'uso")
        self.resize(780, 680)
        self.setMinimumSize(620, 440)
        self.setStyleSheet(POPUP_STYLESHEET)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self.content = QtWidgets.QTextBrowser(self)
        self.content.setOpenExternalLinks(False)
        self.content.setStyleSheet(
            "QTextBrowser { background: #2a2a3d; color: #e2e8f0; "
            "border: 1px solid #3b3b54; border-radius: 8px; padding: 12px; }"
        )
        initial_offset = f"{initial_diode_offset:.2f}".replace(".", ",")
        self.content.setHtml(f"""
            <h1>TestVLD — Guida operatore</h1>
            <p><b>Attenzione alle tensioni di prova, fino a 500 V.</b>
            Utilizzare il banco solo se formati e secondo le procedure aziendali.
            Prima di toccare il dispositivo o cambiare i collegamenti, mettere
            in sicurezza il banco e verificare l'assenza di tensione con strumenti
            idonei. Gli indicatori di connessione, gli stati BLE e un comando
            software di spegnimento <b>non certificano l'assenza di tensione</b>.</p>

            <h2>1. Collegamento al banco</h2>
            <p>All'avvio il programma tenta la connessione all'alimentatore ITech
            all'indirizzo <b>{escape(psu_host)}</b> e avvia la ricerca BLE.
            Controllare gli indicatori PSU e BLE nella barra superiore.
            Se necessario usare <b>Riconnetti</b> e verificare rete, alimentazione
            dei dispositivi e collegamento dell'Arduino.</p>
            <p>Il monitor BLE mostra gli stati dei circuiti del banco.
            Durante le prove AD e AT+AL gli scatti possono essere acquisiti dal
            BLE; i pulsanti <b>Cartellino scattato</b> permettono la registrazione
            manuale. Non registrare manualmente uno scatto già acquisito.</p>

            <h2>2. File Excel e matricola</h2>
            <p>Selezionare il file <b>.xlsx</b> di collaudo e inserire la matricola
            del dispositivo. I pulsanti + e − cambiano la matricola numerica.
            La ricerca avviene nella <b>colonna A del primo foglio</b>; i risultati
            vengono scritti nella stessa riga del <b>quarto foglio</b>.
            Usare quindi il modello Excel previsto, non un foglio vuoto.</p>
            <p>Il riepilogo dei test della matricola indica i risultati già
            presenti nel file. Non sostituisce la lettura degli esiti e degli
            eventuali messaggi di errore. Chiudere il file in Excel prima di
            salvare dal programma, per evitare blocchi in scrittura.</p>

            <h2>3. Caduta di tensione e valore memorizzato</h2>
            <p>Alla prima apertura il campo parte da <b>{initial_offset} V</b>.
            Il valore inserito manualmente viene ricordato per i successivi
            avvii sullo stesso PC, con lo stesso utente. Ogni nuova modifica
            aggiorna il valore memorizzato. Sono accettati sia il punto sia la
            virgola decimale; inserire 0 per non applicare alcuna correzione.</p>
            <p>La dicitura <b>SCR e iTech = 10,55 V</b> è un riferimento:
            <b>non viene applicata automaticamente</b>. Verificare che il valore
            scelto sia appropriato al banco e alla procedura di prova.</p>
            <p>Nel test Innesco Tiristore il dato salvato in <b>colonna H</b> è:</p>
            <p><b>misura grezza − valore del campo Caduta di tensione</b>,
            arrotondato a due decimali.</p>
            <p>Il campo è disponibile anche nella finestra del test, sincronizzato
            con quello in alto. Viene usato il valore corrente al momento del
            calcolo. Il riepilogo riporta l'offset applicato. Cambiarlo non
            modifica la tensione comandata all'alimentatore e non riscrive
            risultati già salvati in Excel.</p>

            <h2>4. Esecuzione delle prove</h2>
            <p>Aprire la prova desiderata, seguire le istruzioni di collegamento
            mostrate nella sua finestra e premere <b>INIZIO TEST</b> solo quando
            il banco è predisposto e l'area di prova è libera.</p>
            <ul>
                <li><b>100 V:</b> misura della corrente; esito positivo sopra 1,9 A.</li>
                <li><b>500 V:</b> misura della corrente; esito positivo fino a 5 mA inclusi.</li>
                <li><b>Anomalia Diodo (AD):</b> rampa di tensione e registrazione
                    dello scatto del cartellino.</li>
                <li><b>AT+AL:</b> registrazione di due scatti; il valore minimo
                    delle due tensioni viene salvato.</li>
                <li><b>Innesco Tiristore:</b> rilevamento automatico del calo di
                    tensione, misura finale e applicazione della correzione
                    impostata. Non richiede un pulsante di scatto manuale.</li>
            </ul>
            <p>I pulsanti <b>Prosegui</b>, quando proposti dopo il salvataggio,
            permettono di passare da AD ad AT+AL e poi a Innesco. Le prove sono
            anche selezionabili singolarmente dalla finestra principale.
            Seguire le indicazioni di riarmo dei cartellini prima della prova successiva.</p>

            <h2>5. Impostazioni e log</h2>
            <p><b>Impostazioni → Tempo step tensione</b> permette di scegliere
            100, 50, 25 o 10 ms per le rampe AD e AT+AL. La selezione è mostrata
            nella barra superiore. Per Innesco l'intervallo resta 100 ms.
            Scegliere l'intervallo prima di avviare la prova.</p>
            <p><b>Impostazioni → Mostra log BLE</b> visualizza le notifiche ricevute
            e i relativi orari, utili per controllare la comunicazione con l'Arduino.</p>

            <h2>6. Salvataggio e problemi comuni</h2>
            <ul>
                <li><b>File o matricola mancanti:</b> il risultato non viene salvato.
                    La matricola deve essere presente nel modello Excel.</li>
                <li><b>Salvataggio completato:</b> controllare il riepilogo dei
                    valori e delle colonne scritte.</li>
                <li><b>Valori fuori range:</b> leggere il messaggio e controllare
                    il foglio; alcune celle valide possono essere già state aggiornate.</li>
                <li><b>Errore di scrittura:</b> verificare che il file non sia
                    aperto in Excel e che il percorso sia accessibile in scrittura.</li>
                <li><b>Errore di connessione o lettura:</b> non considerare la prova
                    valida; mettere in sicurezza il banco prima di intervenire.</li>
            </ul>
            <p>Questa guida descrive il software e non sostituisce la procedura
            di collaudo approvata né le istruzioni di sicurezza del banco.</p>
        """)
        layout.addWidget(self.content)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        close_btn = QtWidgets.QPushButton("Chiudi", self)
        close_btn.setObjectName("close_btn")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)