# Copyright (C) 2026 Cristian Liporace
# Licensed under the GNU General Public License v3.0
# See LICENSE file for details.

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

STRONG_SUBJECT_ALIASES = {
    "rettore": ["rettore", "il rettore"],
    "pro_rettore": ["pro rettore", "pro-rettore", "prorettore"],
    "senato_accademico": ["senato accademico", "il senato accademico"],
    "consiglio_amministrazione": ["consiglio di amministrazione", "consiglio d amministrazione", "cda"],
    "collegio_revisori": ["collegio dei revisori", "collegio dei revisori dei conti"],
    "nucleo_valutazione": ["nucleo di valutazione", "il nucleo di valutazione"],
    "direttore_generale": ["direttore generale", "il direttore generale"],
    "consiglio_studenti": ["consiglio degli studenti", "consiglio studentesco"],
    "comitato_unico_garanzia": ["comitato unico di garanzia", "cug"],
    "collegio_disciplina": ["collegio di disciplina"],
    "commissione_etica": ["commissione etica"],
    "presidio_qualita": ["presidio della qualità", "presidio qualita"],
    "dipartimento": ["dipartimento", "dipartimenti"],
    "scuole_specializzazione": ["scuole di specializzazione", "scuola di specializzazione"],
    "scuole_dottorato": ["scuole di dottorato", "scuola di dottorato", "corsi di dottorato", "corso di dottorato", "dottorato di ricerca"],
    "scuole_interdipartimentali": ["scuole interdipartimentali", "scuola interdipartimentale"],
    "corsi_studio": ["consigli dei corsi di studio", "consiglio dei corsi di studio", "corsi di studio", "corso di studio"],
    "sistema_bibliotecario": ["sistema bibliotecario di ateneo", "sistema bibliotecario"],
    "centro_residenziale": ["centro residenziale"],
}


#WEAK_SUBJECT_ALIASES = {
    #"studenti": ["studenti", "studente"],
    #"rappresentanze_studentesche": ["rappresentanze studentesche", "rappresentanza studentesca"],
    #"personale_docente": ["personale docente", "docenti", "professori", "ricercatori"],
    #"personale_tecnico_amministrativo": ["personale tecnico amministrativo", "personale tecnico-amministrativo", "personale amministrativo"],
    #"centro": ["centro", "centri"],
#}

NORMATIVE_FUNCTIONS = {
    "elezione": ["elezione","elezioni","elettorale","voto","votazione","candidatura","candidature","elettorato attivo","elettorato passivo","scrutinio","quorum","ballottaggio"],
    "nomina": ["nomina","nominato","nominata","designazione","designazioni","designato","designata"],
    "mandato": ["mandato","durata in carica","dura in carica","rinnovabile","rieleggibilità","rieleggibile","non rinnovabile"],
    "decadenza": ["decadenza","decade","decaduto","decaduta","sostituzione","sostituzioni","subentra","cessazione","dimissioni"],
    "incompatibilità": ["incompatibilità","incompatibile","incompatibili","ineleggibilità","ineleggibile","ineleggibili"],
    "composizione": ["composizione","composto","composta","componenti","membri","rappresentanti"],
    "funzionamento": ["funzionamento","sedute","convocazione","ordine del giorno","riunioni","verbale","validità delle sedute","validità delle riunioni"],
    "reclami": ["reclami","reclamo","ricorso","ricorsi"],
    "istituzione": ["istituzione","istituito","istituita","attivazione","costituzione","costituito","costituita",],
    "disattivazione": ["disattivazione","soppressione","disattivato","disattivata"],
    "competenze": ["competenze","funzioni","attribuzioni","responsabilità","poteri"],
    "organizzazione": ["organizzazione","organizzazione del","organizzazione della","organizzazione dei" ],
}

def normalize_text(text):
    text = text.lower()
    text = text.replace("’", "'")
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(r"\b(?:articolo|art|titolo|capo)\.?\b", " ", text)
    common_italian = {"di", "in", "vi", "ci", "mi", "li", "il", "id"}

    def remove_roman(match):
        word = match.group(0)
        if word in common_italian or len(word) < 2:
            return word
        return " "

    text = re.sub(r"\b[ivxlcdm]+\b", remove_roman, text)
    text = re.sub(r"\b\d+(?:\.\d+)?(?:\s*-\s*[a-z]+)?\b", " ", text)

    # non elimino tutte le preposizioni:
    # alcune servono per riconoscere soggetti come "consiglio di amministrazione"
    text = re.sub(r"[^a-zàèéìòù0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_article_number(number):
    number = number.lower()
    number = number.replace(" ", "")
    number = number.replace("–", "-")
    number = number.replace("—", "-")
    return number

def group_by_article(records):
    grouped = {}

    for record in records:
        document = record.get("document")
        number = record.get("number")

        article_id = f"{document}:{number}"

        chapter = record.get("chapter")

        if article_id not in grouped:
            grouped[article_id] = {
                "article_id": article_id,
                "document": document,
                "title": record.get("title", ""),
                "chapter": chapter,
                "number": number,
                "header": record.get("header", ""),
                "paragraphs": [],
                "full_text": "",
            }

        grouped[article_id]["paragraphs"].append(record)

        paragraph_text = record.get("text")
        if paragraph_text:
            grouped[article_id]["full_text"] += "\n" + paragraph_text

    return list(grouped.values())


def find_statute_article(statute_articles, number):
    normalized_number = normalize_article_number(number)

    for article in statute_articles:
        article_number = normalize_article_number(article.get("number"))
        if article_number == normalized_number:
            return article

    return None


# cerchiamo riferimenti espliciti del regolamento che rimandano allo statuto
"""
passaggi:
1) Prende un articolo per intero del Regolamento.
2) Cerca nel suo testo frasi che citano articoli dello Statuto.
3) Estrae numero articolo e numero comma.
4) Controlla se l’articolo dello Statuto esiste davvero.
5) Se esiste, salva il riferimento con anche frase originale indicata dal campo surface.
"""
def explicit_reference_from_regulation_to_statute(reg_article, statute_articles):
    raw_text = reg_article.get("full_text")
    raw_text_lower = raw_text.lower()

    pattern = (
        r""
        r"(?:art\.?|articolo)\s*"
        r"(\d+(?:\.\d+)?(?:\s*[-–]\s*[a-z]+)?)"
        r"(?:\s*,?\s*comma\s*(\d+(?:\.\d+)?(?:\s*[-–]\s*[a-z]+)?))?"
        r"(?:[^\.]{0,40})?"
        r"\bstatuto\b"
    )

    references = []

    for match in re.finditer(pattern, raw_text_lower):
        article_number = normalize_article_number(match.group(1))
        paragraph_number = normalize_article_number(match.group(2)) if match.group(2) else None

        #potrei anche cancellarlo
        target = find_statute_article(statute_articles, article_number)

        if target:
            references.append({
                "target": target,
                "article_number": article_number,
                "paragraph_number": paragraph_number,
                "surface": match.group(0).strip(), #la surface indica quale parte del testo ha generato la relazione
            })
    return references

'''
1) normalizza il testo;
2) trasforma il dizionario degli alias in una lista;
3) cerca prima gli alias più lunghi e specifici;
4) usa regex con confini per evitare match parziali come la parola CUG dentro la parola cugino;
5) evita match sovrapposti;
6) restituisce i soggetti trovati.
'''
def find_subject_aliases(text, alias_dict):
    normalized = normalize_text(text)
    found = set()
    occupied_spans = []

    aliases = []
    for canonical, alias_list in alias_dict.items():
        for alias in alias_list:
            aliases.append((canonical, normalize_text(alias)))

    #utilizzo il riordinamento perchè voglio leggere prima pro-rettore e poi rettore
    #evitando falsi match tra pro-rettore e rettore essendo due soggetti distinti
    aliases.sort(key=lambda x: len(x[1]), reverse=True)


    for canonical, alias_norm in aliases:
        if not alias_norm:
            continue

        pattern = r"(?<!\w)" + re.escape(alias_norm) + r"(?!\w)"

        for match in re.finditer(pattern, normalized):
            start, end = match.span()

            #c’è sovrapposizione se il nuovo intervallo non è completamente prima e non è completamente dopo quello vecchio
            overlaps = any(not (end <= old_start or start >= old_end) for old_start, old_end in occupied_spans)

            if overlaps:
                continue

            found.add(canonical)
            occupied_spans.append((start, end))

    return sorted(found)

def clean_header_for_subjects(header):
    header = re.sub(r"^art\.?\s*\d+(?:\.\d+)?\s*[-–—]?\s*","",header,flags=re.IGNORECASE)
    return header.strip()

def main_subject_text(article):
    return " ".join([article.get("chapter"),clean_header_for_subjects(article.get("header"))])

def find_main_subjects(article):
    text = main_subject_text(article)
    strong = find_subject_aliases(text, STRONG_SUBJECT_ALIASES)
    return {"strong": strong, "all": strong}

def same_main_subject(reg_article, stat_article):
    reg_subjects = find_main_subjects(reg_article)
    stat_subjects = find_main_subjects(stat_article)

    common_subjects = sorted(set(reg_subjects["strong"]).intersection(stat_subjects["strong"]))

    return {
        "matched": bool(common_subjects),
        "common_subjects": common_subjects,
        "regulation_subjects": reg_subjects["strong"],
        "statute_subjects": stat_subjects["strong"],
    }


def function_text(article):
    return " ".join([article.get("header", ""), article.get("chapter", "")])

def find_main_functions(article):
    normalized = normalize_text(function_text(article))
    found = []

    for function_name, keywords in NORMATIVE_FUNCTIONS.items():
        for keyword in keywords:
            keyword_norm = normalize_text(keyword)
            if not keyword_norm:
                continue

            pattern = r"(?<!\w)" + re.escape(keyword_norm) + r"(?!\w)"
            if re.search(pattern, normalized):
                found.append(function_name)
                break

    return sorted(set(found))


def same_main_function(reg_article, stat_article):
    reg_functions = set(find_main_functions(reg_article))
    stat_functions = set(find_main_functions(stat_article))
    common = sorted(reg_functions.intersection(stat_functions))

    return {
        "matched": bool(common),
        "functions": common,
        "regulation_functions": sorted(reg_functions),
        "statute_functions": sorted(stat_functions),
    }


def token_set(text):
    return set(normalize_text(text).split())

def jaccard_similarity(text_a, text_b):
    set_a = token_set(text_a)
    set_b = token_set(text_b)

    if not set_a or not set_b:
        return 0.0
    # numero parole in comune / numero totali di parole
    return len(set_a.intersection(set_b)) / len(set_a.union(set_b))

def structural_similarity(reg_article, stat_article):
    title_score = jaccard_similarity(reg_article.get("title"), stat_article.get("title"))
    header_score = jaccard_similarity(reg_article.get("header"), stat_article.get("header"))
    chapter_header_score = jaccard_similarity(reg_article.get("chapter"), stat_article.get("header"))

    return {
        "title_score": round(title_score, 3),
        "header_score": round(header_score, 3),
        "chapter_header_score": round(chapter_header_score, 3)}


def make_relation(source, target, relation_type, confidence, evidence):
    return {
        "source_article_id": source["article_id"],
        "source_document": source["document"],
        "source_number": source["number"],
        "source_header": source["header"],
        "source_title": source.get("title"),
        "source_chapter": source.get("chapter"),

        "target_article_id": target["article_id"],
        "target_document": target["document"],
        "target_number": target["number"],
        "target_header": target["header"],
        "target_title": target.get("title"),
        "target_chapter": target.get("chapter"),

        "relation_type": relation_type,
        "confidence": round(confidence, 3),
        "evidence": evidence,
    }


def build_explicit_relation(reg_article, ref):
    target = ref["target"]

    #stesso soggetto
    subject_match = same_main_subject(reg_article, target)
    #stessa funzione amministrativa
    function_match = same_main_function(reg_article, target)
    #stessa struttura tramite la similarità di jaccard
    structural = structural_similarity(reg_article, target)

    supporting_patterns = []

    if subject_match["matched"]:
        supporting_patterns.append("same_main_subject")

    if function_match["matched"]:
        supporting_patterns.append("same_main_function")

    if structural["chapter_header_score"] >= 0.45:
        supporting_patterns.append("chapter_header_similarity")

    if structural["title_score"] >= 0.75:
        supporting_patterns.append("same_title_area")

    return make_relation(
        source=reg_article,
        target=target,
        relation_type="explicit_reference",
        confidence=1.0,
        evidence={
            "matched_patterns": ["explicit_reference"],
            "explicit_reference": {
                "surface": ref["surface"],
                "article_number": ref["article_number"],
                "paragraph_number": ref["paragraph_number"],
            },
            "supporting_patterns": supporting_patterns,
            "subjects": subject_match,
            "functions": function_match,
            "structural": structural,
        }
    )


def build_candidate_relation(reg_article, stat_article):
    subject_match = same_main_subject(reg_article, stat_article)
    function_match = same_main_function(reg_article, stat_article)
    structural = structural_similarity(reg_article, stat_article)

    chapter_header_score = structural["chapter_header_score"]
    header_score = structural["header_score"]
    title_score = structural["title_score"]

    has_main_subject = subject_match["matched"]
    has_chapter_header_match = chapter_header_score >= 0.45
    has_header_match = header_score >= 0.55

    has_strong_candidate_evidence = (
            (has_main_subject and (function_match["matched"] or has_chapter_header_match or has_header_match))
            or has_chapter_header_match
            or has_header_match
    )

    if not has_strong_candidate_evidence:
        return None

    score = 0.0
    matched_patterns = []

    if has_main_subject:
        score += 0.60
        matched_patterns.append("same_main_subject")

    if function_match["matched"]:
        score += 0.20
        matched_patterns.append("same_main_function")

    if has_chapter_header_match:
        score += 0.20
        matched_patterns.append("chapter_header_similarity")

    if has_header_match:
        score += 0.15
        matched_patterns.append("header_similarity")

    # stesso titolo
    if title_score >= 0.75:
        score += 0.05
        matched_patterns.append("same_title_area")

    return make_relation(
        source=reg_article,
        target=stat_article,
        relation_type="candidate_relation",
        confidence=min(score, 0.99),
        evidence={
            "matched_patterns": matched_patterns,
            "subjects": subject_match,
            "functions": function_match,
            "structural": structural,
        }
    )

def merge_relation(existing, new_relation):
    if existing["relation_type"] == "explicit_reference":
        return existing

    if new_relation["relation_type"] == "explicit_reference":
        return new_relation

    existing["confidence"] = round(max(existing["confidence"], new_relation["confidence"]), 3)

    old_patterns = set(existing["evidence"].get("matched_patterns", []))
    new_patterns = set(new_relation["evidence"].get("matched_patterns", []))

    existing["evidence"]["matched_patterns"] = sorted(old_patterns.union(new_patterns))
    return existing


def deduplicate_relations(relations):
    deduped = {}

    for relation in relations:
        key = (relation["source_article_id"], relation["target_article_id"],)

        if key not in deduped:
            deduped[key] = relation
        else:
            deduped[key] = merge_relation(deduped[key], relation)

    return list(deduped.values())


def build_relations(input_filename="processed_articles_unical.json", output_filename="candidate_relations_unical.json"):
    input_path = ROOT / "data" / "processed" / input_filename
    output_path = ROOT / "data" / "processed" / output_filename

    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    regulation_records = [record for record in records if record.get("document") == "regolamento"]
    statute_records = [record for record in records if record.get("document") == "statuto"]

    regulation_articles = group_by_article(regulation_records)
    statute_articles = group_by_article(statute_records)

    relations = []

    for reg_article in regulation_articles:
        explicit_refs = explicit_reference_from_regulation_to_statute(reg_article,statute_articles)

        for ref in explicit_refs:
            relations.append(build_explicit_relation(reg_article, ref))

        for stat_article in statute_articles:
            candidate = build_candidate_relation(reg_article, stat_article)

            if candidate:
                relations.append(candidate)

    relations = deduplicate_relations(relations)

    relations = sorted(relations,key=lambda r: (
        0 if r["relation_type"] == "explicit_reference" else 1,
        r["confidence"],
        r["source_article_id"],
        r["target_article_id"],
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(relations, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    build_relations()