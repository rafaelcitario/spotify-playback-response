import webbrowser
import requests
import time
from urllib.parse import urlparse, parse_qs

# ---------------------------------------------
# Configurações do Spotify
CLIENT_ID = input('Adicione o seu hash Cliente ID: ')  # Substitua pelo seu Client ID
CLIENT_SECRET = input('Adicione seu hash Client Secret: ')  # Substitua pelo seu Client Secret
REDIRECT_URI = 'http://localhost:8888/callback'  # Substitua pelo seu redirect URI registrado

# Escopo necessário para acessar o estado do player
SCOPE = 'user-read-playback-state'

# ---------------------------------------------
# Passo 1: Gerar a URL de autorização para o usuário
def get_authorization_url():
    response_type = 'code'  # Tipo de resposta (authorization code)
    authorization_url = f'https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type={response_type}&redirect_uri={REDIRECT_URI}&scope={SCOPE}'
    return authorization_url

# Passo 2: Trocar o código de autorização pelo token de acesso e refresh token
def get_tokens_from_code(auth_code):
    token_url = 'https://accounts.spotify.com/api/token'
    
    # Dados da requisição para trocar o código de autorização por tokens
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI
    }

    # Cabeçalhos com as credenciais do client
    auth = (CLIENT_ID, CLIENT_SECRET)
    
    # Requisição POST para obter o token de acesso e refresh token
    response = requests.post(token_url, data=data, auth=auth)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        return access_token, refresh_token
    else:
        return f"Erro ao obter tokens: {response.json()}"

# Passo 3: Usar o token para fazer a requisição e obter o que está tocando
def request_current_playback(token):
    playback_url = 'https://api.spotify.com/v1/me/player/currently-playing'
    
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Requisição GET para obter o que está tocando no player
    response = requests.get(playback_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return f"Erro ao obter playback: {response.json()}"

# Passo 4: Usar o refresh token para obter um novo access token quando o anterior expirar
def refresh_access_token(refresh_token):
    token_url = 'https://accounts.spotify.com/api/token'
    
    # Dados da requisição para obter um novo access token
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    # Cabeçalhos com as credenciais do client
    auth = (CLIENT_ID, CLIENT_SECRET)
    
    # Requisição POST para obter um novo access token
    response = requests.post(token_url, data=data, auth=auth)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        return access_token
    else:
        return f"Erro ao obter novo access token: {response.json()}"

# ---------------------------------------------
# Função para extrair o código da URL
def extract_code_from_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    # Extraímos o valor do parâmetro 'code'
    code = query_params.get('code', [None])[0]
    
    if code:
        return code
    else:
        raise ValueError("Não foi encontrado o parâmetro 'code' na URL")

# ---------------------------------------------
# Fluxo principal
def main():
    # Passo 1: Gerar a URL de autorização e abrir no navegador
    auth_url = get_authorization_url()
    print("Por favor, abra o link abaixo no seu navegador para autorizar o aplicativo:")
    print(auth_url)
    webbrowser.open(auth_url)
    
    # Passo 2: O usuário deve colar a URL completa aqui
    url = input("Por favor, cole a URL completa aqui (após autorizar no navegador): ")
    
    try:
        # Passo 3: Extrair o código da URL
        auth_code = extract_code_from_url(url)
        print(f"Código de autorização extraído: {auth_code}")

        # Passo 4: Obter os tokens (access token e refresh token)
        access_token, refresh_token = get_tokens_from_code(auth_code)

        if access_token.startswith('Erro'):
            print(access_token)
            return

        # Passo 5: Ficar verificando a música atual a cada 10 segundos
        while True:
            # Usar o token de acesso para obter a música que está tocando
            playback_data = request_current_playback(access_token)

            if isinstance(playback_data, dict):
                # Extrair nome da música e do artista
                track_name = playback_data.get('item', {}).get('name', 'Desconhecido')
                artist_name = playback_data.get('item', {}).get('artists', [{}])[0].get('name', 'Desconhecido')

                # Exibir os dados
                print(f"Artista: {artist_name} - Música: {track_name}")
            else:
                print(playback_data)
            
            # Esperar 10 segundos antes de fazer a próxima requisição
            time.sleep(30)

            # Se o access token estiver expirado, usar o refresh token para obter um novo access token
            if access_token.startswith('Erro'):
                print("O access token expirou. Tentando obter um novo...")
                access_token = refresh_access_token(refresh_token)
                if access_token.startswith('Erro'):
                    print(access_token)
                    break

    except ValueError as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
