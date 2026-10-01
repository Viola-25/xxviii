"""Gera artes PNG 1080x1920 (Instagram Stories) da programacao das festas.

Uso: python scripts/generate-stories.py
Saida: stories/jantar.png e stories/baile.png
"""

import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "stories")
BRASAO = os.path.join(ROOT, "Brasão-09.png")

FONTS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
TITLE = os.path.join(FONTS, "georgiab.ttf")
SANS_B = os.path.join(FONTS, "segoeuib.ttf")
SANS = os.path.join(FONTS, "segoeui.ttf")
MONO_B = os.path.join(FONTS, "consolab.ttf")

BG_TOP = (96, 0, 0)
BG_MID = (139, 0, 0)
BG_BOT = (58, 0, 0)
GOLD = (212, 175, 55)
GOLD_LT = (236, 205, 122)
WHITE = (255, 255, 255)
MUTED = (226, 178, 178)

EVENTOS = [
    {
        "arquivo": "jantar.png",
        "titulo": "Jantar de Formatura",
        "kicker": "COMISSÃO DE FORMATURA · MED XXVIII",
        "badge": "QUI, 08 OUT · 21h00 → 04h00 · ProMagno",
        "rodape": "@medscxxviii · ProMagno, São Paulo",
        "linhas": [
            ("21:00", "Início do evento", "ini"),
            ("21:00 – 22:30", "DJ residente", "dim"),
            ("22:30 – 23:30", "Valsa", "alt"),
            ("23:30 – 00:30", "Fun 7", "alt"),
            ("00:30 – 01:00", "Troca de palco · DJ", "dim"),
            ("01:00 – 02:00", "Bonde do Tigrão", "alt"),
            ("02:00 – 02:30", "Troca de palco · DJ", "dim"),
            ("02:30 – 03:30", "Missiato", "alt"),
            ("03:30 – 04:00", "Troca de palco · DJ", "dim"),
            ("04:00", "Fim", "ini"),
        ],
    },
    {
        "arquivo": "baile.png",
        "titulo": "Baile de Formatura",
        "kicker": "COMISSÃO DE FORMATURA · MED XXVIII",
        "badge": "SÁB, 10 OUT · 22h00 → 05h00 · ProMagno",
        "rodape": "@medscxxviii · ProMagno, São Paulo",
        "linhas": [
            ("22:00", "Início do evento", "ini"),
            ("22:00 – 23:30", "DJ residente", "dim"),
            ("23:30 – 00:30", "Matheus Henrique e Gabriel", "alt"),
            ("00:30 – 01:00", "Bateria São Camilo", "alt"),
            ("01:00 – 02:00", "Chuvisco", "alt"),
            ("02:00 – 02:30", "Troca de palco · DJ", "dim"),
            ("02:30 – 03:30", "MC Lan", "alt"),
            ("03:30 – 04:00", "Troca de palco · DJ", "dim"),
            ("04:00 – 05:00", "GP da ZL", "alt"),
            ("05:00", "Fim", "ini"),
        ],
    },
]


def fonte(caminho, tamanho):
    return ImageFont.truetype(caminho, tamanho)


def gradiente():
    img = Image.new("RGB", (W, H))
    px = img.load()
    meio = H // 2
    for y in range(H):
        if y < meio:
            t = y / meio
            c = tuple(int(BG_TOP[i] + (BG_MID[i] - BG_TOP[i]) * t) for i in range(3))
        else:
            t = (y - meio) / (H - meio)
            c = tuple(int(BG_MID[i] + (BG_BOT[i] - BG_MID[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return img.convert("RGBA")


def caber(texto, caminho, tam, max_w, d):
    while tam > 12:
        f = fonte(caminho, tam)
        if d.textlength(texto, font=f) <= max_w:
            return f, tam
        tam -= 2
    return fonte(caminho, tam), tam


def central(d, cx, y, texto, f, cor):
    w = d.textlength(texto, font=f)
    d.text((cx - w / 2, y), texto, font=f, fill=cor)
    return w


def com_tracking(d, cx, y, texto, f, cor, espaco=6):
    larguras = [d.textlength(c, font=f) for c in texto]
    total = sum(larguras) + espaco * (len(texto) - 1)
    x = cx - total / 2
    for c, w in zip(texto, larguras):
        d.text((x, y), c, font=f, fill=cor)
        x += w + espaco
    return total


def gerar(ev):
    base = gradiente()
    cx = W // 2
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # moldura dourada
    d.rounded_rectangle([40, 40, W - 40, H - 40], radius=56, outline=GOLD + (200,), width=4)

    # brasao
    if os.path.exists(BRASAO):
        b = Image.open(BRASAO).convert("RGBA")
        alvo = 170
        b.thumbnail((alvo, alvo), Image.LANCZOS)
        base.alpha_composite(b, (cx - b.width // 2, 230))

    # titulo (auto-ajuste)
    dt = ImageDraw.Draw(base)
    f_tit, _ = caber(ev["titulo"], TITLE, 92, W - 160, dt)
    f_kick = fonte(SANS_B, 30)
    f_badge = fonte(SANS_B, 34)
    f_time = fonte(MONO_B, 38)
    f_lab = fonte(SANS_B, 38)
    f_lab_dim = fonte(SANS, 38)
    f_rod = fonte(SANS_B, 32)

    # cartao da programacao
    card = [60, 700, W - 60, 700 + 50 + 10 * 84 + 50]
    d.rounded_rectangle(card, radius=40, fill=(0, 0, 0, 78), outline=(255, 255, 255, 26), width=2)

    # badge
    bw = d.textlength(ev["badge"], font=f_badge) + 72
    bx0, by0, bx1, by1 = cx - bw / 2, 600, cx + bw / 2, 672
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=36, fill=(0, 0, 0, 90), outline=GOLD + (220,), width=3)

    # divisorias nas bordas exatas entre faixas (camada com alpha)
    for k in range(1, len(ev["linhas"])):
        y_div = card[1] + 50 + 84 * k
        d.line([(card[0] + 40, y_div), (card[2] - 40, y_div)], fill=(255, 255, 255, 46), width=2)

    img = Image.alpha_composite(base, ov)
    d = ImageDraw.Draw(img)

    com_tracking(d, cx, 430, ev["kicker"], f_kick, GOLD_LT, 5)
    central(d, cx, 470, ev["titulo"], f_tit, WHITE)
    central(d, cx, 614, ev["badge"], f_badge, GOLD_LT)

    # linhas
    x_fim_time = card[0] + 310
    x_lab = card[0] + 360
    for i, (hora, rotulo, tipo) in enumerate(ev["linhas"]):
        cor_h = GOLD_LT if tipo != "dim" else GOLD
        cor_t = GOLD_LT if tipo == "ini" else (WHITE if tipo == "alt" else MUTED)
        cy = card[1] + 50 + 84 * i + 42
        d.text((x_fim_time, cy), hora, font=f_time, fill=cor_h, anchor="rm")
        f = f_lab if tipo in ("alt", "ini") else f_lab_dim
        d.text((x_lab, cy), rotulo, font=f, fill=cor_t, anchor="lm")

    # rodape
    central(d, cx, card[3] + 55, ev["rodape"], f_rod, MUTED)

    os.makedirs(OUT, exist_ok=True)
    caminho = os.path.join(OUT, ev["arquivo"])
    img.convert("RGB").save(caminho, "PNG", optimize=True)
    print("ok:", caminho)


if __name__ == "__main__":
    for ev in EVENTOS:
        gerar(ev)
