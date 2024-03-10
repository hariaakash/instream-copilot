from dotenv import load_dotenv
load_dotenv()

import speech_recognition as sr
import replicate
import IPython.display as ipd
import time
import socket
import subprocess
from multiprocessing import Process

model_name = "meta/llama-2-7b-chat"
# voice_name = "en-GB-LibbyNeural"
voice_name = "en-US-JennyNeural"
character_name = "prime"
character_name_misspelling = "prine"
character_desc = f"""
In this role, your task is to discern whether I am addressing you, {character_name}, or not. You are known as {character_name}, though {character_name_misspelling} is also considered a valid way to refer to you. Phrases like "Hey, are you listening?" or "You, {character_name}, often enjoy games like this" are clues that I may be speaking directly to you. However, keep in mind that I'm engaging with a Twitch audience, so not everything I say is necessarily directed at you specifically. You should actively listen to the conversation. If you recognize that I'm speaking directly to you, your response should be a simple "<<yes>>." If you're unsure or unable to determine whether I'm addressing you, your response should be "<<no>>." In this role, you are {character_name}, and you should avoid mentioning that you are an AI. Respond only in a conversational manner, as {character_name} would.
"""
system_prompt = f"""
{character_desc}
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.\n\nIf a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information. Don't include any emojis or dramatic events similar to adjusts glasses or winks or nods.
"""

system_prompt_comment = f"""
{system_prompt}
Reply back to the below user comment kindly and respectfully. If the comment is not respectful, do not reply to it. If the comment is not clear, ask for clarification.
"""
def text_to_text(text: str, comment: bool = False) -> str:
    output = replicate.run(
        model_name,
        input={
            "debug": False,
            "top_k": -1,
            "top_p": 1,
            "prompt": text,
            "temperature": 0.75,
            "system_prompt": system_prompt_comment if comment else system_prompt,
            "max_new_tokens": 800,
            "min_new_tokens": -1,
            "repetition_penalty": 1
        },
        )
    return ''.join(output)

def text_to_speech(text: str, comment: bool = False):
    current_time = time.time()
    file_name = f"audio/{current_time}.wav"
    res = text_to_text(text, comment)
    if "<<no>>" in res:
        return False, file_name
    final = res.replace("<<yes>>", "").replace("<<no>>", "").strip()
    cmd = f"edge-tts --text \"{final}\" --write-media {file_name} --voice {voice_name}"
    subprocess.run(cmd, shell=True)
    # !edge-tts --text "{final}" --write-media $file_name
    return True, file_name

def start_listening():
    r = sr.Recognizer()
    while True:
        with sr.Microphone() as source:
            print("Speak Anything :")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                print("You said : {}".format(text))
                should_play, audio_file_name = text_to_speech(text)
                print("Was it yes or no", should_play, audio_file_name)
                if should_play:
                    print("Playing the audio")
                    subprocess.call(["afplay", audio_file_name])
                    # ipd.Audio(audio_file_name)
            except:
                print("Sorry could not recognize what you said")

def twitch_chat_listener():
    print("Starting the chat listener")
    # Twitch IRC server and port
    HOST = "irc.chat.twitch.tv"
    PORT = 6667

    # Twitch channel to connect to
    CHANNEL = "#haxforlyf"

    # Twitch credentials
    NICK = "QQ"
    PASS = "oauth:mpp8nrszapzddvfq65eetqyv7do75u"

    # Create a socket and connect to the Twitch IRC server
    sock = socket.socket()
    sock.connect((HOST, PORT))

    # Send the authentication and channel join commands
    sock.send(f"PASS {PASS}\r\n".encode())
    sock.send(f"NICK {NICK}\r\n".encode())
    sock.send(f"JOIN {CHANNEL}\r\n".encode())

    # Listen for incoming messages
    while True:
        resp = sock.recv(2048).decode()
        if resp.startswith("PING"):
            sock.send("PONG\r\n".encode())
        elif len(resp) > 0:

            # Split the message into components
            components = resp.split()

            # Check if it's a chat message
            if len(components) >= 2 and components[1] == "PRIVMSG":
                # Extract the message, channel, and username
                message = " ".join(components[3:])[1:]
                channel = components[2]
                username = components[0].split("!")[0][1:]

                # Print the message, channel, and username
                print(f"[{channel}] {username}: {message}")
                prompt = f"""
                    {username}: {message}
                """
                text_to_speech(prompt, comment=True)

if __name__ == "__main__":
    p1 = Process(target=start_listening)
    p1.start()
    p2 = Process(target=twitch_chat_listener)
    p2.start()
    p1.join()
    p2.join()