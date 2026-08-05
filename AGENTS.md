# Projeto: Site da Comissão de Formatura TXXVIII (São Camilo)

Site estático (HTML + Tailwind via CDN) do grupo de formatura da turma de
medicina XXVIII. Hospedado no **GitHub Pages** (deploy automático a partir do
branch `main`).

## Estrutura

- `index.html` — página principal (quadro de avisos, forms, calendário de residência).
- `comissao.html` — página da comissão.
- `scripts/update-calendar.py` — gerador automático da tabela de residência médica.
- `.github/workflows/update-calendar.yml` — cron diário que roda o script.

## Seção "Residência Médica" (#residencia)

- Tabela gerada automaticamente pelo script (não editar o `<tbody>` à mão).
- O script faz scraping do artigo do **Estratégia MED** (calendário de residência),
  parseia as 2 tabelas (2ª Entrada 2026 e Ingresso 2027) e reescreve o conteúdo
  entre os marcadores `<!-- RESIDENCIA-TABELA-START/END -->` no `index.html`.
- A nota de rodapé fica entre `<!-- RESIDENCIA-NOTA-START/END -->`.
- Filtra provas com data `<= hoje` (fuso `America/Sao_Paulo`); itens "a confirmar"
  e "previsão" sempre permanecem.
- Script é **idempotente** (2ª execução não muda o arquivo) e **aborta sem
  escrever** se a busca falhar ou as tabelas não forem encontradas.

### Como rodar localmente

```
python scripts/update-calendar.py
```

Dependências: apenas Python 3 stdlib. Rodar de novo após editar o script para
regenerar a tabela. O GitHub Actions roda 1x/dia (07:15 UTC = 04:15 BRT) e só
faz commit se o conteúdo mudou. Também dá pra disparar manualmente em
Actions → "Atualizar calendario de residencia" → Run workflow.

## Filtros/ordenação client-side (JS no fim do `index.html`)

- Busca por texto, Nacionais/Regionais, UF e ordenação (prova, taxa, nome,
  edital, fim das inscrições).
- JS lê as linhas do `<tbody>` via DOM. A tabela tem **6 colunas** e as linhas
  de cabeçalho de grupo usam `colspan="6"` — manter essa estrutura ao alterar
  o script, senão o JS quebra.
- Município foi removido (fonte não tem o dado). Não recriar sem fonte confiável.

## Publicação

Push em `main` redeploya o Pages automaticamente. Verificar status em
Actions → "pages build and deployment".

## Admin / credenciais

- Manager de admin: `comissao.html` (Firebase Auth + Firestore: coleções
  `avisos` e `forms`).
- Credenciais de admin ficam em **`AGENTS.local.md`** (arquivo local, ignorado
  pelo `.gitignore`). **Nunca** versionar nem colar credenciais em arquivos que
  vão pro GitHub.
- Coleção `avisos`: campos `titulo`, `categoria`, `data`, `mensagem` (HTML),
  `link`/`linkTexto` (opcional), `createdAt` (serverTimestamp).
- Coleção `forms`: acessada pela página principal (`index.html`).
