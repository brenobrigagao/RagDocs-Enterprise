set -e

echo "Criando tabelas (se ainda não existirem)..."
python scripts/init_db.py

echo "Iniciando API..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir src --reload-dir config