import requests

def buscar_dados_moleculares():
    print("🔬 SENOTRACK - MÓDULO DE TRIAGEM MOLECULAR PRIMÁRIA")
    print("==================================================")
    
    composto = input("Digite o nome do composto (em inglês, ex: quercetin, dasatinib): ").strip().lower()
    
    if not composto:
        print("⚠️ Erro: O nome do composto não pode ser vazio.")
        return

    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{composto}/property/MolecularFormula,MolecularWeight,Title/JSON"

    try:
        # Definimos um timeout para o script não travar infinitamente se a API cair
        response = requests.get(url, timeout=10)
        
        # Levanta um erro automático se o status code for 4XX ou 5XX (ex: 404 Not Found)
        response.raise_for_status()
        
        data = response.json()
        
        # Validação defensiva da estrutura do JSON retornado
        properties = data.get('PropertyTable', {}).get('Properties', [])[0]
        
        nome = properties.get('Title', composto.capitalize())
        formula = properties.get('MolecularFormula', 'Não localizada')
        peso = properties.get('MolecularWeight', 'Não localizado')

        print("\n--- 📊 RESULTADO DA BUSCA CIENTÍFICA ---")
        print(f"Nome Oficial:    {nome}")
        print(f"Fórmula Química: {formula}")
        print(f"Peso Molecular:  {peso} g/mol")
        print("-------------------------------------")

    except requests.exceptions.HTTPError:
        print(f"\n❌ Erro: Composto '{composto}' não encontrado na base internacional do PubChem.")
        print("Verifique a grafia em inglês e tente novamente.")
        
    except requests.exceptions.Timeout:
        print("\n⏳ Erro: A requisição excedeu o tempo limite. Verifique sua conexão ou tente mais tarde.")
        
    except requests.exceptions.RequestException as e:
        print(f"\n⚠️ Erro de rede inesperado: {e}")
        
    except (KeyError, IndexError):
        print("\n🧩 Erro: A API retornou dados em um formato inesperado.")

if __name__ == "__main__":
    buscar_dados_moleculares()