"""Regressão, navegação na hierarquia e decisões, sem entrada ou impressão."""

from math import isfinite


GERACAO_BAIXA_KWH = 50
RESERVA_BAIXA_KWH = 20


def validar_numero(valor, nome):
    """Não aceita números negativos, booleanos, infinito ou valores ausentes."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{nome} deve ser um número.")
    if not isfinite(valor) or valor < 0:
        raise ValueError(f"{nome} deve ser finito e não negativo.")


def ajustar_regressao(ventos, energias):
    """Ajusta energia = intercepto + inclinação * vento por mínimos quadrados."""
    if len(ventos) != len(energias) or len(ventos) < 2:
        raise ValueError("Informe ao menos dois pares de vento e energia.")
    for vento, energia in zip(ventos, energias):
        validar_numero(vento, "Vento histórico")
        validar_numero(energia, "Energia histórica")

    media_vento = sum(ventos) / len(ventos)
    media_energia = sum(energias) / len(energias)
    soma_produtos = 0
    soma_quadrados = 0
    for vento, energia in zip(ventos, energias):
        soma_produtos += (vento - media_vento) * (energia - media_energia)
        soma_quadrados += (vento - media_vento) ** 2
    if soma_quadrados == 0:
        raise ValueError("O histórico precisa ter velocidades de vento diferentes.")

    inclinacao = soma_produtos / soma_quadrados
    return {
        "inclinacao": inclinacao,
        "intercepto": media_energia - inclinacao * media_vento,
        "vento_minimo_ms": min(ventos),
        "vento_maximo_ms": max(ventos),
    }


def prever_energia_eolica(modelo, vento_ms):
    """A previsão não pode representar geração negativa."""
    validar_numero(vento_ms, "Vento previsto")
    energia_estimada = modelo["intercepto"] + modelo["inclinacao"] * vento_ms
    return max(0, energia_estimada)


def listar_hierarquia(sistema, nivel=0):
    """Percorre os filhos recursivamente e devolve linhas para exibição."""
    linhas = ["  " * nivel + "- " + sistema["nome"]]
    for filho in sistema["filhos"]:
        linhas.extend(listar_hierarquia(filho, nivel + 1))
    return linhas


def validar_consumidores(consumidores):
    if not isinstance(consumidores, list) or not consumidores:
        raise ValueError("Informe uma lista não vazia de consumidores.")
    nomes = set()
    for consumidor in consumidores:
        nome = consumidor.get("nome")
        if not isinstance(nome, str) or not nome.strip() or nome in nomes:
            raise ValueError("Os nomes dos consumidores devem ser preenchidos e únicos.")
        nomes.add(nome)
        validar_numero(consumidor.get("consumo_kwh"), "Consumo")
        if not isinstance(consumidor.get("essencial"), bool):
            raise ValueError("O campo essencial deve ser True ou False.")
        prioridade = consumidor.get("prioridade")
        if type(prioridade) is not int or prioridade < 1:
            raise ValueError("A prioridade deve ser um inteiro positivo.")


def prioridade_do_consumidor(consumidor):
    return consumidor["prioridade"]


def decidir_uso_energia(geracao_kwh, reserva_kwh, capacidade_kwh, consumidores):
    """Planeja uma hora sem alterar os dados recebidos ou desligar essenciais."""
    for valor, nome in [
        (geracao_kwh, "Geração"),
        (reserva_kwh, "Reserva"),
        (capacidade_kwh, "Capacidade da bateria"),
    ]:
        validar_numero(valor, nome)
    if reserva_kwh > capacidade_kwh:
        raise ValueError("A reserva não pode superar a capacidade da bateria.")
    validar_consumidores(consumidores)

    consumo_original = sum(item["consumo_kwh"] for item in consumidores)
    consumo_planejado = consumo_original
    mensagens = []
    desligados = []

    if consumo_original > geracao_kwh:
        mensagens.append("ALERTA: consumo maior que geração.")
    elif geracao_kwh > consumo_original:
        mensagens.append("SUGESTÃO: armazenar energia excedente.")
    else:
        mensagens.append("NORMAL: geração e consumo equilibrados.")

    ha_deficit = consumo_original > geracao_kwh
    geracao_baixa = geracao_kwh < GERACAO_BAIXA_KWH
    reserva_baixa = reserva_kwh < RESERVA_BAIXA_KWH
    energia_insuficiente = consumo_original > geracao_kwh + reserva_kwh
    modo_economia = ha_deficit and (geracao_baixa or reserva_baixa or energia_insuficiente)

    if modo_economia:
        mensagens.append("AÇÃO: ativar modo economia e reduzir consumo adiável.")
        adiaveis = [item for item in consumidores if not item["essencial"]]
        # Maior número significa menor prioridade: recreação sai antes do laboratório.
        adiaveis = sorted(adiaveis, key=prioridade_do_consumidor, reverse=True)
        for consumidor in adiaveis:
            if consumo_planejado <= geracao_kwh:
                break
            if consumidor["consumo_kwh"] > 0:
                desligados.append(consumidor["nome"])
                consumo_planejado -= consumidor["consumo_kwh"]

    # Primeiro atendemos a demanda; só a sobra pode ser armazenada.
    falta_apos_geracao = max(0, consumo_planejado - geracao_kwh)
    retirada_bateria = min(reserva_kwh, falta_apos_geracao)
    deficit_nao_atendido = falta_apos_geracao - retirada_bateria
    sobra_geracao = max(0, geracao_kwh - consumo_planejado)
    energia_armazenada = min(sobra_geracao, capacidade_kwh - reserva_kwh)
    excedente_sem_armazenamento = sobra_geracao - energia_armazenada
    reserva_final = reserva_kwh - retirada_bateria + energia_armazenada

    if desligados:
        mensagens.append("SUSPENDER: " + ", ".join(desligados) + ".")
    if deficit_nao_atendido > 0:
        mensagens.append("CRÍTICO: energia insuficiente até para os serviços mantidos; acionar emergência.")
    elif retirada_bateria > 0:
        mensagens.append("AÇÃO: usar a reserva para completar a energia necessária.")
    elif energia_armazenada > 0:
        mensagens.append("AÇÃO: carregar a bateria com o excedente.")
    if excedente_sem_armazenamento > 0:
        mensagens.append("ATENÇÃO: bateria sem espaço para toda a sobra; limitar a geração excedente.")
    if reserva_final < RESERVA_BAIXA_KWH:
        mensagens.append("ATENÇÃO: reserva abaixo de 20 kWh; priorizar sua reposição.")

    return {
        "modo_economia": modo_economia,
        "consumo_original_kwh": consumo_original,
        "consumo_planejado_kwh": consumo_planejado,
        "desligados": desligados,
        "mantidos": [item["nome"] for item in consumidores if item["nome"] not in desligados],
        "retirada_bateria_kwh": retirada_bateria,
        "energia_armazenada_kwh": energia_armazenada,
        "excedente_kwh": excedente_sem_armazenamento,
        "deficit_kwh": deficit_nao_atendido,
        "reserva_final_kwh": reserva_final,
        "mensagens": mensagens,
    }


def analisar_cenario(cenario, modelo):
    """Integra clima, previsão e decisões para o próximo intervalo de uma hora."""
    vento_ms = cenario["clima"]["vento_ms"]
    validar_numero(cenario["solar_kwh"], "Energia solar")
    energia_eolica = prever_energia_eolica(modelo, vento_ms)
    geracao_total = cenario["solar_kwh"] + energia_eolica
    decisao = decidir_uso_energia(
        geracao_total, cenario["reserva_kwh"],
        cenario["capacidade_kwh"], cenario["consumidores"],
    )
    extrapolacao = not modelo["vento_minimo_ms"] <= vento_ms <= modelo["vento_maximo_ms"]
    if extrapolacao:
        decisao["mensagens"].insert(0, "ATENÇÃO: vento fora do histórico; previsão por extrapolação.")
    return {
        "nome": cenario["nome"],
        "vento_ms": vento_ms,
        "solar_kwh": cenario["solar_kwh"],
        "eolica_prevista_kwh": energia_eolica,
        "geracao_total_kwh": geracao_total,
        "reserva_inicial_kwh": cenario["reserva_kwh"],
        "extrapolacao": extrapolacao,
        "decisao": decisao,
    }
