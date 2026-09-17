from __future__ import annotations

from pathlib import Path

import streamlit as st

from lesson_engine import (
    SOCRATIC_QUESTIONS,
    build_report,
    design_torque,
    evaluate_open_answer,
    evaluate_socratic_answer,
    nominal_torque,
)


BASE_DIR = Path(__file__).parent
IMAGE_PATH = BASE_DIR / "assets" / "guida_giunti.png"
VIDEO_PATH = BASE_DIR / "assets" / "lezione_giunti.mp4"

st.set_page_config(
    page_title="Laboratorio sui giunti meccanici",
    page_icon="⚙️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1050px; padding-top: 2rem; padding-bottom: 4rem;}
    .hero {padding: 1.2rem 1.4rem; border-radius: 18px; background: #eef6ff; border: 1px solid #c9def5;}
    .hero h1 {margin: 0 0 .35rem 0; color: #123b5d;}
    .small-note {color: #4b5563; font-size: .92rem;}
    [data-testid="stMetric"] {background: #f8fafc; border: 1px solid #dbe3ea; padding: .8rem; border-radius: 12px;}
    .step-ok {padding: .8rem 1rem; border-left: 5px solid #2e7d32; background: #edf7ee; border-radius: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)


DEFAULTS = {
    "stage": 0,
    "video_done": False,
    "quiz_score": 0,
    "observation_done": False,
    "observation_attempts": 0,
    "calculation_done": False,
    "calculation_attempts": 0,
    "selection_done": False,
    "selection_attempts": 0,
    "socratic_index": 0,
    "socratic_answers": [],
    "socratic_attempts": [0, 0, 0],
    "socratic_hint": "",
    "socratic_model_shown": False,
    "socratic_encouragement": "",
    "socratic_done": False,
    "open_done": False,
    "open_attempts": 0,
    "open_answer_saved": "",
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value.copy() if isinstance(value, list) else value)


def go_to(stage: int) -> None:
    st.session_state.stage = max(st.session_state.stage, stage)


def reset_lesson() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = value.copy() if isinstance(value, list) else value


st.markdown(
    """
    <div class="hero">
      <h1>⚙️ Laboratorio: scegliere un giunto meccanico</h1>
      <p>Osserva, calcola, scegli e motiva. Il percorso cambia quando emerge una difficoltà.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Il tuo percorso")
    labels = ["Introduzione", "Osserva", "Calcola", "Scegli", "Ragiona", "Motiva", "Risultati"]
    progress_index = min(st.session_state.stage, 6)
    st.progress(progress_index / 6 if progress_index else 0)
    st.caption(f"Fase {progress_index + 1} di 7: {labels[progress_index]}")
    for i, label in enumerate(labels):
        symbol = "✅" if i < progress_index else ("▶️" if i == progress_index else "○")
        st.write(f"{symbol} {label}")
    st.divider()
    with st.expander("Ricominciare la lezione"):
        st.warning("Questa azione cancella le risposte della sessione corrente.")
        if st.button("Azzera e ricomincia", type="secondary", use_container_width=True):
            reset_lesson()
            st.rerun()


if st.session_state.stage == 0:
    st.subheader("Obiettivo")
    st.write(
        "Al termine saprai riconoscere le funzioni principali di un giunto, "
        "calcolare la coppia di progetto e motivare una scelta tecnica."
    )
    c1, c2, c3 = st.columns(3)
    c1.info("**1. Osserva**\n\nLeggi un'infografica tecnica.")
    c2.info("**2. Calcola**\n\nUsa potenza, giri e servizio.")
    c3.info("**3. Decidi**\n\nScegli e difendi la soluzione.")
    student_name = st.text_input("Nome dello studente (facoltativo)", key="student_name")
    if st.button("Inizia il percorso", type="primary"):
        go_to(1)
        st.rerun()


elif st.session_state.stage == 1:
    st.subheader("1. Osserva e riconosci")
    if VIDEO_PATH.exists():
        st.video(str(VIDEO_PATH))
        if not st.session_state.video_done:
            st.info("Guarda il video fino alla fine. Poi conferma per aprire l'attività.")
            if st.button("Ho terminato il video", type="primary"):
                st.session_state.video_done = True
                st.rerun()
            st.stop()
    else:
        st.session_state.video_done = True
        st.warning("Video non presente: il percorso prosegue con l'infografica.")
    st.image(str(IMAGE_PATH), caption="Funzioni e tipologie dei giunti di trasmissione")
    with st.form("observation_form"):
        observation = st.radio(
            "Quale affermazione riassume meglio l'immagine?",
            [
                "Tutti i giunti hanno le stesse prestazioni.",
                "Il giunto collega gli alberi e può compensare disallineamenti e vibrazioni.",
                "La funzione principale del giunto è aumentare il numero di giri.",
            ],
            index=None,
        )
        submitted = st.form_submit_button("Controlla la risposta", type="primary")
    if submitted:
        if observation is None:
            st.warning("Scegli una risposta prima di continuare.")
        elif observation.startswith("Il giunto collega"):
            st.success("Corretto. Hai riconosciuto sia la trasmissione sia la protezione del sistema.")
            if not st.session_state.observation_done:
                st.session_state.quiz_score += 1
            st.session_state.observation_done = True
        else:
            st.session_state.observation_attempts += 1
            if st.session_state.observation_attempts >= 3:
                st.info(
                    "Vediamola insieme: il giunto collega gli alberi e può compensare "
                    "disallineamenti e vibrazioni. Ora puoi continuare."
                )
                st.session_state.observation_done = True
            else:
                st.info("Buon tentativo. Osserva le tre funzioni illustrate nella parte sinistra.")
                st.caption(
                    f"Tentativo {st.session_state.observation_attempts}/3 — "
                    "cerca disallineamento, vibrazioni e rigidità torsionale."
                )
    if st.session_state.observation_done and st.button("Continua al calcolo →", type="primary"):
        go_to(2)
        st.rerun()


elif st.session_state.stage == 2:
    st.subheader("2. Simula il funzionamento")
    st.latex(r"M_n = \frac{9550\,P}{n} \qquad M_p = M_n \cdot K_s")
    col1, col2, col3 = st.columns(3)
    power = col1.slider("Potenza P [kW]", 1.0, 100.0, 15.0, 0.5)
    rpm = col2.slider("Velocità n [giri/min]", 100, 3000, 1450, 50)
    service = col3.select_slider("Fattore di servizio Ks", [1.0, 1.2, 1.5, 1.8, 2.0], value=1.5)
    mn = nominal_torque(power, rpm)
    mp = design_torque(power, rpm, service)
    m1, m2 = st.columns(2)
    m1.metric("Coppia nominale", f"{mn:.1f} N·m")
    m2.metric("Coppia di progetto", f"{mp:.1f} N·m", delta=f"+{mp-mn:.1f} N·m di margine")
    st.caption("Modifica i tre parametri e osserva immediatamente come cambia la coppia.")
    with st.form("calculation_form"):
        calc_choice = st.radio(
            "Quale valore devi confrontare con il catalogo per una prima selezione prudente?",
            ["La sola potenza", "La coppia nominale", "La coppia di progetto"],
            index=None,
        )
        calc_submit = st.form_submit_button("Verifica", type="primary")
    if calc_submit:
        if calc_choice == "La coppia di progetto":
            st.success("Corretto: include anche la severità del servizio tramite Ks.")
            if not st.session_state.calculation_done:
                st.session_state.quiz_score += 1
            st.session_state.calculation_done = True
            st.session_state.last_mn = mn
            st.session_state.last_mp = mp
        elif calc_choice is None:
            st.warning("Scegli una risposta.")
        else:
            st.session_state.calculation_attempts += 1
            if st.session_state.calculation_attempts >= 3:
                st.info(
                    "La risposta è la coppia di progetto: comprende la coppia nominale e il "
                    "fattore di servizio Ks. Puoi proseguire."
                )
                st.session_state.calculation_done = True
                st.session_state.last_mn = mn
                st.session_state.last_mp = mp
            else:
                st.info("Sei vicino: cerca il valore che comprende anche la severità del servizio.")
                st.caption(f"Tentativo {st.session_state.calculation_attempts}/3")
    if st.session_state.calculation_done and st.button("Continua alla scelta →", type="primary"):
        go_to(3)
        st.rerun()


elif st.session_state.stage == 3:
    st.subheader("3. Scegli il giunto")
    st.markdown(
        "**Caso tecnico:** due alberi hanno un piccolo disallineamento. Il motore genera vibrazioni "
        "e il carico varia durante il funzionamento."
    )
    with st.form("selection_form"):
        selection = st.radio(
            "Quale soluzione sceglieresti come prima ipotesi?",
            ["Giunto rigido", "Giunto elastico", "Giunto magnetico"],
            index=None,
        )
        selection_submit = st.form_submit_button("Conferma la scelta", type="primary")
    if selection_submit:
        if selection is None:
            st.warning("Scegli una soluzione prima di confermare.")
        else:
            st.session_state.selection_attempts += 1
        if selection == "Giunto elastico":
            st.success("Scelta coerente: tollera piccoli disallineamenti e smorza vibrazioni e picchi.")
            if not st.session_state.selection_done:
                st.session_state.quiz_score += 1
            st.session_state.selection_done = True
        elif selection is not None:
            st.info("La scelta considera una parte del problema. Proviamo a completare il ragionamento.")
            if selection == "Giunto rigido":
                st.info("Un giunto rigido è preciso, ma trasferisce più facilmente disallineamenti e vibrazioni ai cuscinetti.")
            else:
                st.info("Il giunto magnetico è utile per separazione ermetica e assenza di contatto, non è la prima risposta a questo caso.")
            if st.session_state.selection_attempts >= 3:
                st.success(
                    "Per questo caso la prima scelta è il giunto elastico: compensa piccoli "
                    "disallineamenti e smorza le vibrazioni. Ora puoi continuare."
                )
                st.session_state.selection_done = True
    if st.session_state.selection_attempts > 0 and not st.session_state.selection_done:
        st.warning(
            f"Aiuto {st.session_state.selection_attempts}/3: quale componente deformabile può "
            "assorbire parte delle vibrazioni? Cerca l'elemento arancione nell'infografica."
        )
    if st.session_state.selection_done and st.button("Continua al ragionamento →", type="primary"):
        go_to(4)
        st.rerun()


elif st.session_state.stage == 4:
    st.subheader("4. Ragiona come un progettista")
    st.write(
        "Non cercare una parola esatta: collega causa, conseguenza e criterio di scelta. "
        "Se la risposta è incompleta, riceverai una controdomanda invece della soluzione."
    )
    completed = st.session_state.socratic_index
    st.progress(completed / len(SOCRATIC_QUESTIONS))
    st.caption(f"Domande completate: {completed}/{len(SOCRATIC_QUESTIONS)}")
    if st.session_state.socratic_encouragement:
        st.success(st.session_state.socratic_encouragement)

    if completed < len(SOCRATIC_QUESTIONS):
        question = SOCRATIC_QUESTIONS[completed]
        st.markdown(f"**Domanda {completed + 1}:** {question.prompt}")
        response = st.text_area(
            "Costruisci il tuo ragionamento",
            key=f"socratic_response_{completed}",
            height=130,
            placeholder="Secondo me... perché... quindi...",
        )
        attempts = st.session_state.socratic_attempts[completed]
        st.caption(f"Tentativo {min(attempts + 1, 3)} di 3 — sbagliare qui serve a costruire il ragionamento.")
        if st.session_state.socratic_hint:
            st.info("Un aiuto per continuare: " + st.session_state.socratic_hint)
        if st.session_state.socratic_model_shown:
            st.success("Una possibile risposta: " + question.model_answer)
            st.caption("Non devi memorizzarla: confrontala con il tuo ragionamento.")
            if st.button("Ho capito, passa alla domanda successiva →", type="primary"):
                saved = response.strip() or "Nessuna risposta scritta"
                st.session_state.socratic_answers.append(saved + " [risposta guidata]")
                st.session_state.socratic_index += 1
                st.session_state.socratic_hint = ""
                st.session_state.socratic_model_shown = False
                st.session_state.socratic_encouragement = "Hai superato il punto difficile. Continuiamo con calma."
                if st.session_state.socratic_index == len(SOCRATIC_QUESTIONS):
                    st.session_state.socratic_done = True
                st.rerun()
        elif st.button("Esamina il ragionamento", type="primary"):
            accepted = False
            feedback = ""
            if len(response.strip()) >= 20:
                accepted, feedback = evaluate_socratic_answer(response, completed)
            if accepted:
                st.session_state.socratic_answers.append(response.strip())
                st.session_state.socratic_index += 1
                st.session_state.socratic_hint = ""
                st.session_state.socratic_encouragement = feedback
                if st.session_state.socratic_index == len(SOCRATIC_QUESTIONS):
                    st.session_state.socratic_done = True
                st.rerun()
            else:
                st.session_state.socratic_attempts[completed] += 1
                attempts = st.session_state.socratic_attempts[completed]
                if attempts >= 3:
                    st.session_state.socratic_model_shown = True
                    st.session_state.socratic_hint = ""
                else:
                    st.session_state.socratic_hint = question.hints[attempts - 1]
                st.session_state.socratic_encouragement = "Il tentativo è utile: hai ancora spazio per esplorare."
                st.rerun()
    else:
        st.success("Hai completato il dialogo socratico: hai confrontato conseguenze, alternative e dati di progetto.")

    if st.session_state.socratic_answers:
        with st.expander("Rivedi i tuoi ragionamenti"):
            for index, saved_answer in enumerate(st.session_state.socratic_answers, start=1):
                st.markdown(f"**{index}.** {saved_answer}")
    if st.session_state.socratic_done and st.button("Continua alla motivazione finale →", type="primary"):
        go_to(5)
        st.rerun()


elif st.session_state.stage == 5:
    st.subheader("5. Motiva la decisione")
    st.write(
        "Scrivi una breve motivazione tecnica. Spiega il tipo di giunto, i problemi che deve gestire "
        "e quale verifica numerica completerebbe la selezione."
    )
    answer = st.text_area(
        "La tua risposta",
        value=st.session_state.open_answer_saved,
        height=160,
        placeholder="Sceglierei... perché... Verificherei inoltre...",
    )
    if st.button("Ricevi feedback", type="primary"):
        st.session_state.open_attempts += 1
        if len(answer.strip()) < 25:
            st.session_state.open_answer_saved = answer
            if st.session_state.open_attempts < 3:
                st.info("Buon inizio. Aggiungi almeno una causa e una verifica tecnica.")
            else:
                st.session_state.open_done = True
        else:
            st.session_state.open_answer_saved = answer
            st.session_state.open_done = True
    if st.session_state.open_done:
        result = evaluate_open_answer(st.session_state.open_answer_saved)
        st.info(result.feedback)
        st.write(f"**Concetti riconosciuti: {result.score}/{result.max_score}**")
        if result.found:
            st.success("Presenti: " + "; ".join(result.found))
        if result.missing:
            st.warning("Da aggiungere: " + "; ".join(result.missing))
            st.caption("Puoi modificare la risposta e richiedere nuovamente il feedback.")
        if result.score >= 3 and st.button("Vai ai risultati →", type="primary"):
            go_to(6)
            st.rerun()
        elif st.session_state.open_attempts >= 3:
            st.success(
                "Una possibile risposta: sceglierei un giunto elastico perché compensa il "
                "disallineamento e smorza vibrazioni e urti. Verificherei inoltre che la "
                "coppia di progetto sia inferiore a quella ammessa dal catalogo."
            )
            if st.button("Ho capito, vai ai risultati →", type="primary"):
                go_to(6)
                st.rerun()
        else:
            st.caption(
                f"Tentativo {st.session_state.open_attempts}/3: puoi migliorare la risposta; "
                "dopo il terzo tentativo vedrai un esempio completo."
            )


else:
    st.subheader("6. Risultati e relazione")
    mn = st.session_state.get("last_mn", nominal_torque(15, 1450))
    mp = st.session_state.get("last_mp", design_torque(15, 1450, 1.5))
    answer = st.session_state.open_answer_saved
    result = evaluate_open_answer(answer)
    total = st.session_state.quiz_score + result.score
    max_total = 7
    st.markdown('<div class="step-ok"><strong>Percorso completato.</strong> Hai osservato, calcolato, scelto e motivato.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Domande guidate", f"{st.session_state.quiz_score}/3")
    c2.metric("Motivazione", f"{result.score}/4")
    c3.metric("Totale formativo", f"{total}/{max_total}")
    if result.missing:
        st.warning("Prossimo passo consigliato: ripassare " + ", ".join(result.missing) + ".")
    else:
        st.success("La motivazione contiene tutti i criteri attesi.")
    report = build_report(
        st.session_state.get("student_name", "Studente"),
        st.session_state.quiz_score,
        mn,
        mp,
        answer,
        result,
        st.session_state.socratic_answers,
    )
    st.download_button(
        "Scarica la relazione (.txt)",
        data=report,
        file_name="relazione_giunti.txt",
        mime="text/plain",
        type="primary",
    )
    with st.expander("Leggi la relazione"):
        st.text(report)
    st.caption("Il punteggio è formativo: il docente conserva il controllo della valutazione finale.")
