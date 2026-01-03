#!/bin/bash

echo "========================================"
echo "Creator Support AI - Setup Script"
echo "========================================"
echo ""

echo "[1/4] Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - Please add your API keys!"
fi
deactivate
cd ..

echo ""
echo "[2/4] Setting up frontend..."
cd frontend
npm install
cd ..

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your API keys:"
echo "   - OPENAI_API_KEY"
echo "   - PINECONE_API_KEY"
echo ""
echo "2. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Visit http://localhost:3000"
echo ""
echo "See QUICKSTART.md for detailed instructions!"
echo "========================================"
