import flet as ft
import logging

logger = logging.getLogger("supafit.notification")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_notification(page: ft.Page, title: str, text: str):
    """
    Envia uma notificação no app. Usa notificações nativas no Android e SnackBar em outras plataformas.

    Args:
        page (ft.Page): A página Flet atual.
        title (str): Título da notificação.
        text (str): Texto da notificação.
    """
    try:
        if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
            try:
                from jnius import autoclass, cast
                from flet_permission_handler import PermissionHandler

                Context = autoclass("android.content.Context")
                NotificationManager = autoclass("android.app.NotificationManager")
                NotificationChannel = autoclass("android.app.NotificationChannel")
                NotificationCompatBuilder = autoclass(
                    "androidx.core.app.NotificationCompat$Builder"
                )
                System = autoclass("java.lang.System")
                Vibrator = autoclass("android.os.Vibrator")
                Activity = autoclass("org.kivy.android.PythonActivity")

                # Verificar e solicitar permissão POST_NOTIFICATIONS
                permission_handler = PermissionHandler()
                permission_granted = permission_handler.check_permission(
                    "android.permission.POST_NOTIFICATIONS"
                )
                if not permission_granted:
                    permission_handler.request_permission(
                        "android.permission.POST_NOTIFICATIONS"
                    )
                    permission_granted = permission_handler.check_permission(
                        "android.permission.POST_NOTIFICATIONS"
                    )
                    if not permission_granted:
                        logger.warning(
                            "Permissão POST_NOTIFICATIONS não concedida, usando SnackBar"
                        )
                        raise Exception("Permissão POST_NOTIFICATIONS não concedida")

                # Obter contexto
                context = Activity.mActivity.getApplicationContext()

                # Criar canal de notificação (necessário para Android 8.0+)
                channel_id = "supafit_channel"
                channel_name = "SupaFit Notifications"
                channel = NotificationChannel(
                    channel_id, channel_name, NotificationManager.IMPORTANCE_DEFAULT
                )
                notification_manager = cast(
                    NotificationManager,
                    context.getSystemService(Context.NOTIFICATION_SERVICE),
                )
                notification_manager.createNotificationChannel(channel)

                # Criar notificação
                notification = NotificationCompatBuilder(context, channel_id)
                notification.setContentTitle(title)
                notification.setContentText(text)
                notification.setSmallIcon(context.getApplicationInfo().icon)
                notification.setAutoCancel(True)

                # Adicionar vibração
                vibrator = cast(
                    Vibrator, context.getSystemService(Context.VIBRATOR_SERVICE)
                )
                vibrator.vibrate(500)

                # Enviar notificação
                notification_id = int(System.currentTimeMillis() % 10000)
                notification_manager.notify(notification_id, notification.build())
                logger.info(f"Notificação nativa enviada no Android: {title} - {text}")
            except Exception as e:
                logger.error(f"Erro ao enviar notificação nativa no Android: {str(e)}")
                # Fallback para SnackBar
                snack_bar = ft.SnackBar(
                    content=ft.Text(
                        spans=[
                            ft.TextSpan(
                            text=f"{title:}",
                            style=ft.TextStyle(
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                                size=16,
                            ),
                        ),
                            ft.TextSpan(text=f"{text}",
                                        style=ft.TextStyle(
                                    color=ft.Colors.WHITE,
                                    size=14,
                                ),
                            )
                        ]
                        ),
                    action="OK",
                    bgcolor=ft.Colors.RED,
                    action_color=ft.Colors.WHITE,
                )
                page.overlay.append(snack_bar)
                snack_bar.open = True
                page.update()
        else:
            # SnackBar para plataformas não mobile (Windows, Linux, macOS, Web)
            snack_bar = ft.SnackBar(
                content=ft.Text(
                    spans=[
                        ft.TextSpan(
                            text=f"{title:}",
                            style=ft.TextStyle(
                                weight=ft.FontWeight.BOLD,
                                size=16,
                            ),
                        ),
                        ft.TextSpan(
                            text=f"{text}",
                            style=ft.TextStyle(
                                size=14,
                            ))
                    ]
                ),
            )
            page.overlay.append(snack_bar)
            snack_bar.open = True
            page.update()
            logger.info(f"Notificação SnackBar exibida: {title} - {text}")
    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {str(e)}")
        snack_bar = ft.SnackBar(
            content=ft.Text(f"Erro ao exibir notificação", color=ft.Colors.WHITE),
            action="OK",
            action_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED,
        )
        page.overlay.append(snack_bar)
        snack_bar.open = True
        page.update()
