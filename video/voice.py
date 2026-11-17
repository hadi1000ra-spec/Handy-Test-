# Generates the German narration with espeak-ng + MBROLA and mixes it to fit the scene timings.
# Usage: python3 voice.py   ->  audio/narration.wav
import subprocess, json, os
VOICE = 'mb-de6'  # male German MBROLA voice
# (start second, latest end second, text)  -- English terms written as they are spoken
SEGMENTS = [
    (0.4, 5.0, 'Wie spricht eine KI mit deinen Apps?'),
    (5.6, 14.0, 'Ohne Standard braucht jede KI für jedes Tool eine eigene Anbindung. Das sind schnell zwölf Verbindungen.'),
    (14.4, 22.0, 'Die Lösung: Em Tse Pe. Ein offener Standard, wie U S B C für KI. Einmal gebaut, für jede KI.'),
    (22.4, 32.0, 'Die KI-App, etwa Klohd, ist der Host. Ihr Klaient spricht mit dem Server, und der Server mit dem echten Dienst, etwa deinem Kalender.'),
    (32.4, 40.0, 'Ein Server bietet Tools für Aktionen, Ressourcen mit Daten, und Prompts als Vorlagen.'),
    (40.4, 56.0, 'Ein Beispiel. Du sagst: Trag das Meeting morgen um zehn ein. Klohd wählt das passende Tool und schickt die Daten. Der Server ruft den Kalender auf, und das Ergebnis kommt zurück. Erledigt!'),
    (56.4, 62.6, 'Ein Protokoll. Jede KI. Jedes Tool. Das ist Em Tse Pe.'),
]
def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))
parts, report = [], []
for i, (start, end, text) in enumerate(SEGMENTS):
    f = f'audio/seg{i}.wav'
    for speed in (145, 155, 165, 175, 185):
        subprocess.run(['espeak-ng', '-v', VOICE, '-s', str(speed), '-p', '45', '-w', f, text], check=True, capture_output=True)
        d = dur(f)
        if start + d <= end: break
    report.append((i, speed, round(d, 2), round(end - start, 2)))
    parts.append((f, start))
inputs, filt = [], []
for k, (f, start) in enumerate(parts):
    inputs += ['-i', f]
    ms = int(start * 1000)
    filt.append(f'[{k}]aresample=48000,adelay={ms}|{ms}[a{k}]')
mix = ''.join(f'[a{k}]' for k in range(len(parts)))
filt.append(f'{mix}amix=inputs={len(parts)}:normalize=0,apad=whole_dur=63,atrim=0:63,loudnorm=I=-16:TP=-1.5[out]')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(filt), '-map', '[out]', '-ac', '2', '-ar', '48000', 'audio/narration.wav'], check=True)
for r in report: print('segment %d: speed %d, %.2fs of %.2fs' % r)
