import time
import psycopg2
import os

def main():
    # Cakaj na databazu
    while True:
        try:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            print("✅ Pripojenie na databázu úspešné!")
            conn.close()
            break
        except:
            print("⏳ Čakám na databázu...")
            time.sleep(2)
    
    print("Python beží!")
    # Dalsi skript
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()