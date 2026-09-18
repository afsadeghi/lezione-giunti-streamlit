"""Logica didattica indipendente dall'interfaccia Streamlit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class OpenAnswerResult:
    score: int
    max_score: int
    found: tuple[str, ...]
    missing: tuple[str, ...]
    feedback: str


@dataclass(frozen=True)
class SocraticQuestion:
    prompt: str
    groups: tuple[tuple[str, ...], ...]
    hints: tuple[str, str]
    model_answer: str
    confirmation: str


@dataclass(frozen=True)
class CouplingDesignInput:
    """Requisiti essenziali per un primo confronto tra famiglie di giunti."""

    power_kw: float
    rpm: int
    service_factor: float
    misalignment: str
    vibrations: str
    load: str
    precision: str
    environment: str


@dataclass(frozen=True)
class CouplingRecommendation:
    """Esito trasparente di una preselezione didattica, non sostitutiva del catalogo."""

    family: str
    nominal_torque: float
    design_torque: float
    scores: tuple[tuple[str, int], ...]
    reasons: tuple[str, ...]
    principal_risk: str
    checks: tuple[str, ...]


def nominal_torque(power_kw: float, rpm: int) -> float:
    """Calcola la coppia nominale in N·m: M = 9550 P / n."""
    if power_kw <= 0:
        raise ValueError("La potenza deve essere maggiore di zero.")
    if rpm <= 0:
        raise ValueError("Il numero di giri deve essere maggiore di zero.")
    return 9550.0 * power_kw / rpm


def design_torque(power_kw: float, rpm: int, service_factor: float) -> float:
    """Calcola la coppia di progetto applicando il fattore di servizio."""
    if service_factor < 1:
        raise ValueError("Il fattore di servizio non può essere minore di 1.")
    return nominal_torque(power_kw, rpm) * service_factor


def recommend_coupling(data: CouplingDesignInput) -> CouplingRecommendation:
    """Confronta quattro famiglie con regole esplicite e restituisce la prima ipotesi.

    La funzione serve per allenare il ragionamento progettuale. La selezione definitiva
    richiede sempre dati dimensionali, catalogo del costruttore e verifiche applicabili.
    """

    allowed = {
        "misalignment": {"Nullo", "Piccolo", "Medio"},
        "vibrations": {"Basse", "Medie", "Alte"},
        "load": {"Uniforme", "Variabile", "Con urti"},
        "precision": {"Normale", "Elevata"},
        "environment": {"Normale", "Tenuta ermetica/ambiente critico"},
    }
    for field, values in allowed.items():
        if getattr(data, field) not in values:
            raise ValueError(f"Valore non valido per {field}.")

    scores = {
        "Giunto elastico": 1,
        "Giunto a soffietto/lamellare": 1,
        "Giunto rigido": 1,
        "Giunto magnetico": 1,
    }

    if data.misalignment == "Nullo":
        scores["Giunto rigido"] += 4
        scores["Giunto a soffietto/lamellare"] += 1
    elif data.misalignment == "Piccolo":
        scores["Giunto elastico"] += 3
        scores["Giunto a soffietto/lamellare"] += 2
        scores["Giunto rigido"] -= 4
    else:
        scores["Giunto elastico"] += 4
        scores["Giunto a soffietto/lamellare"] += 1
        scores["Giunto rigido"] -= 6

    if data.vibrations == "Basse":
        scores["Giunto rigido"] += 1
        scores["Giunto a soffietto/lamellare"] += 1
    elif data.vibrations == "Medie":
        scores["Giunto elastico"] += 2
    else:
        scores["Giunto elastico"] += 3
        scores["Giunto rigido"] -= 3
        scores["Giunto a soffietto/lamellare"] -= 2

    if data.load == "Uniforme":
        scores["Giunto rigido"] += 1
        scores["Giunto a soffietto/lamellare"] += 1
        scores["Giunto magnetico"] += 1
    elif data.load == "Variabile":
        scores["Giunto elastico"] += 2
    else:
        scores["Giunto elastico"] += 3
        scores["Giunto rigido"] -= 3
        scores["Giunto a soffietto/lamellare"] -= 2

    if data.precision == "Elevata":
        scores["Giunto a soffietto/lamellare"] += 4
        scores["Giunto rigido"] += 4
        scores["Giunto elastico"] -= 1

    if data.environment == "Tenuta ermetica/ambiente critico":
        # La separazione ermetica è trattata come vincolo dominante, non come preferenza estetica.
        scores["Giunto magnetico"] += 12

    ordered_scores = tuple(
        sorted(((name, max(0, value)) for name, value in scores.items()), key=lambda item: (-item[1], item[0]))
    )
    family = ordered_scores[0][0]

    reasons: list[str] = []
    if family == "Giunto elastico":
        if data.misalignment != "Nullo":
            reasons.append(f"deve compensare un disallineamento {data.misalignment.lower()}")
        if data.vibrations != "Basse":
            reasons.append(f"deve smorzare vibrazioni {data.vibrations.lower()}")
        if data.load != "Uniforme":
            reasons.append(f"il carico è {data.load.lower()}")
        risk = "Surriscaldamento o usura dell'elemento elastomerico se ambiente e servizio non sono compatibili."
        family_checks = ("temperatura e compatibilità dell'elastomero", "disallineamento ammesso")
    elif family == "Giunto a soffietto/lamellare":
        reasons.append("serve elevata precisione e rigidità torsionale")
        if data.misalignment != "Nullo":
            reasons.append("è presente un disallineamento da assorbire senza gioco")
        risk = "Fatica del soffietto o delle lamelle se disallineamento e carichi ciclici superano i limiti."
        family_checks = ("rigidità torsionale e gioco", "vita a fatica di soffietto o lamelle")
    elif family == "Giunto rigido":
        reasons.extend(("gli alberi sono dichiarati allineati", "è richiesta una trasmissione torsionale precisa"))
        risk = "Piccoli errori di allineamento possono trasferire carichi elevati ad alberi e cuscinetti."
        family_checks = ("allineamento reale durante montaggio ed esercizio", "carichi aggiuntivi sui cuscinetti")
    else:
        reasons.append("è richiesta separazione senza contatto o tenuta ermetica")
        risk = "Disaccoppiamento se la coppia resistente supera quella trasmissibile magneticamente."
        family_checks = ("coppia di disaccoppiamento", "temperatura e distanza della barriera")

    common_checks = (
        "coppia nominale e massima ammesse dal catalogo",
        "velocità massima di rotazione",
        "diametri degli alberi e sistema di fissaggio",
    )
    return CouplingRecommendation(
        family=family,
        nominal_torque=nominal_torque(data.power_kw, data.rpm),
        design_torque=design_torque(data.power_kw, data.rpm, data.service_factor),
        scores=ordered_scores,
        reasons=tuple(reasons) or ("è la soluzione più equilibrata rispetto ai requisiti inseriti",),
        principal_risk=risk,
        checks=common_checks + family_checks,
    )


RUBRIC = {
    "scelta del giunto elastico": ("giunto elastico", "elastico", "elastomero"),
    "compensazione del disallineamento": (
        "disallineamento",
        "disallineati",
        "angolare",
        "radiale",
        "assiale",
    ),
    "smorzamento di vibrazioni o urti": (
        "vibrazion",
        "smorz",
        "urti",
        "picchi di carico",
    ),
    "verifica della coppia trasmissibile": (
        "coppia",
        "n·m",
        "nm",
        "momento torcente",
    ),
}


SOCRATIC_QUESTIONS = (
    SocraticQuestion(
        prompt=(
            "Immagina di montare un giunto rigido tra due alberi leggermente "
            "disallineati. Che cosa potrebbe succedere nel tempo e perché?"
        ),
        groups=(
            ("cuscinet", "usura", "vibraz", "sollecit", "surriscald", "rottura"),
        ),
        hints=(
            "Hai già individuato qualche effetto? Pensa a vibrazioni, usura e durata dei componenti.",
            "Segui il percorso delle forze: se il giunto non può deformarsi, cosa ricevono alberi e cuscinetti?",
        ),
        model_answer=(
            "Un giunto rigido non compensa il disallineamento. Le forze vengono trasmesse "
            "agli alberi e ai cuscinetti, aumentando vibrazioni, usura e rischio di rottura."
        ),
        confirmation=(
            "Hai collegato la scelta del giunto alle conseguenze sul sistema, "
            "non soltanto alla trasmissione del moto."
        ),
    ),
    SocraticQuestion(
        prompt=(
            "Ora cambia lo scenario: alberi ben allineati, vibrazioni minime e "
            "grande precisione di posizionamento. Manterresti il giunto elastico? Motiva."
        ),
        groups=(
            ("soffietto", "lamellar", "rigido"),
            ("precision", "rigidità", "torsional", "gioco"),
        ),
        hints=(
            "Hai notato che le condizioni sono cambiate: quale prestazione ora conta più dello smorzamento?",
            "Confronta elasticità e precisione torsionale. Quale giunto limita maggiormente il gioco?",
        ),
        model_answer=(
            "In questo caso valuterei un giunto a soffietto o lamellare, perché offre maggiore "
            "rigidità e precisione torsionale quando vibrazioni e disallineamento sono ridotti."
        ),
        confirmation=(
            "Hai modificato la soluzione quando sono cambiate le condizioni: "
            "questo è il cuore della progettazione tecnica."
        ),
    ),
    SocraticQuestion(
        prompt=(
            "Il catalogo indica che un giunto può trasmettere la coppia calcolata. "
            "Questa informazione è sufficiente per approvarlo? Quali altri dati controlleresti?"
        ),
        groups=(
            ("no", "non basta", "non è sufficiente", "insufficiente"),
            ("veloc", "disalline", "vibraz", "servizio", "ambiente", "precision", "temperatur"),
        ),
        hints=(
            "La coppia è importante, ma due macchine con la stessa coppia possono lavorare in condizioni diverse.",
            "Controlla almeno due elementi tra velocità, disallineamento, vibrazioni, temperatura e servizio.",
        ),
        model_answer=(
            "No. Oltre alla coppia controllerei velocità di rotazione, disallineamento ammesso, "
            "vibrazioni, fattore di servizio, temperatura e condizioni ambientali."
        ),
        confirmation=(
            "Hai riconosciuto che la coppia è necessaria, ma non sufficiente: "
            "la selezione dipende dall'intero contesto operativo."
        ),
    ),
)


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def evaluate_open_answer(answer: str) -> OpenAnswerResult:
    """Valutazione formativa e trasparente basata su quattro concetti attesi."""
    normalized = " ".join(answer.lower().strip().split())
    found = tuple(label for label, terms in RUBRIC.items() if _contains_any(normalized, terms))
    missing = tuple(label for label in RUBRIC if label not in found)
    score = len(found)

    if score == 4:
        feedback = "Ragionamento completo: scelta, condizioni di lavoro e verifica sono collegate bene."
    elif score >= 2:
        feedback = "Buona base tecnica. Completa il ragionamento usando i concetti indicati sotto."
    elif score == 1:
        feedback = "Hai individuato un elemento utile, ma la motivazione deve collegare più criteri."
    else:
        feedback = "La risposta è ancora generica. Riparti da disallineamento, vibrazioni e coppia."

    return OpenAnswerResult(score, 4, found, missing, feedback)


def evaluate_socratic_answer(answer: str, question_index: int) -> tuple[bool, str]:
    """Controlla se la risposta collega almeno un concetto di ogni gruppo."""
    if not 0 <= question_index < len(SOCRATIC_QUESTIONS):
        raise IndexError("Indice della domanda socratica non valido.")
    normalized = " ".join(answer.lower().strip().split())
    question = SOCRATIC_QUESTIONS[question_index]
    covered = all(_contains_any(normalized, group) for group in question.groups)
    return (covered, question.confirmation if covered else question.hints[0])


def build_report(
    student_name: str,
    quiz_score: int,
    torque_nominal: float,
    torque_design: float,
    open_answer: str,
    open_result: OpenAnswerResult,
    socratic_answers: Iterable[str] = (),
    design_summary: str = "",
    design_reflection: str = "",
) -> str:
    """Crea una breve relazione testuale scaricabile."""
    strengths = ", ".join(open_result.found) if open_result.found else "da consolidare"
    improvements = ", ".join(open_result.missing) if open_result.missing else "nessuno"
    name = student_name.strip() or "Studente"
    reasoning = "\n".join(
        f"{index}. {answer}" for index, answer in enumerate(socratic_answers, start=1)
    ) or "Nessuna risposta registrata."
    return f"""RELAZIONE FORMATIVA – GIUNTI MECCANICI

Studente: {name}

RISULTATI
- Punteggio domande guidate: {quiz_score}/3
- Coppia nominale calcolata: {torque_nominal:.1f} N·m
- Coppia di progetto: {torque_design:.1f} N·m
- Criteri presenti nella risposta aperta: {open_result.score}/{open_result.max_score}

PERCORSO DI RAGIONAMENTO SOCRATICO
{reasoning}

PROGETTO GUIDATO
{design_summary or "Nessun progetto registrato."}

RIFLESSIONE METACOGNITIVA
{design_reflection or "Nessuna riflessione registrata."}

RISPOSTA DELLO STUDENTE
{open_answer.strip() or "Nessuna risposta inserita."}

PUNTI DI FORZA
{strengths}

DA APPROFONDIRE
{improvements}

NOTA
La valutazione della risposta aperta è formativa e basata su parole-chiave.
Il docente verifica sempre il significato tecnico complessivo.
"""
