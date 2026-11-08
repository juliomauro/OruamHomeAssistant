# template_bloco.py v1.0 - insere ou substitui um bloco nomeado dentro de "template:" no configuration.yaml
# O bloco fica entre "  # BLOCO <nome>" e "  # FIM <nome>".
# uso (no atlas): python3 template_bloco.py <config_entrada> <nome> <arquivo_bloco> > <config_saida>
import sys
cfg, nome, arq = sys.argv[1:4]
txt = open(cfg).read()
corpo = open(arq).read().rstrip("\n") + "\n"
ini, fim = f"  # BLOCO {nome}\n", f"  # FIM {nome}\n"
bloco = ini + corpo + fim
if ini in txt:
    a = txt.index(ini); b = txt.index(fim, a) + len(fim)
    txt = txt[:a] + bloco + txt[b:]
else:
    assert txt.count("\ntemplate:\n") == 1
    txt = txt.replace("\ntemplate:\n", "\ntemplate:\n" + bloco, 1)
sys.stdout.write(txt)
