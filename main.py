import requests 

composto = input("Digite o nome do composto senolítico (ex: quercetin, dasatinib, resveratrol): ")

url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{composto}/property/MolecularFormula,MolecularWeight,Title/JSON"

response = requests.get(url)

data = response.json()

nome = data['PropertyTable']['Properties'][0]['Title']
formula = data ['PropertyTable']['Properties'][0]['MolecularFormula']
peso = data['PropertyTable']['Properties'][0]['MolecularWeight']

print("\n--- RESULTADO DA BUSCA CIENTÍFICA ---")
print(f"Nome do Composto: {nome}")
print(f"Fórmula Química: {formula}")
print(f"Peso Molecular: {peso} g/mol")
print("-------------------------------------")