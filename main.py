"""Execute com python3 main.py. Não é necessário instalar pacotes."""

from dados import criar_cenarios, criar_hierarquia, criar_historico
from logica import ajustar_regressao, analisar_cenario, listar_hierarquia


def exibir_resultado(resultado):
    decisao = resultado["decisao"]
    print(f'\nCENÁRIO: {resultado["nome"]}')
    print(f'Vento: {resultado["vento_ms"]:.1f} m/s')
    print(f'Previsão eólica: {resultado["eolica_prevista_kwh"]:.1f} kWh')
    print(f'Geração solar: {resultado["solar_kwh"]:.1f} kWh')
    print(f'Geração total: {resultado["geracao_total_kwh"]:.1f} kWh')
    print(f'Consumo solicitado: {decisao["consumo_original_kwh"]:.1f} kWh')
    print(f'Consumo após decisão: {decisao["consumo_planejado_kwh"]:.1f} kWh')
    print(f'Reserva inicial: {resultado["reserva_inicial_kwh"]:.1f} kWh')
    print(f'Retirada da bateria: {decisao["retirada_bateria_kwh"]:.1f} kWh')
    print(f'Energia armazenada: {decisao["energia_armazenada_kwh"]:.1f} kWh')
    print(f'Reserva final: {decisao["reserva_final_kwh"]:.1f} kWh')
    print(f'Excedente sem armazenamento: {decisao["excedente_kwh"]:.1f} kWh')
    print(f'Déficit não atendido: {decisao["deficit_kwh"]:.1f} kWh')
    print('Serviços mantidos no plano: ' + ', '.join(decisao["mantidos"]))
    for mensagem in decisao["mensagens"]:
        print(mensagem)


def main():
    print("AURORA SIGER - GESTÃO DE ENERGIA DA COLÔNIA")
    print("Simulação didática. Cada cenário é independente e representa 1 hora.")
    print("\nORGANIZAÇÃO DOS SISTEMAS")
    for linha in listar_hierarquia(criar_hierarquia()):
        print(linha)

    historico = criar_historico()
    modelo = ajustar_regressao(historico["vento_ms"], historico["energia_eolica_kwh"])
    print("\nMODELO AJUSTADO AO HISTÓRICO")
    print(f'Energia eólica (kWh) = {modelo["inclinacao"]:.1f} * vento (m/s) '
          f'+ ({modelo["intercepto"]:.1f})')

    resultados = []
    for cenario in criar_cenarios():
        resultado = analisar_cenario(cenario, modelo)
        resultados.append(resultado)
        exibir_resultado(resultado)
    print(f"\nConcluído: {len(resultados)} cenários analisados.")
    print("Os resultados ficam em uma lista em memória, sem controle de equipamentos reais.")


if __name__ == "__main__":
    main()
