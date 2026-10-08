# LUXURY WHEELS — Gestão de Frotas

Aplicação desktop desenvolvida em **Python** com **CustomTkinter** e **SQLite** para a gestão completa de frotas de veículos, clientes, reservas e faturação.

---

## Funcionalidades Principais

* **Dashboard Executivo:** Página inicial com toda a informação (em gráficos e tabelas) relevante à gestão de frotas: total financeiro, reservas do mês, veículos disponíveis, veículos alugados, próximas manutenções e novos clintes.
* **Gestão de Veículos:** Inventário completo com fichas técnicas dos veículos (ordenável por títulos ou filtros), que inclui: fotografias, quilometragem, número de passageiros, matrícula, entre outros.
* **Gestão de Clientes:** Inventário de clientes, que engloba validação de NIF, número da carta de condução, contactos e região.
* **Gestão de Reservas:** 
  * Listagem com organização cronológica: reservas ativas no topo, com alerta visual para prazos que terminam no próprio dia (sinal de alerta com !) e para entregas com atraso (com !).
  * Possibilidade de filtrar por estado da reserva e tipo de veículo.
  * Cálculo dos valores a cobrar por atraso/prorrogação ou a restituir por devolução antecipada.
* **Gestão de Formas de Pagamento:** Inventário das possíveis formas de pagamento.
* As páginas de **Gestão de Veículos, Clientes, Reservas e Formas de Pagamento**, para além de listar a informação, têm tambéma possibilidade de:
  * Exportação para **Excel (`.xlsx`)** e **CSV (UTF-8)**.
  * Alteração de informação.
  * Adição de novos registos.
  * Remoção de registos.

---

## Dados de Acesso e Segurança

### 1. Início de Sessão (Login)
Ao iniciar a aplicação pela primeira vez, a base de dados é gerada automaticamente e popula um administrador por defeito:
* **Utilizador:** `admin`
* **Palavra-passe:** `admin123`

### 2. Registo de Novos Operadores
Para garantir a segurança do sistema e impedir acessos não autorizados, a criação de novas contas exige a introdução de um **Código de Empresa / Operador** válido:
* **Código de Registo:** `LUXURY2026`

---

## Requisitos e Instalação

Para conseguir utilizar a aplicação de desktop, deverá ter o **Python** instalado no sistema e as seguintes dependências configuradas no teu ambiente virtual (`venv`):

        pip install customtkinter matplotlib openpyxl pillow