"""
Script principal para rodar todo o pipeline v2 (Supabase):
1. Conecta no Postgres do projeto e calcula os KPIs via SQL (compute_kpis.py)
2. Gera o dashboard HTML atualizado em output/apresentacao.html (build_presentation.py)

Nao recarrega os dados brutos no banco - para isso, rode scripts/load_data.py.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    print("[1/2] Calculando KPIs via SQL no Supabase...")
    res1 = subprocess.run([sys.executable, str(ROOT / "scripts" / "compute_kpis.py")])
    if res1.returncode != 0:
        print("[ERRO] Falha ao calcular KPIs.")
        sys.exit(res1.returncode)

    print("[2/2] Gerando novo dashboard em output/apresentacao.html...")
    res2 = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_presentation.py")])
    if res2.returncode != 0:
        print("[ERRO] Falha ao gerar o dashboard.")
        sys.exit(res2.returncode)

    print("[SUCESSO] Pipeline concluido! Abra output/apresentacao.html para visualizar o dashboard atualizado.")


if __name__ == "__main__":
    main()
