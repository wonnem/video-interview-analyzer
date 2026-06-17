from pydub import AudioSegment


def extract_audio(video_path: str, output_path: str) -> float:
    audio = AudioSegment.from_file(video_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav")
    return len(audio) / 1000.0
