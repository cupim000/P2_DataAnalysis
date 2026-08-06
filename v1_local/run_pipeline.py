"""
Script principal para rodar todo o pipeline de analise de dados:
1. Le os CSVs atualizados em data/ e calcula os KPIs (compute_kpis.py)
2. Gera a apresentacao HTML atualizada em output/apresentacao.html (build_presentation.py)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    print("[1/2] Atualizando KPIs a partir dos dados em data/...")
    res1 = subprocess.run([sys.executable, str(ROOT / "scripts" / "compute_kpis.py")])
    if res1.returncode != 0:
        print("[ERRO] Falha ao calcular KPIs.")
        sys.exit(res1.returncode)

    print("[2/2] Gerando nova apresentacao em output/apresentacao.html...")
    res2 = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_presentation.py")])
    if res2.returncode != 0:
        print("[ERRO] Falha ao gerar apresentacao.")
        sys.exit(res2.returncode)

    print("[SUCESSO] Pipeline concluido! Abra output/apresentacao.html para visualizar a apresentacao atualizada.")

if __name__ == "__main__":
    main()
