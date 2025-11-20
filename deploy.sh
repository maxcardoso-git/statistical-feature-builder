#!/bin/bash

# deploy.sh - Script de deploy automático para SFB
# Executa localmente após fazer commit

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy do SFB para o servidor..."

# Verificar se há mudanças não commitadas
if [[ -n $(git status -s) ]]; then
    echo "⚠️  Você tem mudanças não commitadas. Por favor, commit antes de fazer deploy."
    echo ""
    git status -s
    exit 1
fi

# Fazer push para o Git
echo "📤 Enviando código para o repositório..."
git push origin main

# SSH no servidor e atualizar
echo "🔗 Conectando ao servidor..."
ssh root@72.61.52.70 << 'ENDSSH'
    set -e

    cd /var/www/SFB

    echo "📥 Baixando últimas mudanças..."
    git pull origin main

    echo "📦 Criando ambiente virtual Python..."
    python3 -m venv venv || true

    echo "📦 Instalando dependências..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    echo "🔄 Reiniciando serviço SFB..."
    pm2 restart sfb-service || pm2 start ecosystem.config.cjs

    echo "✅ Deploy do SFB completed!"

    # Mostrar status dos serviços
    echo ""
    echo "📊 Status dos serviços:"
    pm2 status
ENDSSH

echo ""
echo "🎉 Deploy do SFB finalizado com sucesso!"
echo "📱 Serviço disponível em:"
echo "   API: http://72.61.52.70:8000"
echo "   Docs: http://72.61.52.70:8000/docs"
echo ""
