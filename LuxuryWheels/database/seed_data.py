# Script auxiliar para popular a base de dados com registos de teste.

import os
from datetime import date, timedelta
import random
from database.queries import adicionar_veiculo, adicionar_cliente, criar_reserva

hoje = date.today()

# 1. CLIENTES (15 Clientes)
nomes = [
    ("Sara", "Nunes", "Lisboa"), ("Pedro", "Santos", "Porto"), ("Tiago", "Ferreira", "Braga"),
    ("Mariana", "Silva", "Coimbra"), ("Joao", "Pereira", "Faro"), ("Ines", "Costa", "Setubal"),
    ("Andre", "Rodrigues", "Aveiro"), ("Beatriz", "Almeida", "Viseu"), ("Rui", "Gomes", "Evora"),
    ("Catarina", "Martins", "Leiria"), ("Diogo", "Lopes", "Cascais"), ("Mafalda", "Ribeiro", "Sintra"),
    ("Goncalo", "Pinto", "Guimaraes"), ("Sofia", "Carvalho", "Portimao"), ("Miguel", "Teixeira", "Funchal")
]

for i, (p_nome, u_nome, cidade) in enumerate(nomes, start=1):
    nome_comp = "{} {}".format(p_nome, u_nome)
    nif_gerado = "250{:06d}".format(i)
    carta_gerada = "P-{:07d}".format(1000000 + i)
    tel_gerado = "91{:07d}".format(random.randint(1000000, 9999999))
    email_gerado = "{}.{}@email.com".format(p_nome.lower(), u_nome.lower())
    adicionar_cliente(nome_comp, nif_gerado, carta_gerada, tel_gerado, email_gerado, cidade)

print("15 Clientes inseridos com sucesso!")

# 2. VEÍCULOS (20 Viaturas variadas com Imagens Locais Geradas)
veiculos_base = [
    ("Renault", "Clio", "Carro", "Económico", "Manual", 5, "Gasolina", 40.0, "AC, Bluetooth"),
    ("Fiat", "500", "Carro", "Pequeno", "Manual", 4, "Gasolina", 38.0, "Sensor Estacionamento"),
    ("Volkswagen", "Golf", "Carro", "Médio", "Automático", 5, "Gasóleo", 60.0, "GPS, Apple CarPlay"),
    ("BMW", "Série 5", "Carro", "Grande", "Automático", 5, "Gasóleo", 130.0, "Bancos em Pele, Head-Up"),
    ("Mercedes-Benz", "GLC", "Carro", "SUV", "Automático", 5, "Híbrido", 110.0, "Câmara 360, Teto Panorâmico"),
    ("Toyota", "Land Cruiser", "Carro", "4x4", "Manual", 7, "Gasóleo", 140.0, "Tração 4x4 Reduzida, Guincho"),
    ("Porsche", "Panamera", "Carro", "Luxo", "Automático", 4, "Gasolina", 260.0, "Som Burmester, Modo Sport Plus"),
    ("Peugeot", "208", "Carro", "Económico", "Manual", 5, "Elétrico", 55.0, "Painel Digital 3D, AC"),
    ("Tesla", "Model 3", "Carro", "Médio", "Automático", 5, "Elétrico", 90.0, "Piloto Automático, Ecrã 15 pol"),
    ("Audi", "Q7", "Carro", "SUV", "Automático", 7, "Gasóleo", 160.0, "Suspensão a Ar, Faróis Matrix"),

    # Motos
    ("Honda", "PCX 125", "Moto", "Económico", "Automático", 2, "Gasolina", 30.0, "Top Case, Tomada USB"),
    ("Yamaha", "MT-07", "Moto", "Médio", "Manual", 2, "Gasolina", 65.0, "Travões ABS, Proteção Motor"),
    ("BMW", "R 1250 GS", "Moto", "4x4", "Manual", 2, "Gasolina", 115.0, "Malas Laterais, Punhos Aquecidos"),
    ("Ducati", "Panigale V2", "Moto", "Luxo", "Manual", 2, "Gasolina", 175.0, "Quickshifter, Controlo Tração"),

    # Carrinhas de Carga
    ("Renault", "Master", "Carrinha de Carga", "Grande", "Manual", 3, "Gasóleo", 85.0, "Capacidade 13m3, Degrau Traseiro"),
    ("Ford", "Transit Custom", "Carrinha de Carga", "Médio", "Manual", 6, "Gasóleo", 75.0, "Porta Lateral Dupla, Sensores"),

    # Camiões
    ("Volvo", "FH 500", "Camião", "Grande", "Automático", 2, "Gasóleo", 280.0, "Cabine Dormitório, Retarder"),
    ("Mercedes-Benz", "Actros", "Camião", "Grande", "Automático", 2, "Gasóleo", 290.0, "MirrorCam, Assistente Faixa"),

    # Autocarros
    ("Mercedes-Benz", "Tourismo", "Autocarro", "Grande", "Automático", 55, "Gasóleo", 450.0, "WC a bordo, Wi-Fi, Microfone"),
    ("Iveco", "Daily Minibus", "Autocarro", "Pequeno", "Manual", 19, "Gasóleo", 180.0, "Ar Condicionado Passageiros")
]

cores = ["Preto", "Branco", "Cinzento", "Azul", "Vermelho"]

for idx, v in enumerate(veiculos_base, start=1):
    marca, mod, tipo_v, cat_v, trans_v, passg, comb, preco, ext = v
    matricula = "LW-{:02d}-PT".format(idx)
    nome_img = "veiculo_{}.png".format(idx)

    # Cria o ficheiro .png local em assets/vehicles/ e devolve o caminho relativo
    caminho_img_relativo = "assets/vehicles/{}".format(nome_img)
    criar_placeholder(nome_img, "{} {}".format(marca, mod), tipo_v)

    offset_rev = random.choice([3, 11, 14, 45, 90]) # 3 dias ativa alerta urgente de 5 dias
    offset_insp = random.choice([4, 12, 60, 120])

    dados = {
        "matricula": matricula,
        "marca": marca,
        "modelo": mod,
        "ano": random.randint(2021, 2024),
        "tipo": tipo_v,
        "categoria": cat_v,
        "transmissao": trans_v,
        "num_passageiros": passg,
        "combustivel": comb,
        "cor": random.choice(cores),
        "quilometragem": random.randint(3000, 75000),
        "preco_diario": preco,
        "imagem_path": caminho_img_relativo, # Caminho do ficheiro local guardado na base de dados
        "extras": ext,
        "estado": "Disponível",
        "data_ultima_revisao": (hoje - timedelta(days=180)).isoformat(),
        "data_proxima_revisao": (hoje + timedelta(days=offset_rev)).isoformat(),
        "data_ultima_inspecao": (hoje - timedelta(days=365)).isoformat(),
        "data_proxima_inspecao": (hoje + timedelta(days=offset_insp)).isoformat()
    }
    adicionar_veiculo(dados)

print("20 Veículos inseridos com caminhos de imagem locais válidos!")

# 3. RESERVAS (15 Contratos de Aluguer)
for i in range(1, 16):
    carro_escolhido_id = i
    cliente_escolhido_id = (i % 15) + 1
    metodo_pag_id = (i % 4) + 1

    dias_duracao = random.randint(2, 6)
    dias_restantes = random.randint(1, 4)

    data_inicio_contrato = hoje - timedelta(days=(dias_duracao - dias_restantes))
    data_fim_contrato = data_inicio_contrato + timedelta(days=dias_duracao)

    criar_reserva(
        veiculo_id=carro_escolhido_id,
        cliente_id=cliente_escolhido_id,
        forma_pag_id=metodo_pag_id,
        data_inicio=data_inicio_contrato.isoformat(),
        data_fim=data_fim_contrato.isoformat(),
        km_inicial=random.randint(10000, 30000),
        valor_dia=70.0,
        obs="Contrato demonstrativo inicial."
    )

print("15 Reservas criadas com sucesso!")