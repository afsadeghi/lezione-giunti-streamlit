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
