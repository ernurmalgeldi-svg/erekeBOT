import os
import logging
import ffmpeg
from groq import AsyncGroq

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 25
CHUNK_DURATION_SEC = 300  # 5 минут

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))


def convert_ogg_to_wav(input_path: str, output_path: str):
    """OGG файлын WAV форматына конвертациялайды."""
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, ar=16000, ac=1, format='wav')
            .overwrite_output()
            .run(quiet=True)
        )
        return True
    except Exception as e:
        logger.error(f"Конвертация қатесі: {e}")
        return False


def get_file_size_mb(file_path: str) -> float:
    """Файл өлшемін МБ-та қайтарады."""
    return os.path.getsize(file_path) / (1024 * 1024)


def split_audio(input_path: str, chunk_duration: int = CHUNK_DURATION_SEC) -> list:
    """Ұзын аудионы чанктарға бөледі."""
    chunks = []
    try:
        probe = ffmpeg.probe(input_path)
        duration = float(probe['format']['duration'])
        
        if duration <= chunk_duration:
            return [input_path]
        
        num_chunks = int(duration // chunk_duration) + 1
        for i in range(num_chunks):
            start = i * chunk_duration
            chunk_path = f"chunk_{i}.wav"
            (
                ffmpeg
                .input(input_path, ss=start, t=chunk_duration)
                .output(chunk_path, ar=16000, ac=1, format='wav')
                .overwrite_output()
                .run(quiet=True)
            )
            chunks.append(chunk_path)
        return chunks
    except Exception as e:
        logger.error(f"Аудио бөлу қатесі: {e}")
        return [input_path]


async def transcribe_audio(file_path: str) -> str:
    """Аудио файлды мәтінге айналдырады."""
    try:
        # Өлшемін тексер
        size_mb = get_file_size_mb(file_path)
        if size_mb > MAX_FILE_SIZE_MB:
            return f"❌ Файл тым үлкен: {size_mb:.1f} МБ (лимит {MAX_FILE_SIZE_MB} МБ)"

        # WAV-қа конвертациялау
        wav_path = file_path.replace(".ogg", ".wav").replace(".opus", ".wav")
        if not convert_ogg_to_wav(file_path, wav_path):
            return "❌ Аудио конвертация сәтсіз аяқталды"

        # Чанктарға бөлу (5 минуттан ұзын болса)
        chunks = split_audio(wav_path)
        full_text = ""

        for chunk_path in chunks:
            with open(chunk_path, "rb") as audio_file:
                transcription = await groq_client.audio.transcriptions.create(
                    file=(chunk_path, audio_file.read()),
                    model="whisper-large-v3",
                    language=None,
                )
                full_text += transcription.text + " "

            # Чанк файлын өшір
            if chunk_path != wav_path and os.path.exists(chunk_path):
                os.remove(chunk_path)

        # WAV файлын өшір
        if os.path.exists(wav_path):
            os.remove(wav_path)

        return full_text.strip()

    except Exception as e:
        logger.error(f"Транскрипция қатесі: {e}")
        return f"❌ Транскрипция қатесі: {str(e)}"