import json
import os
import asyncio
import logging
import flet as ft
import flet_video
from flet_video import Video, VideoMedia
from dotenv import load_dotenv
from supabase import create_client, Client
from components.exercise_tile import ExerciseTile
from components.components import TimerDialog

load_dotenv()
logger = logging.getLogger("supafit.treino")

efr_url = os.getenv("SUPABASE_URL")
efr_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

db: Client = create_client(efr_url, efr_key)


def get_video_url(storage_bucket, file_name: str) -> str:
    """Retorna URL pública para arquivo no bucket."""
    try:
        url = storage_bucket.get_public_url(file_name)
        logger.debug(f"Gerada URL pública para {file_name}: {url}")
        return url
    except Exception as e:
        logger.error(f"Erro ao gerar URL pública para {file_name}: {str(e)}")
        return None


def Treinopage(page: ft.Page, supabase: any, day: str):
    """Renderiza a página de treino para o dia informado."""
    storage_bucket = db.storage.from_("supafit-videos")
    try:
        bucket_files = {f["name"] for f in storage_bucket.list(path="")}
        logger.info(
            f"Arquivos no bucket supafit-videos: {len(bucket_files)} encontrados"
        )
    except Exception as e:
        logger.error(f"Erro ao listar bucket supafit-videos: {e}")
        bucket_files = set()

    def video_for(name: str) -> str:
        """Carrega URL do vídeo a partir da tabela video_urls no Supabase."""
        try:
            cache_key = f"video_url_{name}"
            cached_url = page.client_storage.get(cache_key)
            if cached_url:
                logger.debug(
                    f"URL do vídeo encontrada no cache para {name}: {cached_url}"
                )
                return cached_url
            response = (
                supabase.client.table("video_urls")
                .select("url")
                .eq("name", name)
                .execute()
            )
            if response.data:
                url = response.data[0]["url"]
                page.client_storage.set(cache_key, url)
                logger.debug(f"URL do vídeo encontrada para {name}: {url}")
                return url
            logger.warning(f"Nenhuma URL de vídeo encontrada para {name}")
            return None
        except Exception as e:
            logger.error(f"Erro ao consultar URL do vídeo para {name}: {str(e)}")
            return None

    async def download_videos(e, exercises):
        """Baixa vídeos do treino para armazenamento local."""
        try:
            import httpx

            for ex in exercises:
                url = ex["video_url"]
                if not url:
                    logger.warning(f"Sem URL para baixar vídeo de {ex['name']}")
                    continue
                local_path = f"videos/{ex['name']}.mp4"
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        with open(local_path, "wb") as f:
                            f.write(response.content)
                        page.client_storage.set(
                            f"video_path_{ex['name']}", f"file://{local_path}"
                        )
                        logger.info(f"Vídeo baixado para {ex['name']}: {local_path}")
                    else:
                        logger.error(
                            f"Falha ao baixar vídeo de {ex['name']}: {response.status_code}"
                        )
            page.open(ft.SnackBar(
                content=ft.Text("Vídeos baixados com sucesso!", ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
            ))
            page.update()
        except Exception as e:
            logger.error(f"Erro ao baixar vídeos: {str(e)}")
            page.open(ft.SnackBar(
                content=ft.Text(f"Erro ao baixar vídeos: {str(e)}", ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
            ))
            page.update()

    def clear_downloaded_videos(e):
        """Remove vídeos baixados e limpa cache de caminhos locais."""
        try:
            import shutil

            videos_dir = "videos"
            if os.path.exists(videos_dir):
                shutil.rmtree(videos_dir)
                logger.info("Diretório de vídeos removido")
            for key in page.client_storage.get_keys():
                if key.startswith("video_path_"):
                    page.client_storage.remove(key)
                    logger.debug(f"Chave de vídeo removida: {key}")
            page.open(ft.SnackBar(
                content=ft.Text("Vídeos baixados limpos com sucesso!", ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
            ))
            page.update()
        except Exception as e:
            logger.error(f"Erro ao limpar vídeos baixados: {str(e)}")
            page.open(ft.SnackBar(
                content=ft.Text(f"Erro ao limpar vídeos: {str(e)}", ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
            ))
            page.update()

    def load_exercises(day: str):
        """Carrega exercícios do Supabase para o dia especificado."""
        cache_key = f"exercises_{day}"
        try:
            cached = page.client_storage.get(cache_key)
            if cached:
                logger.info(f"Carregando exercícios de {day} do cache")
                return cached
        except Exception as e:
            logger.warning(f"Erro ao verificar cache para {day}: {str(e)}")

        try:
            response = supabase.client.table("video_urls").select("name").execute()
            exercise_names = (
                [item["name"] for item in response.data] if response.data else []
            )
            logger.info(f"Carregados {len(exercise_names)} exercícios do Supabase")
        except Exception as e:
            logger.error(f"Erro ao carregar exercícios do Supabase: {str(e)}")
            exercise_names = []

        day_exercises = {
            "segunda": [
                {"name": "Supino Reto", "sets": 4, "reps": 12, "load": 0},
                {
                    "name": "Supino Inclinado Com Halteres",
                    "sets": 4,
                    "reps": 10,
                    "load": 0,
                },
                {"name": "Cross Over", "sets": 4, "reps": 12, "load": 0},
                {"name": "Peck Deck Aberto", "sets": 4, "reps": 12, "load": 0},
            ],
            "terça": [
                {"name": "Puxador Frente", "sets": 4, "reps": 12, "load": 0},
                {"name": "Remada Baixa", "sets": 4, "reps": 10, "load": 0},
                {
                    "name": "Rosca Direta Com Barra Reta",
                    "sets": 4,
                    "reps": 12,
                    "load": 0,
                },
                {
                    "name": "Rosca Martelo Com Halteres",
                    "sets": 4,
                    "reps": 10,
                    "load": 0,
                },
            ],
            "quarta": [
                {"name": "Agachamento Livre", "sets": 4, "reps": 10, "load": 0},
                {"name": "Cadeira Extensora", "sets": 4, "reps": 12, "load": 0},
                {"name": "Cadeira Flexora", "sets": 4, "reps": 12, "load": 0},
                {"name": "Panturrilha Sentado", "sets": 4, "reps": 15, "load": 0},
            ],
            "quinta": [
                {
                    "name": "Desenvolvimento com Halteres Sentado",
                    "sets": 4,
                    "reps": 10,
                    "load": 0,
                },
                {"name": "Arnold Press", "sets": 4, "reps": 12, "load": 0},
                {"name": "Remada Alta Com Halteres", "sets": 4, "reps": 12, "load": 0},
                {
                    "name": "Encolhimento de Ombros na Paralela no Graviton",
                    "sets": 4,
                    "reps": 12,
                    "load": 0,
                },
            ],
            "sexta": [
                {"name": "Supino Declinado", "sets": 4, "reps": 12, "load": 0},
                {"name": "Supino Reto com Halteres", "sets": 4, "reps": 10, "load": 0},
                {"name": "Cross Over Crucifixo", "sets": 4, "reps": 12, "load": 0},
                {"name": "Peck Deck Aberto", "sets": 4, "reps": 12, "load": 0},
            ],
            "sábado": [
                {"name": "Supra Abdominal", "sets": 4, "reps": 15, "load": 0},
                {"name": "Abdominal Infra no Solo", "sets": 4, "reps": 15, "load": 0},
                {"name": "Prancha Isometria", "sets": 4, "reps": 30, "load": 0},
                {
                    "name": "Prancha Isometria de Joelhos",
                    "sets": 4,
                    "reps": 30,
                    "load": 0,
                },
            ],
            "domingo": [
                {
                    "name": "Alongamento de Adutores Sentado",
                    "sets": 3,
                    "reps": 30,
                    "load": 0,
                },
                {
                    "name": "Alongamento de Posterior de Coxa no Espaldar",
                    "sets": 3,
                    "reps": 30,
                    "load": 0,
                },
                {
                    "name": "Alongamento de Panturrilha",
                    "sets": 3,
                    "reps": 30,
                    "load": 0,
                },
                {
                    "name": "Alongamento de Peitorais e Dorsais no Solo",
                    "sets": 3,
                    "reps": 30,
                    "load": 0,
                },
            ],
        }

        exercises = day_exercises.get(day.lower(), [])
        valid_exercises = []
        for ex in exercises:
            if ex["name"] in exercise_names:
                video_url = video_for(ex["name"])
                valid_exercises.append(
                    {
                        "name": ex["name"],
                        "series": ex["sets"],
                        "repetitions": ex["reps"],
                        "load": ex["load"],
                        "video_url": video_url,
                    }
                )
                logger.debug(f"Exercício válido adicionado: {ex['name']}")
            else:
                logger.warning(
                    f"Exercício {ex['name']} não encontrado na tabela video_urls"
                )

        if not valid_exercises:
            logger.warning(f"Nenhum exercício válido para {day}. Carregando padrão.")
            valid_exercises = [
                {
                    "name": "Supino Reto",
                    "series": 4,
                    "repetitions": 12,
                    "load": 0,
                    "video_url": video_for("Supino Reto"),
                },
                {
                    "name": "Agachamento Livre",
                    "series": 4,
                    "repetitions": 10,
                    "load": 0,
                    "video_url": video_for("Agachamento Livre"),
                },
            ]

        try:
            page.client_storage.set(cache_key, valid_exercises)
            logger.info(f"Exercícios de {day} salvos no cache: {len(valid_exercises)}")
        except Exception as e:
            logger.error(f"Erro ao salvar exercícios no cache: {str(e)}")

        logger.info(f"Exercícios válidos para {day}: {len(valid_exercises)}")
        return valid_exercises

    training_started = False
    training_time = 0
    training_running = False
    training_timer_ref = ft.Ref[ft.Text]()

    async def run_training_timer():
        """Executa o temporizador do treino."""
        nonlocal training_time, training_running
        while training_running:
            training_time += 1
            m, s = divmod(training_time, 60)
            training_timer_ref.current.value = f"Tempo: {m:02d}:{s:02d}"
            training_timer_ref.current.update()
            await asyncio.sleep(1)
            logger.debug(f"Tempo de treino atualizado: {m:02d}:{s:02d}")

    def start_training(e):
        """Inicia o treino, habilitando controles e temporizador."""
        nonlocal training_started, training_running
        training_started = True
        training_running = True
        for tile in exercise_list.controls:
            tile.enable_controls()
        start_btn.visible = False
        pause_btn.visible = True
        finish_btn.visible = True
        download_btn.visible = True
        clear_btn.visible = True
        page.run_task(run_training_timer)
        logger.info(f"Treino iniciado para o dia {day}")
        page.update()

    def pause_training(e):
        """Pausa o treino."""
        nonlocal training_running
        training_running = False
        pause_btn.visible = False
        resume_btn.visible = True
        logger.info(f"Treino pausado para o dia {day}")
        page.update()

    def resume_training(e):
        """Retoma o treino."""
        nonlocal training_running
        training_running = True
        page.run_task(run_training_timer)
        pause_btn.visible = True
        resume_btn.visible = False
        logger.info(f"Treino retomado para o dia {day}")
        page.update()

    def stop_training(e):
        """Finaliza o treino com confirmação."""
        nonlocal training_running

        def confirm(ev):
            nonlocal training_running
            if ev.control.text == "Sim":
                training_running = False
                logger.info(f"Treino finalizado para o dia {day}")
                page.go("/home")
            page.close(dlg)
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Finalizar Treino"),
            content=ft.Text("Deseja realmente finalizar o treino?"),
            actions=[
                ft.TextButton("Sim", on_click=confirm),
                ft.TextButton("Não", on_click=confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dlg)
        logger.debug("Diálogo de finalização de treino aberto")

    def favorite_ex(tile):
        """Manipula o evento de favoritar/desfavoritar exercício."""
        msg = (
            "Exercício favoritado!" if tile.is_favorited else "Exercício desfavoritado!"
        )
        page.open(ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=ft.Colors.GREEN_700 if tile.is_favorited else ft.Colors.RED_700,
        ))
        page.update()
        logger.info(
            f"Exercício {tile.exercise_name} {'favoritado' if tile.is_favorited else 'desfavoritado'}"
        )
        page.update()

    exercises = load_exercises(day)
    exercise_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=10,
        controls=[
            ExerciseTile(
                exercise_name=ex["name"],
                series=ex["series"],
                repetitions=ex["repetitions"],
                load=ex["load"],
                video_url=ex["video_url"],
                on_favorite_click=favorite_ex,
                on_load_save=lambda v: logger.info(
                    f"Carga salva para {ex['name']}: {v}kg"
                ),
                page=page,
            )
            for ex in exercises
        ],
    )

    start_btn = ft.ElevatedButton(
        "Iniciar Treino", on_click=start_training, ref=ft.Ref()
    )
    pause_btn = ft.IconButton(
        ft.Icons.PAUSE, on_click=pause_training, visible=False, ref=ft.Ref()
    )
    resume_btn = ft.IconButton(
        ft.Icons.PLAY_ARROW, on_click=resume_training, visible=False, ref=ft.Ref()
    )
    finish_btn = ft.ElevatedButton(
        "Finalizar Treino", on_click=stop_training, visible=False, ref=ft.Ref()
    )
    download_btn = ft.ElevatedButton(
        "Baixar Vídeos",
        on_click=lambda e: page.run_task(download_videos, exercises),
        visible=False,
        ref=ft.Ref(),
    )
    clear_btn = ft.ElevatedButton(
        "Limpar Vídeos", on_click=clear_downloaded_videos, visible=False, ref=ft.Ref()
    )

    control_bar = ft.Container(
        content=ft.ResponsiveRow(
            [
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/home")),
                ft.Text(ref=training_timer_ref, value="Tempo: 00:00", size=16),
                ft.Row(
                    [pause_btn, resume_btn, finish_btn, download_btn, clear_btn],
                    spacing=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=10,
        ),
        padding=10,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
    )

    return ft.Column(
        [
            control_bar,
            ft.Container(
                start_btn,
                alignment=ft.alignment.center,
                padding=10,
                visible=not training_started,
            ),
            exercise_list,
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        alignment=ft.MainAxisAlignment.START,
    )
