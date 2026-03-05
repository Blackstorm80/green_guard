#!/bin/bash
echo "🚀 Démarrage Green Guard API..."
docker-compose up --build -d
echo "✅ API dispo sur http://localhost:8000/docs"
echo "📊 Logs: docker-compose logs -f"