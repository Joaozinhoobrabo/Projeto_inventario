# Inventário Inteligente

Projeto Django em português para inventário compartilhado de frotas, com PostgreSQL e seleção de perfil sem senha.

## Ambiente local (macOS)

Pré-requisitos: Python 3.12 ou superior e Homebrew.

1. Instale e inicie o PostgreSQL 17:

   ```sh
   brew install postgresql@17
   brew services start postgresql@17
   ```

2. Crie o banco de desenvolvimento:

   ```sh
   /opt/homebrew/opt/postgresql@17/bin/createdb inventario_db
   ```

   Se o banco já existir, não precisa recriá-lo.

3. Ative o ambiente virtual e instale as dependências:

   ```sh
   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

4. Configure o acesso ao PostgreSQL. Por padrão, o projeto usa `inventario_db`, o usuário atual do macOS, `localhost` e a porta `5432`. Se seu banco usa outros valores, exporte `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST` e `PGPORT` no terminal antes de iniciar o Django.

5. Crie e aplique as migrations e verifique a configuração:

   ```sh
   python manage.py makemigrations inventario
   python manage.py migrate
   python manage.py check
   python manage.py test inventario
   ```

6. Inicie o site:

   ```sh
   python manage.py runserver
   ```

   Abra http://127.0.0.1:8000.

## Funcionalidades disponíveis

- Seleção de perfil ADMIN ou USUÁRIO sem login nem senha.
- Painel com total de frotas, inventariadas, pendentes e percentual concluído.
- Busca por número da frota, com descrição, equipamentos, números de série e status.
- Lista compartilhada de frotas inventariadas e respectivos equipamentos para ADMIN e USUÁRIO.
- ADMIN e USUÁRIO podem remover equipamentos de frotas inventariadas; a remoção registra item, série e perfil no histórico.
- Cadastro e edição de frota e vários equipamentos no mesmo formulário (ADMIN).
- Exclusão de frota com confirmação (equipamentos são removidos junto; histórico preservado).
- Inventariar e desinventariar a frota inteira para ADMIN ou USUÁRIO, com confirmação e histórico de cada transição.

## Regras dos dados

- `Frota` guarda o status do inventário, que começa como `PENDENTE`.
- `Equipamento` pertence a uma frota e não tem status de inventário próprio.
- `Historico` registra frota, perfil escolhido, ação e data/hora. O número da frota é preservado no registro mesmo se a frota for removida.
- Ao remover um equipamento inventariado, o registro do equipamento é excluído e os demais itens/frota permanecem; o evento fica no histórico. A remoção não possui restauração automática.
- A seleção ADMIN/USUÁRIO é uma preferência de interface armazenada na sessão, não autenticação e não identificação confiável. Não há senha nem login tradicional.

O perfil ADMIN não protege operações contra visitantes: qualquer pessoa com o link pode selecioná-lo. Não publique esta versão como sistema protegido. Em produção, defina `DJANGO_SECRET_KEY` com um valor secreto e forte, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` e as variáveis PostgreSQL; a seleção de perfil não substitui autenticação.

## Próximas etapas

Próximas etapas: busca por número de série, histórico e dashboard detalhado; importação de Excel/CSV; perguntas respondidas exclusivamente com dados do banco; preparação de publicação.