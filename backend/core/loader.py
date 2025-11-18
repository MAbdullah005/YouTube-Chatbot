from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound
import re

def load_youtube_transcript(url):
    video_id = re.findall(r"v=([^&]+)", url)[0]

    try:
        # Try English first
        api_yt=YouTubeTranscriptApi()
        transcript=api_yt.fetch(video_id)
        #transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    except NoTranscriptFound:
        # If English is not available, try ANY auto-generated subtitles
        api_yt=YouTubeTranscriptApi()
        transcript_list=api_yt.fetch(video_id)

        try:
            transcript = transcript_list.find_transcript(['hi', 'ur', 'en'])
        except:
            # Last fallback: take the FIRST available transcript
            transcript = transcript_list.find_generated_transcript(transcript_list._generated_transcripts.keys())

    #text = " ".join([entry['text'] for entry in transcript])
    raw_data=transcript.to_raw_data()
    text=" ".join(chunk['text'] for chunk in raw_data)
    return text
