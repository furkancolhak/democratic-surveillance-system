#!/bin/bash

# Surveillance System Setup Script
# Maximum security installation

set -e

echo "🚀 Starting Surveillance System Setup..."

# 1. Check .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "❗ IMPORTANT: Edit .env file with your secure credentials!"
    echo "   - Change DB_PASSWORD"
    echo "   - Change JWT_SECRET (use: openssl rand -hex 32)"
    echo "   - Configure SMTP settings"
    read -p "Press Enter after editing .env file..."
fi

# 2. Create secrets directory
echo "📁 Creating secrets directory..."
mkdir -p secrets
chmod 700 secrets

# 3. Generate SSL certificates (self-signed)
if [ ! -f ssl/cert.pem ]; then
    echo "🔐 Generating self-signed SSL certificates..."
    mkdir -p ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem -out ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Surveillance/CN=localhost"
    chmod 600 ssl/key.pem
    echo "✅ SSL certificates created"
fi

# 4. Create required directories
echo "📁 Creating required directories..."
mkdir -p encrypted_videos decrypted_videos violence_recordings totp_qr_codes/master totp_qr_codes/members

# 5. Check Docker installation
echo "🐳 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# 6. Load .env file
source .env

# 7. Start Docker containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

# 8. Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# 9. Initialize database
echo "🗄️  Initializing database..."
docker-compose exec -T app python init_database.py || true

# 10. Check Python dependencies (for local development)
if command -v python3 &> /dev/null; then
    echo "🐍 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Test the system:"
echo "      docker-compose exec app python test_system.py"
echo ""
echo "   2. Create master user:"
echo "      docker-compose exec app python master_user_manager.py <username> <email> <password>"
echo ""
echo "   3. Access the system:"
echo "      https://localhost (or your configured domain)"
echo ""
echo "   4. View logs:"
echo "      docker-compose logs -f app"
echo ""
echo "⚠️  SECURITY REMINDERS:"
echo "   - Keep secrets/ directory secure (chmod 700)"
echo "   - Never commit .env file to git"
echo "   - Backup master.key regularly"
echo "   - Use strong passwords for master users"
echo "   - Enable firewall rules for production"
echo ""
