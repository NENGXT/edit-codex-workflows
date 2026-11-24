"""Cloud-only batch inference; input JSON and reference live outside source code."""
import os
os.environ.update({"MPLBACKEND": "Agg", "ORT_DISABLE_TELEMETRY": "1",
    "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
    "GRADIO_ANALYTICS_ENABLED": "False", "TOKENIZERS_PARALLELISM": "false",
    "OMP_NUM_THREADS": "4", "MKL_NUM_THREADS": "4", "version": "v5turbo", "language": "en_US"})
import argparse
import hashlib
import json
from pathlib import Path
import signal
import sys
import time


def run(root, job_path, out):
    job = json.loads(job_path.read_text())
    ref = Path(job['reference'])
    if not job.get('reference_use_approved'):
        raise ValueError('Explicit reference upload and synthesis authorization required')
    if hashlib.sha256(ref.read_bytes()).hexdigest() != job['reference_sha256']:
        raise ValueError('Reference SHA-256 mismatch')
    items = job['items']
    ids = [x['id'] for x in items]
    if not items or len(set(ids)) != len(ids):
        raise ValueError('Batch must contain unique IDs')
    if any(not i or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in i) for i in ids):
        raise ValueError('Unsafe output ID')
    if any(not x['text'].strip() for x in items):
        raise ValueError('Empty text')
    if out.exists():
        raise FileExistsError('Output already exists; use a fresh job directory')
    out.mkdir(parents=True)
    source = root / 'source'
    os.environ['NLTK_DATA'] = str(root / 'nltk_data')
    os.chdir(source)
    sys.path[:0] = [str(source), str(source / 'GPT_SoVITS')]
    import torch
    import numpy as np
    import soundfile as sf
    from GPT_SoVITS.TTS_infer_pack.TTS import TTS
    if not torch.cuda.is_available() or 'T4' not in torch.cuda.get_device_name(0):
        raise RuntimeError('T4 CUDA device required; no CPU fallback')
    torch.set_num_threads(4)
    model = TTS({'custom': {'device': 'cuda:0', 'is_half': False, 'version': 'v5turbo',
        't2s_weights_path': 'GPT_SoVITS/pretrained_models/s1v3.ckpt',
        'vits_weights_path': 'GPT_SoVITS/pretrained_models/gsv-v5-pretrained/s2Gv5turbo.pth',
        'bert_base_path': 'GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large',
        'cnhuhbert_base_path': 'GPT_SoVITS/pretrained_models/chinese-hubert-base'}})
    settings = dict(top_k=15, top_p=1.0, temperature=1.0, text_split_method='cut5',
        batch_size=1, speed_factor=1.0, seed=42, parallel_infer=True, repetition_penalty=1.35,
        sample_steps=4, cfg_rate=0.0, super_sampling=False, streaming_mode=False,
        return_fragment=False, use_cuda_graph=False, use_flash_attention=False)
    speed = float(job.get('speed_factor', 1.0))
    if not 0.75 <= speed <= 1.25:
        raise ValueError('speed_factor must be between 0.75 and 1.25')
    settings['speed_factor'] = speed
    split_method = job.get('text_split_method', 'cut5')
    if split_method not in ('cut0', 'cut5'):
        raise ValueError('Supported text_split_method values are cut0 and cut5')
    settings['text_split_method'] = split_method
    report = {'status': 'running', 'gpu': torch.cuda.get_device_name(0), 'model': 'v5turbo', 'files': []}
    def timeout(sig, frame):
        raise TimeoutError('One synthesis exceeded 300 seconds')
    signal.signal(signal.SIGALRM, timeout)
    try:
        for item in items:
            seed = item.get('seed', settings['seed'])
            if not isinstance(seed, int) or not 0 <= seed < 2**32:
                raise ValueError('seed must be an unsigned 32-bit integer')
            started = time.monotonic()
            signal.alarm(300)
            with torch.inference_mode():
                chunks = list(model.run(dict(settings, seed=seed, text=item['text'], text_lang=item['language'],
                    ref_audio_path=str(ref), prompt_text=job['prompt_text'], prompt_lang=job['prompt_language'])))
            signal.alarm(0)
            if not chunks or any(x[0] != chunks[0][0] for x in chunks):
                raise RuntimeError('Missing or inconsistent audio chunks')
            sr = chunks[0][0]
            audio = np.concatenate([x[1] for x in chunks])
            if not audio.size or not np.isfinite(audio).all():
                raise RuntimeError('Empty or nonfinite audio')
            path = out / (item['id'] + '.wav')
            temporary = path.with_suffix('.partial')
            sf.write(temporary, audio, sr, format='WAV', subtype='PCM_16')
            decoded, rate = sf.read(temporary, dtype='float32', always_2d=True)
            rms = float(np.sqrt(np.mean(decoded ** 2)))
            if rate != sr or len(decoded) != len(audio) or len(audio) / sr < .5 or rms < .001:
                raise RuntimeError('Audio verification failed')
            temporary.rename(path)
            report['files'].append({'name': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'sample_rate': sr, 'channels': decoded.shape[1], 'subtype': 'PCM_16',
                'duration': len(audio) / sr, 'rms': rms, 'peak': float(np.abs(decoded).max()),
                'seconds': time.monotonic() - started, 'seed': seed,
                'text_split_method': split_method, 'speed_factor': speed})
            print('COMPLETED', item['id'], flush=True)
        report['status'] = 'complete'
    finally:
        signal.alarm(0)
        (out / 'manifest.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--job', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.job.resolve(), a.output.resolve())
