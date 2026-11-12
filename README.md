# Gestão de energia da colônia Aurora Siger

Atividade integradora da Fase 3 de Ciências da Computação da FIAP.

Felipe Cagnin de Lima · Grupo 41.

O programa organiza os sistemas da colônia, estima a energia eólica a partir do vento e decide como distribuir a energia disponível. As mensagens mostram quando reduzir consumo, usar a bateria, armazenar uma sobra ou acionar emergência.

## Como executar

1. Tenha o Python 3 instalado.
2. Clique em **Code → Download ZIP** no GitHub e extraia a pasta.
3. Abra o terminal nessa pasta e execute:

```bash
python3 main.py
```

No Windows, se necessário, use `py main.py` ou `python main.py`.
Mantenha `dados.py`, `logica.py` e `main.py` na mesma pasta. Não é preciso instalar pacotes.

O programa executa seis exemplos independentes. Não pede informações no terminal nem altera arquivos.

## Organização dos arquivos

- `dados.py`: histórico, consumidores, hierarquia e cenários simulados.
- `logica.py`: regressão, navegação nos subsistemas e regras de decisão.
- `main.py`: integra os dados e exibe os resultados.
- `test_sistema.py`: testes automatizados com `unittest`, da biblioteca padrão.

## Organização dos dados

O histórico usa duas listas com posições correspondentes:

```python
vento_ms = [6, 8, 10, 12, 14]
energia_eolica_kwh = [12, 18, 24, 30, 36]
```

Cada cenário é um dicionário: guarda o clima, a energia solar prevista, a reserva, a capacidade da bateria e uma lista de consumidores. Os resultados também são guardados em uma lista durante a execução.

A hierarquia é uma árvore de dicionários com `nome` e uma lista de `filhos`. A função `listar_hierarquia` percorre esses filhos recursivamente:

```text
Colônia Aurora Siger
  Sistema energético
    Geração solar
    Geração eólica
    Bateria
  Serviços essenciais
    Suporte à vida
    Comunicação
  Serviços adiáveis
    Laboratório
    Recreação
```

## Modelo de previsão

Usamos regressão linear simples por mínimos quadrados, calculada com somas e operações aritméticas. O programa ajusta os coeficientes a partir das listas; a reta não é fixada no código.

```text
energia prevista = intercepto + inclinação × vento
inclinação = soma((vento - média dos ventos) × (energia - média das energias))
             / soma((vento - média dos ventos)²)
intercepto = média das energias - inclinação × média dos ventos
```

Para o histórico fornecido, a inclinação é 3 e o intercepto é -6:

```text
energia eólica prevista = 3 × vento - 6
vento = 11 m/s → energia eólica prevista = 27 kWh
```

O sistema impede previsões negativas e avisa se o vento estiver fora do intervalo histórico de 6 a 14 m/s. Um histórico com ventos todos iguais é rejeitado, pois não permite calcular a inclinação.

São dados inventados para a atividade, não medições de Marte. A reta exemplifica o método de regressão e não é uma curva física de uma turbina. Os pontos estão perfeitamente alinhados por construção; isso não comprova precisão para dados reais. O vento fornecido e a energia solar são estimativas para o próximo intervalo de uma hora, não previsões meteorológicas calculadas pelo sistema.

## Regras de decisão

Toda geração e todo consumo são expressos em **kWh para uma hora**. A reserva e sua capacidade também são expressas em kWh. Assim, o programa não soma potência em kW com energia em kWh.

1. Soma a energia solar e a previsão eólica.
2. Compara a geração com a demanda original e emite alerta, sugestão de armazenamento ou mensagem de equilíbrio.
3. Ativa economia quando há déficit **E** pelo menos uma destas condições: geração abaixo de 50 kWh, reserva abaixo de 20 kWh ou demanda maior que geração mais reserva.
4. Em economia, suspende consumidores não essenciais por prioridade: recreação antes do laboratório. Para quando a demanda restante cabe na geração ou não há outro consumidor adiável.
5. Se a geração ainda não bastar, usa a reserva até o limite disponível.
6. Se houver sobra, carrega a bateria até sua capacidade; a parcela restante gera orientação para limitar a geração excedente.
7. Se ainda faltar energia depois da bateria, declara o déficit e emite alerta crítico. Não afirma que os serviços essenciais foram atendidos quando não existe energia suficiente.

Os limites de 50 e 20 kWh são escolhas didáticas, não normas de segurança. Prioridade 1 é a mais importante. Suporte à vida e comunicação nunca são desligados automaticamente. O laboratório do exemplo realiza atividades adiáveis, sem processos críticos.

As cargas são suspensas por inteiro, não parcialmente. A simulação considera carga e descarga sem perdas, sem limite de potência e sem persistência entre cenários. Não controla equipamentos reais nem garante continuidade em uma emergência.

## Exemplo de entrada e saída

O primeiro exemplo equivale a estes dados:

```python
vento_ms = 11
solar_kwh = 13
reserva_kwh = 30
capacidade_kwh = 100
# Demanda: suporte à vida 30, comunicação 10, laboratório 20, recreação 10.
```

Trecho da saída real de `python3 main.py`:

```text
CENÁRIO: Déficit e economia
Vento: 11.0 m/s
Previsão eólica: 27.0 kWh
Geração solar: 13.0 kWh
Geração total: 40.0 kWh
Consumo solicitado: 70.0 kWh
Consumo após decisão: 40.0 kWh
Reserva inicial: 30.0 kWh
Retirada da bateria: 0.0 kWh
Energia armazenada: 0.0 kWh
Reserva final: 30.0 kWh
Excedente sem armazenamento: 0.0 kWh
Déficit não atendido: 0.0 kWh
Serviços mantidos no plano: Suporte à vida, Comunicação
ALERTA: consumo maior que geração.
AÇÃO: ativar modo economia e reduzir consumo adiável.
SUSPENDER: Recreação, Laboratório.
```

Os outros exemplos mostram excedente, bateria quase cheia, uso da reserva, falta de energia essencial e equilíbrio.

Para experimentar, altere os exemplos em `criar_cenarios`, no arquivo `dados.py`, e execute novamente. Por exemplo, aumente a energia solar ou diminua a reserva e compare as decisões. Não altere apenas um consumo total: o total é calculado a partir dos consumidores.

## Testes

Na pasta do projeto, execute:

```bash
python3 -m unittest -v
```

Os testes verificam regressão, entradas inválidas, hierarquia, prioridades, limites da bateria, extrapolação e execução completa. Também conferem a conservação de energia e a preservação das prioridades em 77 combinações de geração e reserva.

## Entrega

Repositório público: https://github.com/FelipeCagnin2007/ATIVIDADE-INTEGRADORA---FASE-3
O relatório em PDF foi entregue na plataforma da FIAP ON.
