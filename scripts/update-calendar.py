#!/usr/bin/env python3
"""Busca o calendario de residencia medica no Estrategia MED e regenera a
tabela em index.html (entre os marcadores RESIDENCIA-TABELA / RESIDENCIA-NOTA).

Uso: python scripts/update-calendar.py
Sai com codigo 0 mesmo sem mudancas; nao toca no arquivo se a busca falhar.
"""

import html
import re
import sys
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

SOURCE_URL = (
    "https://med.estrategia.com/portal/residencia-medica/"
    "calendario-de-residencia-medica-confira-as-datas-das-proximas-provas/"
)
SOURCE_LINK = (
    'https://med.estrategia.com/portal/residencia-medica/'
    'calendario-de-residencia-medica-confira-as-datas-das-proximas-provas/'
)
INDEX = Path(__file__).resolve().parents[1] / "index.html"

TABELA_START = "<!-- RESIDENCIA-TABELA-START -->"
TABELA_END = "<!-- RESIDENCIA-TABELA-END -->"
NOTA_START = "<!-- RESIDENCIA-NOTA-START -->"
NOTA_END = "<!-- RESIDENCIA-NOTA-END -->"

# A tabela "2\u00aa Entrada Anual 2026" (provas de meio de ano, ingresso ainda
# em 2026) nao se aplica a turma atual; renderiza-se apenas o "Ingresso 2027".
GROUP_1 = "2\u00aa Entrada Anual 2026 (ingresso ainda em 2026)"
GROUP_2 = "Ingresso 2027"

WEAK_VALUES = {"\u2013", "\u2014", "a confirmar", "aguardando divulga\u00e7\u00e3o",
               "aguardando edital suplementar", "aguardando divulga\u00e7\u00e3o edital suplementar"}


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; update-calendar-bot/1.0)"
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


class TableParser(HTMLParser):
    """Extrai todas as tabelas como listas de linhas; cada linha = lista de
    celulas; cada celula = texto com quebras de linha preservadas."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.tables = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.cell_is_header = False
        self.rows = None
        self.cells = None
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "table" and not self.in_table:
            self.in_table = True
            self.tables.append([])
            self.rows = self.tables[-1]
        elif tag == "tr" and self.in_table:
            self.rows.append([])
            self.cells = self.rows[-1]
        elif tag in ("td", "th") and self.in_table:
            self.in_cell = True
            self.cell_is_header = tag == "th"
            self.buf = []
        elif self.in_cell and tag == "br":
            self.buf.append("\n")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.in_cell:
            text = "".join(self.buf)
            text = html.unescape(text)
            self.cells.append((text, self.cell_is_header))
            self.in_cell = False
        elif tag == "table" and self.in_table:
            self.in_table = False

    def handle_data(self, data):
        if self.in_cell:
            self.buf.append(data)

    def handle_entityref(self, name):
        if self.in_cell:
            self.buf.append(f"&{name};")

    def handle_charref(self, name):
        if self.in_cell:
            self.buf.append(f"&#{name};")


def clean(text):
    return re.sub(r"[ \t]+", " ", text).strip()


def extract_tables(raw):
    parser = TableParser()
    parser.feed(raw)
    out = []
    for table in parser.tables:
        if not table:
            continue
        headers = table[0]
        if any(h[1] for h in headers) and any("PROVA" in h[0].upper() for h in headers if h[1]):
            data = []
            for row in table[1:]:
                cells = [clean(c) for c, _ in row]
                if len(cells) >= 6:
                    data.append(cells[:6])
            out.append(data)
    return out


def parse_date(text):
    m = re.search(r"\b(\d{2})/(\d{2})/(\d{4})", text)
    if not m:
        return None
    return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))


def esc(text):
    return html.escape(text, quote=False)


def format_cell(text, primary=False, weak=False):
    cls = "p-4"
    if primary:
        cls += " font-semibold"
    if weak:
        cls += " text-gray-500"
    if not text:
        return f"<td class=\"{cls}\">\u2014</td>"

    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(.*?)\s+\(([^()]*)\)$", line)
        if m and m.group(1):
            line = (f"{esc(m.group(1))} "
                    f"<span class=\"text-xs text-gray-500\">({esc(m.group(2))})</span>")
        else:
            line = esc(line)
        lines.append(line)
    inner = "<br>".join(lines)
    return f"<td class=\"{cls}\">{inner}</td>"


def render_group(title, rows):
    out = [f"<tr class=\"bg-gray-100/60\">"
           f"<td class=\"p-4 font-semibold\" colspan=\"6\">{esc(title)}</td></tr>"]
    for cells in rows:
        uf, selecao, edital, inscricoes, taxa, prova = cells
        is_nac = uf.upper() == "NAC" or selecao.upper() in ("ENAMED", "ENARE")
        row_cls = ("bg-camilo-primary/5 hover:bg-camilo-primary/10 transition"
                   if is_nac else "hover:bg-gray-50 transition")
        name_cls = "p-4 font-bold text-camilo-primary" if is_nac else "p-4 font-semibold"
        taxa_fmt = re.sub(r"R\$(\d)", r"R$ \1", taxa)
        out.append("<tr class=\"" + row_cls + "\">")
        out.append(f"<td class=\"p-4\">{esc(uf) or '\u2014'}</td>")
        out.append(f"<td class=\"{name_cls}\">{esc(selecao)}</td>")
        out.append(format_cell(edital, weak=edital.lower() in WEAK_VALUES or "(previs" in edital))
        out.append(format_cell(inscricoes))
        out.append(format_cell(taxa_fmt, weak=any(v in taxa_fmt.lower() for v in ("a confirmar", "aguardando"))
                               or taxa_fmt in {"\u2013", "\u2014"}))
        out.append(format_cell(prova, primary=True, weak=not parse_date(prova)))
        out.append("</tr>")
    return out


def main():
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()

    try:
        raw = fetch(SOURCE_URL)
        tables = extract_tables(raw)
    except Exception as exc:
        print(f"ERRO: falha ao buscar fonte: {exc}", file=sys.stderr)
        return 1

    if len(tables) < 2:
        print(f"ERRO: tabelas esperadas (2) nao encontradas (achou {len(tables)})", file=sys.stderr)
        return 1

    # A tabela "Ingresso 2027" e a que contem as selecoes nacionais (ENAMED/ENARE)
    # ou provas a partir de set/2026; a outra e a de 2a Entrada (meio de ano),
    # que nao deve ser exibida para a turma.
    ingress2027 = None
    for table in tables:
        if any(cells[0].upper() == "NAC" or cells[1].upper() in ("ENAMED", "ENARE")
               for cells in table):
            ingress2027 = table
            break
    if ingress2027 is None:
        print("ERRO: tabela Ingresso 2027 nao encontrada", file=sys.stderr)
        return 1

    body = []
    filtered = []
    for cells in ingress2027:
        prova = cells[5]
        d = parse_date(prova)
        if d is not None and d.date() <= today:
            continue
        filtered.append(cells)
    if filtered:
        body.extend(render_group(GROUP_2, filtered))

    if not body:
        print("ERRO: nenhuma prova futura encontrada; nao vou sobrescrever o arquivo",
              file=sys.stderr)
        return 1

    novo_tbody = "\n" + "\n".join(body) + "\n"
    nota = (f"Somente processos de ingresso em 2027 com prova ainda por acontecer. "
            f"Dados conforme "
            f"<a href=\"{SOURCE_LINK}\" target=\"_blank\" "
            f"class=\"text-camilo-primary underline\">Estrat\u00e9gia MED</a> "
            f"(atualizado automaticamente em {today.strftime('%d/%m/%Y')}). "
            f"Itens com \"previs\u00e3o\" ou \"a confirmar\" ainda dependem de edital oficial.")

    idx = INDEX.read_text(encoding="utf-8")
    if TABELA_START not in idx or TABELA_END not in idx:
        print("ERRO: marcadores RESIDENCIA-TABELA nao encontrados em index.html",
              file=sys.stderr)
        return 1
    if NOTA_START not in idx or NOTA_END not in idx:
        print("ERRO: marcadores RESIDENCIA-NOTA nao encontrados em index.html",
              file=sys.stderr)
        return 1

    ts, te = idx.index(TABELA_START) + len(TABELA_START), idx.index(TABELA_END)
    new_idx = idx[:ts] + novo_tbody + idx[te:]
    ns = new_idx.index(NOTA_START) + len(NOTA_START)
    ne = new_idx.index(NOTA_END)
    new_idx = new_idx[:ns] + nota + new_idx[ne:]
    INDEX.write_text(new_idx, encoding="utf-8")

    data_rows = sum(1 for t in body if t.startswith("<tr class=\"hover") or "bg-camilo-primary" in t)
    print(f"OK: {len(body)} linhas geradas ({data_rows} sele\u00e7\u00f5es)")
    print(f"OK: tabela atualizada para {today.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
