import flet as ft
from services.supabase import SupabaseService
import logging

logger = logging.getLogger("supafit.terms")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def TermsPage(page: ft.Page, supabase, openai):
    terms_markdown = """
# Termos de Uso do SupaFit

Bem-vindo ao **SupaFit**! Antes de iniciar sua jornada fitness, leia atentamente estes Termos de Uso. Ao utilizar o SupaFit, você concorda com todas as condições aqui descritas. Caso não concorde, não poderá usar a aplicação.

## 1. O que é o SupaFit?

O SupaFit é uma plataforma fitness inovadora que utiliza inteligência artificial para criar treinos personalizados, rastrear seu progresso e oferecer uma experiência interativa. Desenvolvida por **Alison Santos**, a aplicação integra **Flet**, **Supabase**, **Groq** e **OpenAI** para proporcionar planos de treino adaptados ao seu perfil (idade, peso, altura, objetivo e restrições físicas) e um dashboard para acompanhar sua evolução.

## 2. Uso Responsável

- Utilize o SupaFit apenas para fins legítimos, como criar, seguir e acompanhar planos de treino personalizados.
- É proibido usar a aplicação para spam, assédio, compartilhamento de conteúdo sensível (ex.: linguagem ofensiva ou dados pessoais não autorizados) ou qualquer atividade ilegal. Violações podem resultar na suspensão ou encerramento imediato da conta.
- Respeite as leis brasileiras, incluindo a [LGPD (Lei Geral de Proteção de Dados)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm).

## 3. Funcionalidades e Limites

- **Geração de Treinos**: Crie planos personalizados com base em seus objetivos (ex.: hipertrofia, perda de peso, resistência) e perfil.
- **Rastreamento de Progresso**: Registre e acompanhe o progresso de exercícios, incluindo cargas e histórico de treinos.
- **Moderação por IA**: Perguntas e restrições são verificadas pela OpenAI para garantir conteúdo seguro e apropriado.
- **Limites de Uso**: O uso está sujeito a quotas de APIs de terceiros (ex.: Groq, OpenAI). Exceder limites pode temporariamente restringir funcionalidades, conforme políticas dos provedores.

## 4. Cadastro e Autenticação

- Para usar o SupaFit, você deve criar uma conta com email e senha, gerenciada pelo Supabase.
- Mantenha suas credenciais seguras. Você é responsável por atividades realizadas em sua conta.
- A restauração de sessões é automática via `client_storage`, mas sessões expiradas exigem novo login.

## 5. Responsabilidade

- O SupaFit se esforça para oferecer um serviço estável, mas não se responsabiliza por falhas de terceiros (ex.: Supabase para dados, Groq/OpenAI para IA).
- Você é responsável por fornecer informações precisas (ex.: restrições físicas) e por seguir os treinos de forma segura. Consulte um profissional de saúde antes de iniciar qualquer programa fitness.
- Não garantimos resultados específicos de treino, pois dependem de fatores individuais (ex.: adesão, alimentação).

## 6. Suspensão do Serviço

- Podemos suspender o SupaFit para manutenção ou atualizações sem aviso prévio, buscando minimizar transtornos.
- Violações destes Termos podem resultar em suspensão ou encerramento da conta sem notificação.

## 7. Suporte

- Problemas? Contate-nos por email ([Alisondev77@hotmail.com](mailto:Alisondev77@hotmail.com)) ou [WhatsApp](https://wa.link/oebrg2).
- O suporte é técnico e não cobre mau uso, questões de saúde ou problemas fora do nosso controle.

## 8. Mudanças nos Termos

- Podemos atualizar os Termos periodicamente. Você será notificado na aplicação ou por email. Continuar usando o SupaFit após mudanças implica aceitação dos novos termos.

## 9. Lei Aplicável

- Estes Termos são regidos pelas leis do Brasil. Disputas serão resolvidas nos tribunais de Bastos/SP.

**Dúvidas?** Vamos treinar juntos! 💪
    """

    privacy_markdown = """
# Política de Privacidade do SupaFit

No SupaFit, sua privacidade é nossa prioridade! Esta Política explica como coletamos, usamos e protegemos seus dados, em conformidade com a [LGPD (Lei nº 13.709/2018)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm).

## 1. Que dados coletamos?

- **Dados fornecidos por você**: Nome, email, idade, peso, altura, objetivo fitness, nível de condicionamento e restrições físicas (no cadastro e perfil).
- **Dados automáticos**: Uso da aplicação (treinos criados, exercícios registrados, progresso, logs de acesso para segurança) e preferências salvas via `client_storage` (ex.: treinos temporários).
- **O que não coletamos**: Dados financeiros ou informações sensíveis não relacionadas ao fitness.

## 2. Para que usamos esses dados?

- Criar e gerenciar treinos personalizados com base no seu perfil.
- Rastrear progresso de exercícios e exibir estatísticas no dashboard.
- Melhorar a experiência por meio de análises de uso.
- Moderar conteúdo (ex.: perguntas, restrições) via OpenAI para garantir segurança.
- Cumprir obrigações legais, conforme a LGPD.

## 3. Como armazenamos e protegemos seus dados?

- Dados são armazenados no **Supabase**, com criptografia para informações sensíveis (ex.: `flet.security.encrypt`).
- Apenas a equipe do SupaFit e serviços essenciais (Supabase, Groq, OpenAI) acessam os dados, exclusivamente para operar a aplicação.
- Logs de acesso são mantidos para segurança e debugging, conforme necessário.

## 4. Com quem compartilhamos seus dados?

- **Serviços de terceiros**: Supabase (armazenamento), Groq/OpenAI (geração de treinos e moderação de conteúdo). Eles recebem apenas o necessário.
- **Sem vendas**: Não compartilhamos dados para marketing sem sua autorização.
- **Autoridades**: Dados podem ser compartilhados em caso de ordem judicial, conforme exigido por lei.

## 5. Seus direitos (LGPD)

- Solicite acesso, correção ou exclusão de seus dados por email ([Alisondev77@hotmail.com](mailto:Alisondev77@hotmail.com)).
- Você pode interromper o uso de seus dados, mas isso pode limitar o funcionamento da aplicação.
- Respondemos em até 15 dias, conforme a LGPD.

## 6. Por quanto tempo guardamos seus dados?

- Dados são mantidos enquanto sua conta estiver ativa. Após encerramento, excluímos tudo em até 30 dias, exceto logs exigidos por lei (mantidos por 1 ano).
- Dados de treinos e progresso são criptografados e armazenados apenas enquanto necessários.

## 7. Cookies e tecnologias similares

- Usamos `client_storage` do Flet para salvar preferências (ex.: tema, treinos temporários), sem cookies de terceiros para rastreamento.

## 8. Mudanças na Política

- Atualizações na Política serão notificadas na aplicação ou por email. Continuar usando o SupaFit implica aceitação.

## 9. Contato

- Dúvidas? Envie um email para [Alisondev77@hotmail.com](mailto:Alisondev77@hotmail.com) ou contate-nos no [WhatsApp](https://wa.link/oebrg2).

**Treine com segurança e confiança!** 💪
    """

    terms_content = ft.Column(
        [
            ft.ResponsiveRow(
                [
                    ft.Container(
                        ft.Container(
                            content=ft.Image(
                                src="icon.png",
                                fit=ft.ImageFit.CONTAIN,
                            )
                        ),
                        padding=5,
                        col=10,
                    ),
                    ft.Container(
                        ft.Markdown(
                            terms_markdown,
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            on_tap_link=lambda e: page.launch_url(e.data),
                        ),
                        padding=5,
                        col=10,
                    ),
                    ft.Divider(),
                    ft.Container(
                        ft.Markdown(
                            privacy_markdown,
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            on_tap_link=lambda e: page.launch_url(e.data),
                        ),
                        padding=5,
                        col=10,
                    ),
                ],
            ),
        ],
        spacing=20,
        scroll=ft.ScrollMode.AUTO,
        alignment=ft.MainAxisAlignment.CENTER,
    )

    return ft.Container(content=terms_content, padding=20)
