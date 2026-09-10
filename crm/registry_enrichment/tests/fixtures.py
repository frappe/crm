# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Offline fixtures for network-free tests.

``CNPJ_PACKAGE6`` is an anonymized snapshot of a package 6 response from the
registry API (synthetic CNPJ, fictitious company data). Tests take a deep copy
before mutating it, so the normalizer and mapper can be exercised without a
network call or a spent credit.
"""

from __future__ import annotations

import copy

CNPJ_PACKAGE6: dict = {
	"status": 1,
	"cnpj": "12.345.678/0001-95",
	"tipo": "Matriz",
	"razao": "TOKEN TEST LTDA",
	"fantasia": "TOKEN TEST",
	"capitalSocial": 95000,
	"inicioAtividade": "31/12/1999",
	"email": "CONTATO@EMPRESA.COM",
	"responsavel": "Joao Jose",
	"responsavelCpf": "111.222.333-44",
	"simplesNacional": {"optante": "Não", "inicio": "17/01/2020", "fim": "01/01/2023"},
	"matrizEndereco": {
		"cep": "39400-000",
		"tipo": "RUA",
		"logradouro": "DAS FLORES",
		"numero": "1",
		"complemento": "SALA 1",
		"bairro": "CENTRO",
		"cidade": "MONTES CLAROS",
		"uf": "MG",
	},
	"telefones": [{"ddd": "11", "numero": "22334454"}],
	"situacao": {
		"id": 4,
		"nome": "Inapta",
		"data": "03/04/2020",
		"motivo": {"id": 63, "descricao": "Omissão De Declarações"},
	},
	"naturezaJuridica": {"codigo": "2062", "descricao": "SOCIEDADE EMPRESARIA LIMITADA"},
	"cnae": {
		"fiscal": "6202300",
		"secao": "J",
		"descricao": "DESENVOLVIMENTO E LICENCIAMENTO DE PROGRAMAS DE COMPUTADOR CUSTOMIZAVEIS",
	},
	"porte": {"id": "03", "descricao": "EMPRESA DE PEQUENO PORTE"},
	"regimesTributarios": [
		{"ano": 2019, "regime_tributario": "SIMPLES NACIONAL"},
		{"ano": 2021, "regime_tributario": "LUCRO PRESUMIDO"},
	],
	"socios": [
		{
			"cpf_cnpj_socio": "111.222.333-44",
			"nome": "JOAO JOSE",
			"tipo": "Pessoa Física",
			"data_entrada": "2020-01-01",
			"qualificacao_socio": {"id": 49, "descricao": "Sócio-Administrador "},
		}
	],
	"pacoteUsado": 6,
	"saldo": 123,
	"consultaID": "11bb22cc33dd44ee",
	"delay": 0.3,
}


def cnpj_package6() -> dict:
	"""Return a fresh deep copy of the package 6 fixture."""
	return copy.deepcopy(CNPJ_PACKAGE6)
