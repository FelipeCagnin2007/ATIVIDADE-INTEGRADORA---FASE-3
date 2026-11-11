"""Dados simulados da colônia. Todos os valores de energia se referem a 1 hora."""


def criar_historico():
    """Cada posição das duas listas representa a mesma observação."""
    return {
        "vento_ms": [6, 8, 10, 12, 14],
        "energia_eolica_kwh": [12, 18, 24, 30, 36],
    }


def criar_hierarquia():
    """Dicionários com listas de filhos representam a árvore de sistemas."""
    return {
        "nome": "Colônia Aurora Siger",
        "filhos": [
            {
                "nome": "Sistema energético",
                "filhos": [
                    {"nome": "Geração solar", "filhos": []},
                    {"nome": "Geração eólica", "filhos": []},
                    {"nome": "Bateria", "filhos": []},
                ],
            },
            {
                "nome": "Serviços essenciais",
                "filhos": [
                    {"nome": "Suporte à vida", "filhos": []},
                    {"nome": "Comunicação", "filhos": []},
                ],
            },
            {
                "nome": "Serviços adiáveis",
                "filhos": [
                    {"nome": "Laboratório", "filhos": []},
                    {"nome": "Recreação", "filhos": []},
                ],
            },
        ],
    }


def criar_consumidores():
    """Prioridade 1 é a mais importante. Cada chamada cria uma lista nova."""
    return [
        {"nome": "Suporte à vida", "consumo_kwh": 30, "essencial": True, "prioridade": 1},
        {"nome": "Comunicação", "consumo_kwh": 10, "essencial": True, "prioridade": 1},
        {"nome": "Laboratório", "consumo_kwh": 20, "essencial": False, "prioridade": 2},
        {"nome": "Recreação", "consumo_kwh": 10, "essencial": False, "prioridade": 3},
    ]


def criar_cenarios():
    """Exemplos independentes: a reserva de um caso não passa para o próximo."""
    exemplos = [
        ("Déficit e economia", 11, 13, 30),
        ("Excedente para armazenar", 11, 53, 30),
        ("Bateria quase cheia", 11, 53, 95),
        ("Uso da reserva", 11, 28, 30),
        ("Falta de energia essencial", 6, 3, 10),
        ("Geração e consumo equilibrados", 11, 43, 30),
    ]
    cenarios = []
    for nome, vento_ms, solar_kwh, reserva_kwh in exemplos:
        cenarios.append({
            "nome": nome,
            "clima": {"vento_ms": vento_ms},
            "solar_kwh": solar_kwh,
            "reserva_kwh": reserva_kwh,
            "capacidade_kwh": 100,
            "consumidores": criar_consumidores(),
        })
    return cenarios
