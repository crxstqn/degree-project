# Copyright (C) 2026 Cristian Liporace
# Licensed under the GNU General Public License v3.0
# See LICENSE file for details.

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

university = input("Enter an available university (unical, unipi, unimi, polito): ").strip()
Path(f"output/{university}").mkdir(parents=True, exist_ok=True)
df = pd.read_csv(f'data/processed/merged_dataset_{university}.csv', sep=';')

prompt = ("You are an expert in Answer Set Programming (ASP). Do not output comments or anything other "
            "than facts and rules. In your response you must use the following atoms: "
            "'proposizione(Pair, ID, P, S, A, O)' where 'Pair' is the identifier of the text pair, " 
            "'ID' identifies the source text where 0 means Regolamento and 1 means Statuto, 'P' identifies " 
            "the atomic proposition as p1, p2, p3 and so on, 'S' is the main subject, 'A' is the main predicate, normalized " 
            " to the infinitive form and 'O' is the object of the sentence; "
            "Create a separate proposizione for each explicitly stated independent predicate; "
            "forma(Pair, ID, P, Tipo), where 'Pair', 'ID' and 'P' are the same of the 'proposizione' and "
            "'Tipo' is positiva when the proposition is not explicitly negated and negativa when the text explicitly negates "
            "the proposition: one forma for one proposizione; "
            "'modalita(Pair, ID, P, Tipo)', where 'Tipo' is 'obbligatorio' for an explicit duty, 'facoltativo' for an explicit permission, " "'vietato' for an explicit prohibition, and 'neutrale' for descriptive; "
            " 'quantita(Pair, ID, P, Concetto, Operatore, Valore, Unita)', where 'Concetto' identifies what is measured, "
            "'Operatore' must be eq, gt, ge, lt or le where expressions such as 'almeno' map to ge, 'più di' / 'oltre' is gt, "
            "'al massimo' /  'non più di' is le, 'meno di' is lt and exact numerical values is 'eq',  "
            "'Valore' must be an integer, but when the value is a fraction use a normalized atom such as "
            "'due_terzi', 'tre_quarti', etc. 'Unita' identifies the unit; "
            "Use 'esclusiva(Pair, ID, P)' only when the text explicitly states that the competence or action belongs exclusively "
            "to the subject. "
            "General rules: Preserve the explicit semantic content of the source text; Use the same normalized atom for "
            "the same concept whenever it occurs; "
            "Assign proposition identifiers p1, p2, p3, ... according to the order in which the propositions appear in the "
            "source text. Use lowercase snake_case atoms for S, A, O, Concetto, Valore and Unita "
            "Example of sentences: "
            "Sentence from Regolamento: Il Senato Accademico ha la prerogativa di proporre al corpo elettorale, con "
            "le modalità di cui all’art. 2.4, comma 1, lettera f), dello Statuto, con maggioranza di almeno due terzi dei suoi "
            "componenti, la mozione di sfiducia al Rettore di cui all’art. 2.2, comma 1, lettera r), dello Statuto, non prima che "
            "siano trascorsi due anni dall’inizio del mandato del Rettore medesimo. "
            "Example of output: proposizione(1, 0, p1, senato_accademico, proporre, mozione_sfiducia). "
            "forma(1, 0, p1, positiva). modalita(1, 0, p1, neutrale). quantita(1, 0, p1, componenti, ge, due_terzi, frazione). "
            " Sentence from Statuto: Il Collegio di Disciplina svolge funzioni istruttorie nell’ambito dei procedimenti disciplinari "
            "promossi nei confronti dei professori e ricercatori ed esprime in merito parere conclusivo. Le relative funzioni sono "
            "svolte a titolo gratuito. " 
            "Example of output: proposizione(1, 1, p1, collegio_di_disciplina, svolgere, funzione_istruttoria). "
            "proposizione(1, 1, p2, collegio_di_disciplina, esprimere, parere_conclusivo). "
            "proposizione(1, 1, p3, funzione, essere_svolto, titolo_gratuito). "
            "forma(1, 1, p1, positiva). forma(1, 1, p2, positiva). forma(1, 1, p3, positiva). modalita(1, 1, p1, neutrale). "
            "modalita(1, 1, p2, neutrale). modalita(1, 1, p3, neutrale). "
)

def call_llm(system_prompt, pair_id, node_id_a, frase_a, node_id_b, frase_b):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Pair ID: {pair_id}\n"
                    f"Sentence 0 ({node_id_a}): '{frase_a}'\n"
                    f"Sentence 1 ({node_id_b}): '{frase_b}'"
                )
            }
        ],
        reasoning_effort="medium"
    )
    content = response.choices[0].message.content.strip()

    usage = response.usage

    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens

    print(f"Pair {pair_id} |  input={input_tokens} | output={output_tokens} | totale={total_tokens}")
    return content



def parse_node_id(node_id):
    parts = str(node_id).split(":")

    document = parts[0]
    article = parts[1] if len(parts) > 1 else ""

    if len(parts) > 2 and parts[2]:
        comma = parts[2]
    else:
        comma = "0"

    return document, article, comma

for index, row in df.iterrows():
    pair_id = int(row["PAIR_ID"])
    node_id_a = row['NODE_ID_A']
    frase_a = row['FRASE_A']
    node_id_b = row['NODE_ID_B']
    frase_b = row['FRASE_B']

    doc_a, art_a, comma_a = parse_node_id(node_id_a)
    doc_b, art_b, comma_b = parse_node_id(node_id_b)

    source_facts = (f'articolo({pair_id}, 0, {doc_a}, "{art_a}", "{comma_a}").\n' 
                    f'articolo({pair_id}, 1, {doc_b}, "{art_b}", "{comma_b}").\n')
    if pair_id > 52:
        result = call_llm(prompt, pair_id,node_id_a, frase_a,node_id_b, frase_b)
        with open(f'./output/{university}/output_{index}.asp', 'w', encoding="utf-8") as f:
                f.write(source_facts)
                f.write(result + "\n")