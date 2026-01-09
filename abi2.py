import win32com.client

speaker = win32com.client.Dispatch("SAPI.SpVoice")
voices = speaker.GetVoices()

for i, v in enumerate(voices):
    print(i, "-", v.GetDescription())
