import flet as ft

from services.services import SupabaseService
import logging

logger = logging.getLogger("supafit.terms")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def TermsPage(page: ft.Page, supabase, anthropic):
    # Conteúdo dos Termos de Uso em Markdown
    terms_markdown = """
# Termos de Uso do DebtManager

Bem-vindo ao DebtManager! Antes de usar nossa ferramenta, por favor, leia atentamente estes Termos de Uso. Ao utilizar o DebtManager, você concorda com todas as condições aqui descritas. Caso não concorde, não poderá usar a aplicação.

## 1. O que é o DebtManager?

O DebtManager é uma ferramenta que ajuda você a gerenciar dívidas e enviar notificações automáticas via WhatsApp. Extraímos dados de PDFs, enviamos mensagens para seus clientes e fornecemos um dashboard para acompanhar tudo de forma fácil, rápida e direta.

## 2. Uso Responsável

- Use o DebtManager apenas para fins legais e legítimos, como enviar notificações de dívidas válidas.
- É proibido usar a aplicação para spam, assédio ou qualquer uso indevido (ex.: enviar mensagens para contatos não autorizados). Caso isso ocorra, sua conta poderá ser suspensa ou encerrada imediatamente.
- Respeite as leis brasileiras, incluindo a [LGPD (Lei Geral de Proteção de Dados)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm).

## 3. Limites de Uso

Cada plano possui limites mensais de mensagens e PDFs:

- **Básico:** 100 mensagens, 5 PDFs.
- **Pro:** 200 mensagens, 15 PDFs.
- **Enterprise:** 500 mensagens, 30 PDFs.

Se você exceder o limite, sua conta poderá ser bloqueada até que um upgrade de plano seja realizado. Tentar burlar os limites (ex.: criar múltiplas contas) pode resultar em suspensão permanente.

## 4. Pagamento e Upgrades

- Nossos planos são pagos, com os seguintes valores:  
  - **Básico:** R$150/mês.  
  - **Pro:** R$250/mês.  
  - **Enterprise:** R$400/mês.
- Upgrades de plano requerem validação manual por meio de um código enviado ao suporte.
- Não há reembolso após a ativação do plano, então escolha com cuidado!
- A renovação é manual e pode ser solicitada a qualquer momento na página de perfil.

## 5. Responsabilidade

- Fazemos o possível para manter o DebtManager funcionando perfeitamente, mas não nos responsabilizamos por falhas de serviços de terceiros (ex.: Twilio para mensagens, Supabase para dados, Anthropic para extração de PDFs).
- Se você usar a aplicação de forma incorreta (ex.: enviar dados errados nos PDFs), a responsabilidade é sua.
- O DebtManager não garante que todas as notificações serão entregues (devido a falhas de rede ou bloqueios), mas notificaremos você em caso de problemas.

## 6. Suspensão do Serviço

- Podemos suspender o DebtManager para manutenção ou atualizações sem aviso prévio. Faremos o possível para ser breve!
- Em caso de violação destes Termos, sua conta poderá ser suspensa ou encerrada sem aviso.

## 7. Suporte

- Enfrentando problemas? Entre em contato por email ([Alisondev77@hotmail.com](mailto:Alisondev77@hotmail.com)) ou [WhatsApp](https://wa.link/oebrg2).
- Nosso suporte é técnico e não cobre mau uso da aplicação ou problemas fora do nosso controle.

## 8. Mudanças nos Termos

- Podemos atualizar estes Termos periodicamente. Você será notificado na aplicação ou por email. Continuar usando o DebtManager após as mudanças significa que você aceita os novos termos.

## 9. Lei Aplicável

- Estes Termos são regidos pelas leis do Brasil. Qualquer disputa será resolvida nos tribunais de Bastos/SP.

**Dúvidas?** Fale com a gente!
    """

    # Conteúdo da Política de Privacidade em Markdown
    privacy_markdown = """
# Política de Privacidade do DebtManager

No DebtManager, levamos sua privacidade a sério! Como lidamos com dados sensíveis, esta Política explica como coletamos, usamos e protegemos suas informações, em conformidade com a [LGPD (Lei Geral de Proteção de Dados – Lei nº 13.709/2018)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm). Leia com atenção para entender tudo!

## 1. Que dados coletamos?

- **Dados fornecidos por você:** Nome de usuário, email, plano escolhido (no cadastro) e dados dos PDFs enviados (nome dos clientes, contatos, valores de dívidas, datas de vencimento).
- **Dados automáticos:** Uso da aplicação (quantidade de mensagens enviadas, PDFs processados) e logs de acesso (para segurança).
- **O que não coletamos:** Dados financeiros diretos (como número de cartão), apenas os valores de dívidas informados nos PDFs.

## 2. Para que usamos esses dados?

- Para fazer a aplicação funcionar: extrair dados de PDFs, enviar notificações via WhatsApp e exibir seu uso no dashboard.
- Para melhorar o DebtManager: analisar o uso da aplicação e aprimorar a experiência.
- Para suporte: ajudar você em caso de problemas.
- Para cumprir a lei: responder a autoridades, se necessário, conforme a LGPD.

## 3. Como armazenamos e protegemos seus dados?

- Seus dados são armazenados no Supabase, um serviço de banco de dados seguro.
- Utilizamos criptografia para proteger informações sensíveis (como no nosso código, com `flet.security.encrypt`).
- Apenas nossa equipe e os serviços necessários (como Twilio e Anthropic) têm acesso aos dados, e somente para o funcionamento da aplicação.

## 4. Com quem compartilhamos seus dados?

- **Serviços de terceiros:** Usamos Twilio para enviar mensagens, Supabase para armazenar dados e Anthropic para extrair dados de PDFs. Eles recebem apenas o necessário para operar.
- **Sem vendas:** Não vendemos nem compartilhamos seus dados com terceiros para fins de marketing, a menos que você autorize.
- **Autoridades:** Em caso de ordem judicial, podemos compartilhar dados, mas apenas o exigido por lei.

## 5. Seus direitos (de acordo com a LGPD)

- Você pode solicitar acesso, correção ou exclusão de seus dados a qualquer momento. Envie um email para [Alisondev77@hotmail.com](mailto:Alisondev77@hotmail.com).
- Você também pode pedir para interrompermos o uso de seus dados (mas isso pode impedir o funcionamento da aplicação para você).
- Respondemos às suas solicitações em até 15 dias, conforme a LGPD.

## 6. Por quanto tempo guardamos seus dados?

- Mantemos seus dados enquanto sua conta estiver ativa. Se você encerrar a conta, excluímos tudo em até 30 dias, exceto o que a lei exige manter (ex.: logs de uso por 1 ano).
- Dados dos PDFs (como contatos de clientes) são criptografados e mantidos apenas enquanto necessários na aplicação.

## 7. Cookies e tecnologias similares

- Usamos o `client_storage` do Flet para salvar preferências (ex.: tema, avatar, uso de mensagens). Isso não é um cookie, mas funciona de forma semelhante, apenas para melhorar a experiência na aplicação.
- Não usamos cookies de terceiros para rastreamento ou anúncios.

## 8. Mudanças na Política

- Podemos atualizar esta Política periodicamente. Você será notificado na aplicação ou por email. Continuar usando o DebtManager após as mudanças significa que você aceita a nova política.

## 9. Contato

- Dúvidas sobre sua privacidade? Envie um email para [Alisondev77@hotmail.com](mailto:Alisondev77@hotmail.com) ou fale conosco no [WhatsApp](https://wa.link/oebrg2).

Estamos aqui para ajudar você a organizar suas finanças com segurança!
    """
    # Monta o conteúdo da página com Markdown
    terms_content = ft.Column(
        [
            ft.ResponsiveRow(
                [
                    ft.Container(
                        ft.Container(
                            content=ft.Image(
                                src="icon.png",
                                width=200,
                                height=200,
                                fit=ft.ImageFit.CONTAIN,
                            )
                        ),
                        padding=5,
                        bgcolor=ft.Colors.YELLOW,
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
                        bgcolor=ft.Colors.GREEN,
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
                        bgcolor=ft.Colors.BLUE,
                        col=10,
                    ),
                ],
            ),
        ],
        spacing=20,
        scroll=ft.ScrollMode.AUTO,
    )

    return ft.Container(content=terms_content, padding=20)
