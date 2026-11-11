"""Testes da regressão, das prioridades e do balanço de energia."""

from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
import unittest

from dados import criar_cenarios, criar_consumidores, criar_hierarquia, criar_historico
from logica import (
    ajustar_regressao, analisar_cenario, decidir_uso_energia,
    listar_hierarquia, prever_energia_eolica,
)
from main import main


class TesteRegressao(unittest.TestCase):
    def setUp(self):
        historico = criar_historico()
        self.modelo = ajustar_regressao(historico["vento_ms"], historico["energia_eolica_kwh"])

    def test_ajusta_reta_do_historico(self):
        self.assertAlmostEqual(self.modelo["inclinacao"], 3)
        self.assertAlmostEqual(self.modelo["intercepto"], -6)
        self.assertAlmostEqual(prever_energia_eolica(self.modelo, 11), 27)

    def test_calcula_outra_reta_sem_coeficientes_fixos(self):
        modelo = ajustar_regressao([1, 2, 3], [2, 5, 5])
        self.assertAlmostEqual(modelo["inclinacao"], 1.5)
        self.assertAlmostEqual(modelo["intercepto"], 1)

    def test_rejeita_historico_invalido(self):
        for ventos, energias in [([], []), ([1], [2]), ([1, 2], [3]), ([2, 2], [3, 5])]:
            with self.subTest(ventos=ventos, energias=energias):
                with self.assertRaises(ValueError):
                    ajustar_regressao(ventos, energias)

    def test_rejeita_numeros_invalidos(self):
        for valor in [-1, True, "11", float("nan"), float("inf")]:
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    prever_energia_eolica(self.modelo, valor)
                with self.assertRaises(ValueError):
                    ajustar_regressao([6, 8], [12, valor])

    def test_energia_nunca_negativa(self):
        self.assertEqual(prever_energia_eolica(self.modelo, 0), 0)

    def test_sinaliza_extrapolacao(self):
        cenario = criar_cenarios()[0]
        cenario["clima"]["vento_ms"] = 18
        resultado = analisar_cenario(cenario, self.modelo)
        self.assertTrue(resultado["extrapolacao"])
        self.assertIn("extrapolação", resultado["decisao"]["mensagens"][0])
        self.assertFalse(analisar_cenario(criar_cenarios()[0], self.modelo)["extrapolacao"])


class TesteDecisoes(unittest.TestCase):
    def decidir(self, geracao, reserva=30, capacidade=100):
        return decidir_uso_energia(geracao, reserva, capacidade, criar_consumidores())

    def test_economia_prioriza_essenciais(self):
        decisao = self.decidir(40)
        self.assertTrue(decisao["modo_economia"])
        self.assertEqual(decisao["desligados"], ["Recreação", "Laboratório"])
        self.assertEqual(decisao["mantidos"], ["Suporte à vida", "Comunicação"])
        self.assertEqual(decisao["consumo_planejado_kwh"], 40)
        self.assertEqual(decisao["reserva_final_kwh"], 30)

    def test_armazena_excedente(self):
        decisao = self.decidir(80)
        self.assertFalse(decisao["modo_economia"])
        self.assertEqual(decisao["energia_armazenada_kwh"], 10)
        self.assertEqual(decisao["reserva_final_kwh"], 40)

    def test_respeita_capacidade_da_bateria(self):
        decisao = self.decidir(80, reserva=95)
        self.assertEqual(decisao["energia_armazenada_kwh"], 5)
        self.assertEqual(decisao["reserva_final_kwh"], 100)
        self.assertEqual(decisao["excedente_kwh"], 5)

    def test_usa_reserva_quando_a_politica_permite(self):
        decisao = self.decidir(55)
        self.assertFalse(decisao["modo_economia"])
        self.assertEqual(decisao["desligados"], [])
        self.assertEqual(decisao["retirada_bateria_kwh"], 15)
        self.assertEqual(decisao["reserva_final_kwh"], 15)

    def test_alerta_se_nem_essenciais_puderem_ser_atendidos(self):
        decisao = self.decidir(15, reserva=10)
        self.assertEqual(decisao["retirada_bateria_kwh"], 10)
        self.assertEqual(decisao["deficit_kwh"], 15)
        self.assertEqual(decisao["reserva_final_kwh"], 0)
        self.assertTrue(any("CRÍTICO" in mensagem for mensagem in decisao["mensagens"]))

    def test_equilibrio_nao_altera_reserva(self):
        decisao = self.decidir(70)
        self.assertEqual(decisao["desligados"], [])
        self.assertEqual(decisao["retirada_bateria_kwh"], 0)
        self.assertEqual(decisao["energia_armazenada_kwh"], 0)
        self.assertEqual(decisao["reserva_final_kwh"], 30)

    def test_limites_de_economia(self):
        self.assertTrue(self.decidir(49)["modo_economia"])
        self.assertFalse(self.decidir(50)["modo_economia"])
        self.assertTrue(self.decidir(60, reserva=19)["modo_economia"])
        self.assertFalse(self.decidir(60, reserva=20)["modo_economia"])

    def test_reduz_demanda_que_supera_geracao_mais_reserva(self):
        consumidores = criar_consumidores()
        consumidores[-1]["consumo_kwh"] = 100
        decisao = decidir_uso_energia(60, 20, 100, consumidores)
        self.assertTrue(decisao["modo_economia"])
        self.assertEqual(decisao["desligados"], ["Recreação"])
        self.assertEqual(decisao["deficit_kwh"], 0)

    def test_nao_precisa_desligar_todos_os_adiaveis(self):
        decisao = self.decidir(60, reserva=10)
        self.assertEqual(decisao["desligados"], ["Recreação"])
        self.assertEqual(decisao["consumo_planejado_kwh"], 60)

    def test_funciona_sem_bateria(self):
        decisao = self.decidir(80, reserva=0, capacidade=0)
        self.assertEqual(decisao["reserva_final_kwh"], 0)
        self.assertEqual(decisao["excedente_kwh"], 10)

    def test_rejeita_energia_ou_capacidade_invalida(self):
        for geracao, reserva, capacidade in [(-1, 0, 100), (40, 101, 100), (40, 0, -1), (float("inf"), 0, 100)]:
            with self.subTest(geracao=geracao, reserva=reserva, capacidade=capacidade):
                with self.assertRaises(ValueError):
                    self.decidir(geracao, reserva, capacidade)

    def test_rejeita_consumidores_invalidos(self):
        for campo, valor in [("consumo_kwh", -1), ("essencial", "sim"), ("prioridade", 0), ("nome", "")]:
            consumidores = criar_consumidores()
            consumidores[0][campo] = valor
            with self.subTest(campo=campo):
                with self.assertRaises(ValueError):
                    decidir_uso_energia(40, 30, 100, consumidores)
        with self.assertRaises(ValueError):
            decidir_uso_energia(40, 30, 100, [])

    def test_balanco_e_prioridades_em_77_combinacoes(self):
        consumidores = criar_consumidores()
        original = deepcopy(consumidores)
        for geracao in [0, 15, 40, 49, 50, 55, 60, 70, 80, 100, 200]:
            for reserva in [0, 10, 19, 20, 30, 95, 100]:
                with self.subTest(geracao=geracao, reserva=reserva):
                    decisao = decidir_uso_energia(geracao, reserva, 100, consumidores)
                    self.assertGreaterEqual(decisao["reserva_final_kwh"], 0)
                    self.assertLessEqual(decisao["reserva_final_kwh"], 100)
                    self.assertGreaterEqual(decisao["deficit_kwh"], 0)
                    self.assertAlmostEqual(
                        geracao + decisao["retirada_bateria_kwh"] + decisao["deficit_kwh"],
                        decisao["consumo_planejado_kwh"] + decisao["energia_armazenada_kwh"] + decisao["excedente_kwh"],
                    )
                    self.assertAlmostEqual(
                        decisao["reserva_final_kwh"],
                        reserva - decisao["retirada_bateria_kwh"] + decisao["energia_armazenada_kwh"],
                    )
                    self.assertIn("Suporte à vida", decisao["mantidos"])
                    self.assertIn("Comunicação", decisao["mantidos"])
                    self.assertFalse(decisao["retirada_bateria_kwh"] > 0 and decisao["energia_armazenada_kwh"] > 0)
        self.assertEqual(consumidores, original)


class TesteIntegracao(unittest.TestCase):
    def test_navega_na_hierarquia(self):
        linhas = listar_hierarquia(criar_hierarquia())
        self.assertEqual(len(linhas), 11)
        self.assertIn("    - Geração eólica", linhas)
        self.assertIn("    - Suporte à vida", linhas)

    def test_cenarios_sao_independentes(self):
        cenarios = criar_cenarios()
        cenarios[0]["consumidores"][0]["consumo_kwh"] = 999
        self.assertEqual(cenarios[1]["consumidores"][0]["consumo_kwh"], 30)

    def test_analise_nao_muda_entrada(self):
        cenario = criar_cenarios()[0]
        original = deepcopy(cenario)
        historico = criar_historico()
        modelo = ajustar_regressao(historico["vento_ms"], historico["energia_eolica_kwh"])
        self.assertEqual(analisar_cenario(cenario, modelo)["geracao_total_kwh"], 40)
        self.assertEqual(cenario, original)

    def test_execucao_completa(self):
        saida = StringIO()
        with redirect_stdout(saida):
            main()
        self.assertIn("Concluído: 6 cenários analisados.", saida.getvalue())
        self.assertIn("Previsão eólica: 27.0 kWh", saida.getvalue())
        self.assertIn("CRÍTICO", saida.getvalue())


if __name__ == "__main__":
    unittest.main()
