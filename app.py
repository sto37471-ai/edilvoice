import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI
import io

# ==========================================
# 1. CONFIGURAZIONE
# ==========================================
MODALITA_PRODUZIONE = False 
API_KEY_OPENAI = "LA_TUA_CHIAVE_API_OPENAI" 
SIMULA_AI = True 

client = OpenAI(api_key=API_KEY_OPENAI)
users_db = {"demo@edilvoice.com": {"password": "demo", "nome": "Mario Rossi"}}

# ==========================================
# 2. LOGICA & FUNZIONI
# ==========================================

def calcola_riga(prezzo_acq, ricarico, qta, iva_pct):
    prezzo_vendita_u = prezzo_acq * (1 + ricarico/100)
    totale = prezzo_vendita_u * qta
    iva = totale * (iva_pct / 100)
    guadagno = (prezzo_vendita_u - prezzo_acq) * qta
    return round(prezzo_vendita_u, 2), round(totale, 2), round(iva, 2), round(guadagno, 2)

def genera_documento_html(profilo, dati_lavoro, voci_costi):
    """Genera Preventivo Ufficiale con TUTTI i Dati"""
    data_oggi = datetime.now().strftime("%d/%m/%Y")
    
    if not voci_costi.empty: 
        totale_imponibile = voci_costi['Totale Vendita (€)'].sum()
        iva_valore = totale_imponibile * (profilo['IVA Standard (%)'] / 100)
        totale_ivato = totale_imponibile + iva_valore
    else: 
        totale_imponibile = 0; iva_valore = 0; totale_ivato = 0
    
    html = f"""
    <html><head><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Helvetica', sans-serif; margin: 40px; color: #333; line-height: 1.4; }}
        .header {{ text-align: center; border-bottom: 3px solid #000; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 38px; color: #000; text-transform: uppercase; letter-spacing: 3px; font-weight: bold; }}
        .header p {{ font-size: 14px; color: #555; margin: 5px 0; }}
        
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-bottom: 30px; }}
        .info-box h3 {{ margin-top: 0; border-bottom: 1px solid #ccc; padding-bottom: 5px; font-size: 16px; color: #000; margin-bottom: 10px; text-transform: uppercase; font-weight: bold; }}
        .info-box p {{ margin: 4px 0; font-size: 13px; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 13px; }}
        th {{ background-color: #004d40; color: white; border: 1px solid #000; padding: 10px; text-align: left; font-weight: bold; }}
        td {{ border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }}
        
        .totals {{ display: flex; justify-content: flex-end; flex-direction: column; align-items: flex-end; margin-top: 20px; }}
        .row {{ display: flex; justify-content: space-between; width: 320px; margin-bottom: 5px; font-size: 14px; }}
        .total {{ font-size: 22px; font-weight: bold; border-top: 2px solid #000; padding-top: 10px; margin-top: 10px; width: 320px; color: #000; }}
        
        .footer {{ margin-top: 60px; border-top: 1px solid #000; padding-top: 20px; font-size: 11px; color: #777; text-align: center; }}
        .payment {{ text-align: right; margin-bottom: 20px; font-weight: bold; font-size: 13px; }}
    </style></head><body>
    
    <div class="header">
        <h1>PREVENTIVO</h1>
        <p>Data: {data_oggi} | N. {dati_lavoro['ID Lavoro']}</p>
        <p>Di: <b>{profilo['Nome Ditta']}</b> | P.IVA: {profilo['Partita IVA']} | C.F.: {profilo['Codice Fiscale']}</p>
        <p>{profilo['Sede Legale']} | Tel: {profilo['Telefono Cellulare']} | {profilo['Email Professionale']}</p>
    </div>

    <div class="info-grid">
        <div class="info-box">
            <h3>Spettabile</h3>
            <p><b>Nome:</b> {dati_lavoro['Nome Cliente']}</p>
            <p><b>Indirizzo Cantiere:</b> {dati_lavoro['Indirizzo Cantiere']}</p>
            <p><b>Tel/WhatsApp:</b> {dati_lavoro.get('Telefono/WhatsApp', '-')}</p>
            <p><b>Email:</b> {dati_lavoro.get('Email Cliente', '-')}</p>
        </div>
        <div class="info-box">
            <h3>Dettagli Lavoro</h3>
            <p><b>Titolo:</b> {dati_lavoro['Titolo Lavoro']}</p>
            <p><b>Stato:</b> {dati_lavoro['Stato Avanzamento']}</p>
            <p><b>Priorità:</b> {dati_lavoro.get('Priorità', 'Normale')}</p>
            <p><b>Scadenza:</b> {dati_lavoro.get('Scadenza Preventivo', '-')}</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th width="45%">Descrizione</th>
                <th width="10%" style="text-align: center;">Q.tà</th>
                <th width="20%">Fornitore</th>
                <th width="12%" style="text-align: right;">Prezzo Un.</th>
                <th width="13%" style="text-align: right;">Totale</th>
            </tr>
        </thead>
        <tbody>
    """
    
    if not voci_costi.empty:
        for _, row in voci_costi.iterrows():
            html += f""" 
                <tr> 
                    <td>{row['Descrizione']}</td> 
                    <td style="text-align: center;">{row['Quantità']}</td> 
                    <td>{row.get('Fornitore', '-')}</td> 
                    <td style="text-align: right;">€ {row['Prezzo Vendita (€)']:.2f}</td> 
                    <td style="text-align: right;">€ {row['Totale Vendita (€)']:.2f}</td> 
                </tr> 
             """
    else:
        html += "<tr><td colspan='5' style='text-align: center; padding: 20px; color: #999;'>Nessuna voce inserita</td></tr>"

    html += f"""
        </tbody>
    </table>

    <div class="totals">
        <div class="row"><span>Imponibile:</span> <span>€ {totale_imponibile:.2f}</span></div>
        <div class="row"><span>IVA ({profilo['IVA Standard (%)']}%):</span> <span>€ {iva_valore:.2f}</span></div>
        <div class="total"><span>TOTALE:</span> <span>€ {totale_ivato:.2f}</span></div>
    </div>

    <div class="payment">
        <p>Pagamento a: {profilo['Nome Ditta']}</p>
        <p>Modalità: Bonifico Bancario</p>
        <p>IBAN: {profilo['IBAN']}</p>
        <p>PEC: {profilo['PEC / Codice Univoco']}</p>
    </div>

    <div class="footer">
        <p>{profilo.get('Note Piè di Pagina', '')}</p>
        <p>Certificazioni: {profilo.get('Certificazioni', '-')}</p>
        <center>Preventivo generato da EdilVoice Pro</center>
    </div>
    </body></html>
    """
    return html

def process_ai_command(text):
    if SIMULA_AI:
        text_lower = text.lower()
        if "nuovo" in text_lower: return {"azione": "nuovo_lavoro", "cliente": "Cliente Vocale"}
        if "apri" in text_lower: return {"azione": "apri_lavoro", "cliente": "Cliente Vocale"}
        return {"azione": "aggiungi_voce"}
    return {"azione": "errore"}

# ==========================================
# 3. INTERFACCIA (STREAMLIT)
# ==========================================
st.set_page_config(page_title="EdilVoice Pro", layout="wide")

# CSS TASTO ROSSO
st.markdown("""
<style>
@keyframes pulse-red {
    0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7); }
    70% { transform: scale(1.05); box-shadow: 0 0 0 20px rgba(255, 75, 75, 0); }
    100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
}

/* IL CERCHIO ROSSO */
div[data-testid="stAudioInput"] {
    width: 350px !important;
    height: 350px !important;
    border-radius: 50% !important;
    background: radial-gradient(circle, #ff4b4b 0%, #b30000 100%);
    margin: 40px auto;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border: 8px solid white;
    animation: pulse-red 2s infinite;
}

/* SCRITTA "PREMI" */
div[data-testid="stAudioInput"] label {
    color: white !important;
    font-size: 28px !important;
    font-weight: bold !important;
    text-transform: uppercase;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    margin-bottom: 20px !important;
}

/* IL WIDGET ORIGINALE (Rendiamolo grande ma cliccabile) */
div[data-testid="stAudioInput"] > div {
    background-color: white !important;
    border-radius: 30px !important;
    width: 90% !important;
    /* Non mettiamo pointer-events: none qui, altrimenti il click non passa */
}

/* Rimuove icone doppie */
div[data-testid="stAudioInput"] label::after {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# --- INIT SESSIONE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# PROFILO COMPLETO (TUTTE LE COLONNE EXCEL)
if 'profilo' not in st.session_state: 
    st.session_state.profilo = {
        "Nome Ditta": "EDILVOICE CO.", 
        "Partita IVA": "123456789", 
        "Codice Fiscale": "AAABBB00A00A000A",
        "Sede Legale": "Via Roma 10", 
        "PEC / Codice Univoco": "abcdefg@pec.it",
        "IBAN": "IT00 X000 0000 0000 0000 0000 00", 
        "Telefono Cellulare": "3331234567", 
        "Email Professionale": "info@edilvoice.it",
        "Tariffa Oraria (€/h)": 35.0, 
        "Ricarico Materiali (%)": 20.0, 
        "IVA Standard (%)": 22.0,
        "Note Piè di Pagina": "",
        "Certificazioni": ""
    }

if 'lista_lavori' not in st.session_state: 
    st.session_state.lista_lavori = pd.DataFrame(columns=["ID Lavoro", "Nome Cliente", "Titolo Lavoro", "Stato Avanzamento", "Priorità", "Telefono/WhatsApp", "Email Cliente", "Indirizzo Cantiere", "Data Sopralluogo", "Scadenza Preventivo", "Totale Imponibile", "Totale IVA", "Totale Ivato"])

if 'dettaglio' not in st.session_state: 
    st.session_state.dettaglio = pd.DataFrame(columns=["ID Lavoro", "Categoria", "Descrizione", "Fornitore", "Quantità", "Prezzo Acquisto (€)", "Ricarico (%)", "Prezzo Vendita (€)", "IVA (%)", "Totale Vendita (€)", "Guadagno Netto (€)", "Stato Prezzo"])

if 'listino' not in st.session_state:
    st.session_state.listino = pd.DataFrame(columns=["Codice", "Descrizione", "Prezzo Acquisto (€)"])

if 'current_client' not in st.session_state: st.session_state.current_client = None
if 'current_id' not in st.session_state: st.session_state.current_id = None

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("🏗️ LOGIN EDILVOICE PRO")
    u = st.text_input("Email (demo@edilvoice.com)")
    p = st.text_input("Password (demo)", type="password")
    if st.button("ENTRA", type="primary", use_container_width=True):
        if u == "demo@edilvoice.com" and p == "demo":
            st.session_state.logged_in = True
            if st.session_state.lista_lavori.empty:
                st.session_state.lista_lavori.loc[0] = ["1000", "Studio Shodwe", "Ristrutturazione", "In Corso", "Alta", "3331112222", "info@shodwe.com", "Via Roma 1", "01/01/2024", "01/02/2024", 1000, 220, 1220]
                st.session_state.dettaglio.loc[0] = ["1000", "Manodopera", "Smaltimento Rifiuti", "EcoSrl", 1, 100, 20, 120, 22, 120, 20, "Definitivo"]
            st.rerun()
        else: st.error("Credenziali errate")
    st.stop()

# --- 2. PRIMO LOGIN (SETUP COMPLETO) ---
if st.session_state.profilo.get("Nome Ditta") == "EDILVOICE CO.":
    st.title("⚙️ CONFIGURAZIONE COMPLETA DITTA")
    st.warning("Compila tutti i campi della tua ditta per generare correttamente i preventivi.")
    
    with st.form("setup_completo"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ditta = st.text_input("Nome Ditta", value="EdilVoice Co.")
            piva = st.text_input("Partita IVA", value="123456789")
            cf = st.text_input("Codice Fiscale", value="AAABBB00A00A000A")
            sede = st.text_input("Sede Legale", value="Via Roma 10")
            tel = st.text_input("Telefono Cellulare", value="3331234567")
        with col2:
            pec = st.text_input("PEC / Codice Univoco", value="abcdefg@pec.it")
            email = st.text_input("Email Professionale", value="info@edilvoice.it")
            iban = st.text_input("IBAN", value="IT00 X000 0000 0000 0000 0000 00")
            
            tar = st.number_input("Tariffa Oraria (€/h)", value=35.0)
            ric = st.number_input("Ricarico Materiali (%)", value=20.0)
            iva = st.number_input("IVA Standard (%)", value=22.0)
        with col3:
            note = st.text_area("Note Piè di Pagina", value="")
            cert = st.text_input("Certificazioni", value="ISO 9001")
        
        if st.form_submit_button("💾 SALVA TUTTO E INIZIA", type="primary", use_container_width=True):
            st.session_state.profilo = {
                "Nome Ditta": ditta, "Partita IVA": piva, "Codice Fiscale": cf, "Sede Legale": sede,
                "PEC / Codice Univoco": pec, "IBAN": iban, "Telefono Cellulare": tel, "Email Professionale": email,
                "Tariffa Oraria (€/h)": tar, "Ricarico Materiali (%)": ric, "IVA Standard (%)": iva,
                "Note Piè di Pagina": note, "Certificazioni": cert
            }
            st.toast("Dati Salvati!")
            st.rerun()
    st.stop()

# --- SIDEBAR: ARCHIVI (3 TABBED) ---
with st.sidebar:
    st.title("📂 GESTIONE AZIENDA")
    tab_archivio, tab_listini, tab_profilo = st.tabs(["📋 Preventivi", "📦 Listini", "⚙️ Profilo"])
    
    #TAB1
    with tab_archivio:
        # 1. SELEZIONA CLIENTE
        st.subheader("👤 1. Seleziona Cliente")
        if not st.session_state.lista_lavori.empty:
            lista_clienti = sorted(st.session_state.lista_lavori['Nome Cliente'].unique().tolist())
            cliente_scelto = st.selectbox("Scegli il cliente:", options=lista_clienti, key="sel_cliente_sidebar")
            st.session_state.current_client = cliente_scelto

            st.divider()

            # 2. SELEZIONA LAVORO (Filtrato per il cliente sopra)
            st.subheader("🏗️ 2. Seleziona Lavoro")
            df_lavori_cliente = st.session_state.lista_lavori[st.session_state.lista_lavori['Nome Cliente'] == cliente_scelto]
            
            if not df_lavori_cliente.empty:
                opzioni_lavori = [f"{r['ID Lavoro']} - {r['Titolo Lavoro']}" for _, r in df_lavori_cliente.iterrows()]
                lavoro_scelto = st.selectbox("Scegli il cantiere:", options=opzioni_lavori, key="sel_lavoro_sidebar")
                st.session_state.current_id = lavoro_scelto.split(" - ")[0]
                
                st.divider()

                # 3. MODIFICA DATI
                st.subheader("📝 3. Modifica Dati Cliente")
                edited_lavori = st.data_editor(
                    df_lavori_cliente, 
                    use_container_width=True, 
                    num_rows="dynamic", 
                    key="editor_filtrato",
                    hide_index=True
                )

                if not edited_lavori.equals(df_lavori_cliente):
                    # Recuperiamo il vecchio ID prima che venga sovrascritto
                    vecchio_id = st.session_state.current_id
                    
                    # 1. Aggiorniamo l'archivio generale
                    # Prendiamo tutti i lavori tranne quelli del cliente che stiamo modificando
                    altri_lavori = st.session_state.lista_lavori[st.session_state.lista_lavori['Nome Cliente'] != st.session_state.current_client]
                    # Uniamo i lavori non toccati con quelli modificati nella tabella
                    st.session_state.lista_lavori = pd.concat([altri_lavori, edited_lavori], ignore_index=True)
                    
                    # 2. SE HAI CAMBIATO L'ID: aggiorniamo i materiali collegati
                    # Prendiamo il nuovo ID dalla prima riga della tabella modificata
                    nuovo_id = str(edited_lavori.iloc[0]['ID Lavoro'])
                    
                    if nuovo_id != vecchio_id:
                        # Cambia l'ID in tutte le voci di costo nel database 'dettaglio'
                        st.session_state.dettaglio.loc[st.session_state.dettaglio['ID Lavoro'] == vecchio_id, 'ID Lavoro'] = nuovo_id
                        # Aggiorna l'ID attivo nella sessione
                        st.session_state.current_id = nuovo_id
                    
                    # 3. SE HAI CAMBIATO IL NOME: aggiorna il puntatore cliente
                    nuovo_nome = edited_lavori.iloc[0]['Nome Cliente']
                    st.session_state.current_client = nuovo_nome

                    st.rerun()
            else:
                st.info("Nessun lavoro trovato per questo cliente.")
        else:
            st.info("L'archivio è vuoto.")

    # TAB 2: LISTINI
    with tab_listini:
        st.subheader("1. Carica Foto Listino (OCR)")
        uploaded = st.file_uploader("Carica Foto", type=['jpg'])
        if uploaded: st.success("Analisi simulata")
        
        st.divider()
        st.subheader("2. Aggiungi Manuale")
        with st.form("add_prod"):
            cod = st.text_input("Codice")
            desc = st.text_input("Descrizione")
            pr = st.number_input("Prezzo Acq.", value=0.0)
            if st.form_submit_button("Aggiungi"):
                st.session_state.listino.loc[len(st.session_state.listino)] = [cod, desc, pr]
                st.rerun()
        
        st.subheader("Database")
        st.dataframe(st.session_state.listino, use_container_width=True, height=250)

    # TAB 3: PROFILO (MODIFICA)
    with tab_profilo:
        st.subheader("⚙️ Impostazioni Complete Ditta")
        
        # Carichiamo tutti i campi attuali per permettere la modifica
        col1, col2 = st.columns(2)
        with col1:
            n_ditta = st.text_input("Nome Ditta", st.session_state.profilo.get("Nome Ditta"))
            n_piva = st.text_input("Partita IVA", st.session_state.profilo.get("Partita IVA"))
            n_cf = st.text_input("Codice Fiscale", st.session_state.profilo.get("Codice Fiscale"))
            n_sede = st.text_input("Sede Legale", st.session_state.profilo.get("Sede Legale"))
            n_tel = st.text_input("Telefono", st.session_state.profilo.get("Telefono Cellulare"))
        
        with col2:
            n_pec = st.text_input("PEC / Univoco", st.session_state.profilo.get("PEC / Codice Univoco"))
            n_email = st.text_input("Email Prof.", st.session_state.profilo.get("Email Professionale"))
            n_iban = st.text_input("IBAN", st.session_state.profilo.get("IBAN"))
            n_tar = st.number_input("Tariffa Oraria (€/h)", value=float(st.session_state.profilo.get("Tariffa Oraria (€/h)", 35.0)))
            n_ric = st.number_input("Ricarico (%)", value=float(st.session_state.profilo.get("Ricarico Materiali (%)", 20.0)))
            n_iva = st.number_input("IVA (%)", value=float(st.session_state.profilo.get("IVA Standard (%)", 22.0)))

        n_note = st.text_area("Note Piè di Pagina", st.session_state.profilo.get("Note Piè di Pagina", ""))
        
        st.divider()
        
        # Sezione Conferma
        st.warning("Inserisci la password per salvare")
        conf_pwd = st.text_input("Password Amministratore", type="password", key="p_sidebar")
        
        if st.button("💾 SALVA TUTTE LE IMPOSTAZIONI", type="primary", use_container_width=True):
            if conf_pwd == "demo": # Qui puoi mettere la tua password
                st.session_state.profilo.update({
                    "Nome Ditta": n_ditta, "Partita IVA": n_piva, "Codice Fiscale": n_cf,
                    "Sede Legale": n_sede, "Telefono Cellulare": n_tel, "PEC / Codice Univoco": n_pec,
                    "Email Professionale": n_email, "IBAN": n_iban, "Tariffa Oraria (€/h)": n_tar,
                    "Ricarico Materiali (%)": n_ric, "IVA Standard (%)": n_iva, "Note Piè di Pagina": n_note
                })
                st.success("✅ Tutte le voci sono state aggiornate!")
                st.rerun()
            else:
                st.error("❌ Password non corretta")

# --- MAIN AREA ---
st.title("🎤 CANTIERE VOCALE")

# Info Stato
c1, c2 = st.columns(2)
with c1: st.info(f"👤 {st.session_state.current_client}" if st.session_state.current_client else "Nessuno")
with c2: st.success(f"📋 {st.session_state.current_id}" if st.session_state.current_id else "Nessuno")

# 1. PULSANTE AUDIO
st.markdown("### 1. Registra (Clicca il cerchio rosso)")
audio = st.audio_input("🎤 PREMI QUI", key="mic")

if audio:
    st.info("👂 Elaborazione...")
    if st.session_state.lista_lavori.empty:
        res = {"azione": "nuovo_lavoro", "cliente": "Cliente Prova", "titolo": "Lavoro"}
    elif st.session_state.current_id is None:
        res = {"azione": "apri_lavoro", "cliente": st.session_state.lista_lavori.iloc[0]['Nome Cliente']}
    else:
        res = {"azione": "aggiungi_voce"}

    if res["azione"] == "nuovo_lavoro":
        new_id = 1000 + len(st.session_state.lista_lavori)
        r = {"ID Lavoro": new_id, "Nome Cliente": res['cliente'], "Titolo Lavoro": res['titolo'], "Indirizzo Cantiere": ""}
        st.session_state.lista_lavori = pd.concat([st.session_state.lista_lavori, pd.DataFrame([r])], ignore_index=True)
        st.session_state.current_client = res['cliente']
        st.session_state.current_id = new_id
        st.toast("Creato"); st.rerun()
    elif res["azione"] == "aggiungi_voce":
        if st.session_state.current_id:
            p, tot, iva_v, guad = calcola_riga(100, 20, 1, 22)
            r = {
                "ID Lavoro": st.session_state.current_id, 
                "Categoria": "Generale",
                "Descrizione": "Nuova Voce", 
                "Quantità": 1, 
                "Prezzo Acquisto (€)": 100,
                "Ricarico (%)": 20,
                "Prezzo Vendita (€)": p, 
                "IVA (%)": 22,
                "Totale Vendita (€)": tot, 
                "Guadagno Netto (€)": guad,
                "Stato Prezzo": "Definitivo"
            }
            st.session_state.dettaglio = pd.concat([st.session_state.dettaglio, pd.DataFrame([r])], ignore_index=True)
            st.toast("Voce Aggiunta!"); st.rerun()

st.divider()

# 2. GENERA PREVENTIVO  
# 2. GENERA PREVENTIVO (Copia da qui...)
if st.session_state.current_id:
    if st.button("🖨️ GENERA PREVENTIVO FINALE", type="primary", use_container_width=True):
        # Definiamo la variabile dentro il click del bottone
        lavoro_sel = st.session_state.lista_lavori[st.session_state.lista_lavori['ID Lavoro'] == st.session_state.current_id]
        
        if not lavoro_sel.empty:
            dati_lavoro = lavoro_sel.iloc[0]
            voci_lavoro = st.session_state.dettaglio[st.session_state.dettaglio["ID Lavoro"] == st.session_state.current_id]
            
            # Genera l'HTML (Assicurati che la funzione nasconda il guadagno come detto prima)
            st.session_state.current_doc = genera_documento_html(st.session_state.profilo, dati_lavoro, voci_lavoro)
            st.rerun()

# Visualizzazione (Sposta questo fuori dal pulsante ma sotto di esso)
if 'current_doc' in st.session_state:  
    st.divider()
    st.subheader("📄 Anteprima Documento")  
    st.components.v1.html(st.session_state.current_doc, height=600, scrolling=True)  
    
    html_bytes = st.session_state.current_doc.encode('utf-8')  
    st.download_button(
        label="⬇️ SCARICA PREVENTIVO (HTML)", 
        data=html_bytes, 
        file_name=f"Preventivo_{st.session_state.current_id}.html", 
        mime="text/html", 
        use_container_width=True
    )

# 3. TABELLA DETTAGLIO
if st.session_state.current_id:
    st.subheader(f"📝 Modifica Voci Preventivo {st.session_state.current_id}")
    
    # Recuperiamo solo le voci di questo preventivo
    df_voci = st.session_state.dettaglio[st.session_state.dettaglio["ID Lavoro"] == st.session_state.current_id]
    
    # Visualizziamo la tabella MODIFICABILE
    edited_voci = st.data_editor(df_voci, use_container_width=True, hide_index=True, key="edit_voci_main")
    
    # Se scrivi qualcosa nella tabella, il sistema salva le modifiche
    if not edited_voci.equals(df_voci):
        altre_voci = st.session_state.dettaglio[st.session_state.dettaglio["ID Lavoro"] != st.session_state.current_id]
        st.session_state.dettaglio = pd.concat([altre_voci, edited_voci], ignore_index=True)
        st.rerun()