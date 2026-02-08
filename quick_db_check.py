#!/usr/bin/env python3
"""Quick database check using available libraries."""
import os
import sys

# Try to use existing venv from a service
venv_paths = [
    "backend/services/sentiment-analysis/venv",
    "backend/services/market_service/venv",
    "backend/services/stock_service/venv",
]

for venv in venv_paths:
    venv_python = os.path.join(venv, "bin", "python3")
    if os.path.exists(venv_python):
        print(f"✅ Found Python in: {venv}")
        print(f"   Using: {venv_python}\n")
        
        # Re-run this script with that Python
        import subprocess
        result = subprocess.run([venv_python, __file__ + ".actual"], capture_output=False)
        sys.exit(result.returncode)

# If we're here, no venv found or we're in the venv already
print("⚠️  No virtual environment found")
print("Let me check with psql directly...\n")

# Use psql command instead
env_file = "backend/services/api_gateway/.env"
try:
    with open(env_file) as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.split("=", 1)[1].strip()
                print(f"🔌 Database URL found")
                print(f"   {db_url.split('@')[1] if '@' in db_url else 'unknown'}\n")
                
                # Try psql command
                import subprocess
                
                commands = [
                    ("Tables", "\\dt"),
                    ("Stocks count", "SELECT COUNT(*) FROM stocks;"),
                    ("Historical prices count", "SELECT COUNT(*) FROM historical_prices;"),
                    ("Sample stocks", "SELECT ticker, name, code FROM stocks LIMIT 5;"),
                    ("Latest prices", "SELECT date, COUNT(*) FROM historical_prices GROUP BY date ORDER BY date DESC LIMIT 5;"),
                ]
                
                for title, cmd in commands:
                    print(f"📊 {title}:")
                    try:
                        result = subprocess.run(
                            ["psql", db_url, "-c", cmd],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            print(result.stdout)
                        else:
                            print(f"   ⚠️  Error: {result.stderr[:200]}")
                    except FileNotFoundError:
                        print("   ⚠️  psql command not found")
                        break
                    except Exception as e:
                        print(f"   ⚠️  Error: {str(e)[:100]}")
                    print()
                break
except FileNotFoundError:
    print(f"❌ .env file not found: {env_file}")
except Exception as e:
    print(f"❌ Error: {e}")
