import urllib.request
import requests
import socket
import time
import subprocess

class SocketGrabber:
    """ A horrible hack, so as to allow us to recover
        the socket we still need from urllib """

    def __init__(self):
        self.sock = None

    def __enter__(self):
        self._temp = socket.socket.close
        socket.socket.close = lambda sock: self._close(sock)
        return self

    def __exit__(self, type, value, tb):
        socket.socket.close = self._temp
        if tb is not None:
            self.sock = None

    def _close(self, sock):
        if sock._closed:
            return
        if self.sock == sock:
            return
        if self.sock is not None:
            self._temp(self.sock)
        self.sock = sock


input_audio_file = "testing.mp3"
output_audio_file = "testing_output.wav"
ip = "ip"
username = "username"
password = "password"
index = 1
base = f"http://{ip}"
chunksize = 128
sleep_time = 1.0 / 64

# Convert audio file to the required format (PCM A-law with a sample rate of 8000 Hz and 16-bit sample format)
ffmpeg_cmd = [
    "ffmpeg",
    "-i", input_audio_file,
    "-acodec", "pcm_alaw",
    "-ac", "1",
    "-ar", "8000",
    "-f", "wav",
    "-sample_fmt", "s16",
    output_audio_file,
    "-y"
]
subprocess.run(ffmpeg_cmd)

base_url = f"http://{username}:{password}@{ip}"
req = requests.put(
    f"{base_url}/ISAPI/System/TwoWayAudio/channels/{index}/open")

mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
mgr.add_password(None, [base], username, password)
auth = urllib.request.HTTPDigestAuthHandler(mgr)
opener = urllib.request.build_opener(auth)
audiopath = f"{base}/ISAPI/System/TwoWayAudio/channels/{index}/audioData"

with SocketGrabber() as sockgrab:
    req = urllib.request.Request(audiopath, method='PUT')
    resp = opener.open(req)
    output = sockgrab.sock


def frames_yield(ulaw_data, chunksize=128):
    for i in range(0, len(ulaw_data), chunksize):
        for x in [ulaw_data[i:i + chunksize]]:
            tosend = x + (b'\xff' * (chunksize - len(x)))
            time.sleep(sleep_time)
            yield tosend


with open(output_audio_file, 'rb') as file_obj:
    ulaw_data = file_obj.read()
    for dataframe in frames_yield(ulaw_data, chunksize):
        output.send(dataframe)
