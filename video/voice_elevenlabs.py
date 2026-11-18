# Generates the German narration with ElevenLabs (eleven_multilingual_v2) and mixes it to fit the scene timings.
# The API key is not read here: the session's network proxy adds it to requests to api.elevenlabs.io.
# Outside this environment set ELEVENLABS_API_KEY. Usage: python3 voice_elevenlabs.py  ->  audio/narration.wav
import json, os, subprocess, urllib.request
VOICE_ID = os.environ.get('ELEVENLABS_VOICE', 'nPczCjzI2devNBz1zQrb')  # "Brian", a default ElevenLabs voice
KEY = os.environ.get('ELEVENLABS_API_KEY', 'proxy-injected')
SEGMENTS = [  # (start second, latest end second, text)
    (0.4, 5.0, 'Wie spricht eine KI eigentlich mit deinen Apps? Das erklärt MCP.'),
    (5.6, 14.0, 'Ohne Standard braucht jede KI für jedes Tool eine eigene Anbindung. Das sind schnell zwölf Verbindungen.'),
    (14.4, 22.0, 'Die Lösung: MCP. Ein offener Standard, wie USB-C für KI. Einmal gebaut, für jede KI.'),
    (22.4, 32.0, 'Die KI-App, etwa Claude, ist der Host. Ihr Client spricht mit dem Server, und der Server mit dem echten Dienst, etwa deinem Kalender.'),
    (32.4, 40.0, 'Ein Server bietet drei Dinge an: Tools für Aktionen, Resources mit Daten zum Lesen, und Prompts als fertige Vorlagen.'),
    (40.4, 56.0, 'Ein Beispiel. Du sagst: Trag das Meeting morgen um zehn ein. Claude kennt die Tools des Kalender-Servers, wählt das passende und schickt die Daten. Der Server ruft den Kalender auf, und das Ergebnis kommt zurück. Erledigt!'),
    (56.4, 62.6, 'Ein Protokoll. Jede KI. Jedes Tool. Das ist MCP.'),
]
os.makedirs('audio', exist_ok=True)
def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))
def tts(text, f, speed, prev, nxt):
    body = {'text': text, 'model_id': 'eleven_multilingual_v2', 'language_code': 'de',
            'previous_text': prev, 'next_text': nxt,
            'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75, 'style': 0.2, 'use_speaker_boost': True, 'speed': speed}}
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128',
                                 data=json.dumps(body).encode(), headers={'xi-api-key': KEY, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r, open(f, 'wb') as out:
        out.write(r.read())
parts, report = [], []
for i, (start, end, text) in enumerate(SEGMENTS):
    f = f'audio/el{i}.mp3'
    prev = SEGMENTS[i - 1][2] if i else ''
    nxt = SEGMENTS[i + 1][2] if i + 1 < len(SEGMENTS) else ''
    for speed in (1.0, 1.06, 1.12, 1.18):
        tts(text, f, speed, prev, nxt)
        d = dur(f)
        if start + d <= end: break
    report.append((i, speed, d, end - start))
    parts.append((f, start))
inputs, filt = [], []
for k, (f, start) in enumerate(parts):
    inputs += ['-i', f]
    ms = int(start * 1000)
    filt.append(f'[{k}]aresample=48000,adelay={ms}|{ms}[a{k}]')
mix = ''.join(f'[a{k}]' for k in range(len(parts)))
filt.append(f'{mix}amix=inputs={len(parts)}:normalize=0,apad=whole_dur=63,atrim=0:63,loudnorm=I=-16:TP=-1.5[out]')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(filt), '-map', '[out]', '-ac', '2', '-ar', '48000', 'audio/narration.wav'], check=True)
for r in report: print('segment %d: speed %.2f, %.2fs of %.2fs' % r)
