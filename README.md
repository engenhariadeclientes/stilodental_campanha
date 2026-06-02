# BotConversa Stilo — Atualização de Campos Personalizados

Script que atualiza os campos `proced_orcado` e `valor_orcado` nos contatos do BotConversa para a campanha de reativação da Stilo Dental.

---

## Arquivos

| Arquivo | Descrição |
|---|---|
| `main.py` | Script principal |
| `dados_pacientes.csv` | 149 pacientes com telefone, procedimento e valor |
| `contatos.xlsx` | Planilha BotConversa (importação manual) |
| `requirements.txt` | Dependências Python |
| `Procfile` | Configuração Railway |

---

## Deploy no Railway

### 1. Criar repositório no GitHub
- Suba todos os arquivos desta pasta para um repositório **privado** no GitHub

### 2. Criar projeto no Railway
- Acesse [railway.app](https://railway.app)
- **New Project → Deploy from GitHub repo**
- Selecione o repositório

### 3. Configurar variável de ambiente
No Railway, vá em **Variables** e adicione:
```
BOTCONVERSA_API_KEY = sua_chave_aqui
```

### 4. Executar
- Railway detecta o `Procfile` e inicia o worker automaticamente
- Acompanhe os logs em tempo real na aba **Logs**

---

## O que o script faz

1. Lê o arquivo `dados_pacientes.csv`
2. Para cada paciente, busca o contato no BotConversa pelo telefone
3. Atualiza os campos personalizados:
   - `proced_orcado` → ex: "Tratamento odontológico"
   - `valor_orcado` → ex: "R$ 2.500,00"
4. Aguarda 1,2s entre cada chamada (respeita rate limit da API)
5. Exibe log completo: ✓ atualizado / não encontrado / erro

---

## Resultado esperado no log

```
[1/149] Saulo Rico dos Santos (5547999409960)
  → ✓ Atualizado | Tratamento odontológico | R$ 6.820,00
[2/149] Lucimara Linhares dos Santos (5547984116360)
  → ✓ Atualizado | Tratamento odontológico | R$ 1.490,00
...
CONCLUÍDO: 147 atualizados | 2 não encontrados | 0 erros
```

---

## Observação
Os contatos precisam estar **importados no BotConversa antes** de rodar o script.
Use o arquivo `contatos.xlsx` para a importação manual.
