# SupaFit 🏋️‍♂️

Bem-vindo ao **SupaFit**, um aplicativo de treino fitness desenvolvido com **Flet** e integrado com **Supabase**! Este app ajuda você a gerenciar treinos, compartilhar conquistas na comunidade, conversar com um treinador virtual (via Openai), e receber notificações para manter a motivação. Tudo isso com uma interface fluida e suporte a notificações nativas no Android!

## ✨ Funcionalidades

- **Gerenciamento de Treinos**: Acesse treinos diários com exercícios detalhados, animações (via ExerciseDB API), e controle de tempo.
- **Comunidade**: Compartilhe suas vitórias (ex.: "Levantei 100kg no supino!") e curta conquistas de outros usuários.
- **Treinador Virtual**: Faça perguntas ao treinador (integrado com Openai) e receba respostas personalizadas.
- **Notificações**:
  - Receba notificações nativas no Android ao finalizar um treino, postar uma vitória, ou obter uma resposta do treinador.
  - SnackBars em outras plataformas (Windows, macOS, web).
- **Integração com Supabase**: Armazene treinos, vitórias, e interações com o treinador de forma segura.
- **Responsivo**: Funciona em Android, desktop, e web (com notificações adaptadas por plataforma).

## 🛠️ Tecnologias

- **Flet 0.27.6**: Framework para a interface multiplataforma.
- **Supabase 2.15.0**: Backend para autenticação, banco de dados, e armazenamento.
- **Pyjnius 1.6.1**: Notificações nativas no Android.
- **Flet-Permission-Handler 0.1.0**: Gerenciamento de permissões no Android.
- **Requests 2.32.3**: Integração com a ExerciseDB API.
- **Httpx 0.28.1**: Chamadas à API Openai.
- **Python-Dotenv 1.1.0**: Gerenciamento de variáveis de ambiente.

## 📋 Pré-requisitos

- **Python 3.9+**
- **Android SDK** e **JDK** (para build do APK, recomendamos o Android Studio)
- Um dispositivo Android (8.0+) ou emulador para testar notificações nativas
- Conta no **Supabase** (para backend)
- Chave da **ExerciseDB API** (para animações de exercícios)
- Chave da **Openai API** (para o treinador virtual)

## 🚀 Instalação

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/Alisonsantos77/supafit.git
   cd supafit