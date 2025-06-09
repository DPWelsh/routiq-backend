#!/usr/bin/env python3
"""
SurfRehab v2 - Multi-Tenant SaaS Setup Script
Initialize the platform for multi-tenant operations
"""

import os
import sys
import logging
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiTenantSetup:
    """Setup script for multi-tenant SaaS platform"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / '.env'
        
    def generate_encryption_key(self) -> str:
        """Generate a new encryption key for credential storage"""
        return Fernet.generate_key().decode()
    
    def create_env_file(self, force: bool = False):
        """Create .env file with required environment variables"""
        if self.env_file.exists() and not force:
            logger.info("✅ .env file already exists")
            return
        
        encryption_key = self.generate_encryption_key()
        
        env_content = f"""# SurfRehab v2 - Multi-Tenant Configuration

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# Clerk.com Configuration
CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key_here
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Security - Credentials Encryption
CREDENTIALS_ENCRYPTION_KEY={encryption_key}

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
TIMEZONE=UTC

# Background Jobs (optional)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# API Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
"""
        
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        logger.info(f"✅ Created .env file at {self.env_file}")
        logger.warning("🔒 Please update the placeholder values with your actual credentials")
    
    def setup_database_schema(self):
        """Setup database schema for multi-tenant operations"""
        sql_files = [
            "sql/01_initial_schema.sql",
            "sql/02_analytics_views.sql", 
            "sql/03_data_cleanup.sql",
            "sql/04_multi_tenant_enhancements.sql"
        ]
        
        for sql_file in sql_files:
            file_path = self.project_root / sql_file
            if not file_path.exists():
                logger.warning(f"⚠️  SQL file not found: {sql_file}")
                continue
            
            logger.info(f"🔄 Executing {sql_file}")
            try:
                with open(file_path, 'r') as f:
                    sql_content = f.read()
                
                # Execute SQL
                with db.get_cursor() as cursor:
                    cursor.execute(sql_content)
                    db.connection.commit()
                
                logger.info(f"✅ Executed {sql_file}")
                
            except Exception as e:
                logger.error(f"❌ Failed to execute {sql_file}: {e}")
                return False
        
        return True
    
    def create_sample_organization(self):
        """Create a sample organization for testing"""
        sample_org = {
            'id': 'org_sample_123',
            'name': 'Sample Healthcare Practice',
            'slug': 'sample-practice',
            'subscription_status': 'trial',
            'settings': json.dumps({
                'timezone': 'America/New_York',
                'business_hours': {'start': '09:00', 'end': '17:00'},
                'auto_sync_enabled': True
            })
        }
        
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO organizations (id, name, slug, subscription_status, settings)
                    VALUES (%(id)s, %(name)s, %(slug)s, %(subscription_status)s, %(settings)s)
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id
                """, sample_org)
                
                result = cursor.fetchone()
                db.connection.commit()
                
                if result:
                    logger.info(f"✅ Created sample organization: {sample_org['name']}")
                else:
                    logger.info(f"ℹ️  Sample organization already exists")
                
        except Exception as e:
            logger.error(f"Failed to create sample organization: {e}")
    
    def create_sample_user(self):
        """Create a sample user for testing"""
        sample_user = {
            'id': 'user_sample_123',
            'email': 'admin@sampleclinic.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin'
        }
        
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (id, email, first_name, last_name, role)
                    VALUES (%(id)s, %(email)s, %(first_name)s, %(last_name)s, %(role)s)
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id
                """, sample_user)
                
                result = cursor.fetchone()
                
                # Add user to sample organization
                if result:
                    cursor.execute("""
                        INSERT INTO organization_members (organization_id, user_id, role, status)
                        VALUES ('org_sample_123', %(id)s, 'owner', 'active')
                        ON CONFLICT (organization_id, user_id) DO NOTHING
                    """, sample_user)
                
                db.connection.commit()
                logger.info(f"✅ Created sample user: {sample_user['email']}")
                
        except Exception as e:
            logger.error(f"Failed to create sample user: {e}")
    
    def setup_directory_structure(self):
        """Create necessary directories"""
        directories = [
            'logs',
            'data/exports',
            'data/backups',
            'tmp'
        ]
        
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {dir_name}")
    
    def validate_setup(self) -> bool:
        """Validate that the setup was successful"""
        checks = [
            self._check_database_connection(),
            self._check_required_tables(),
            self._check_environment_variables()
        ]
        
        return all(checks)
    
    def _check_database_connection(self) -> bool:
        """Check database connection"""
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            if result:
                logger.info("✅ Database connection successful")
                return True
            else:
                logger.error("❌ Database connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            return False
    
    def _check_required_tables(self) -> bool:
        """Check that all required tables exist"""
        required_tables = [
            'organizations', 'users', 'organization_members',
            'contacts', 'active_patients', 'conversations', 'messages',
            'api_credentials', 'sync_logs', 'audit_logs'
        ]
        
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                
                existing_tables = {row[0] for row in cursor.fetchall()}
                
            missing_tables = set(required_tables) - existing_tables
            
            if missing_tables:
                logger.error(f"❌ Missing tables: {missing_tables}")
                return False
            else:
                logger.info("✅ All required tables exist")
                return True
                
        except Exception as e:
            logger.error(f"❌ Table check error: {e}")
            return False
    
    def _check_environment_variables(self) -> bool:
        """Check that required environment variables are set"""
        required_vars = [
            'SUPABASE_URL', 'SUPABASE_KEY', 'CLERK_SECRET_KEY',
            'CREDENTIALS_ENCRYPTION_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var) or os.getenv(var).startswith('your_'):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠️  Environment variables need configuration: {missing_vars}")
            return False
        else:
            logger.info("✅ All environment variables configured")
            return True
    
    def run_full_setup(self, force_env: bool = False):
        """Run complete setup process"""
        logger.info("🚀 Starting SurfRehab v2 Multi-Tenant Setup")
        
        # 1. Create environment file
        self.create_env_file(force=force_env)
        
        # 2. Setup directory structure
        self.setup_directory_structure()
        
        # 3. Setup database schema
        if not self.setup_database_schema():
            logger.error("❌ Database setup failed")
            return False
        
        # 4. Create sample data
        self.create_sample_organization()
        self.create_sample_user()
        
        # 5. Validate setup
        if self.validate_setup():
            logger.info("🎉 Multi-tenant setup completed successfully!")
            self._print_next_steps()
            return True
        else:
            logger.error("❌ Setup validation failed")
            return False
    
    def _print_next_steps(self):
        """Print next steps for user"""
        print("\n" + "="*60)
        print("🎉 SurfRehab v2 Multi-Tenant Setup Complete!")
        print("="*60)
        print("\n📋 NEXT STEPS:")
        print("\n1. 🔧 Configure your environment variables in .env:")
        print("   - Update Supabase URL and keys")
        print("   - Update Clerk.com credentials")
        print("   - Keep the generated encryption key secure")
        print("\n2. 🔗 Setup Clerk.com webhooks:")
        print("   - user.created")
        print("   - organization.created") 
        print("   - organizationMembership.created")
        print("\n3. 🚀 Start your application:")
        print("   python scripts/run_sync.py --organization org_sample_123")
        print("\n4. 🌐 Deploy to Railway:")
        print("   railway up")
        print("\n" + "="*60)

def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup SurfRehab v2 Multi-Tenant Platform')
    parser.add_argument('--force-env', action='store_true', help='Force recreation of .env file')
    
    args = parser.parse_args()
    
    setup = MultiTenantSetup()
    success = setup.run_full_setup(force_env=args.force_env)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 