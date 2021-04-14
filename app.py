import subprocess
import json
from flask import Flask, jsonify, request

with open('config.json', 'r') as f:
    config = json.load(f)

max_users = int(config['max_users'])
bin_dir = config['bin_dir']

app = Flask(__name__)

senders = []

def parse_output(output: str) -> dict:
    lines = output.splitlines()
    verif_next = False
    
    data = {}
    for l in lines:
        if l.lower().startswith('seed:'):
            data['seed'] = l.split(' ')[1]
        elif l.lower().startswith('verification token:'):
            if len(l.split(' ')) >= 3:
                data['verification'] = l.split(' ')[2]
            else:
                verif_next = True
        elif verif_next:
            verif_next = False
            data['verification'] = l
    return data


@app.route("/")
def homepage():
    return "You were probably headed to /generate"


@app.route("/generate")
def gen():
    global senders

    if len(senders) >= max_users:
        return jsonify({'message': "Server busy serving others, please try later"}), 503
    
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        addr = request.environ['REMOTE_ADDR']
    else:
        addr = request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy

    if(addr in senders):
        return jsonify({'message': "Server already serving you, please try later"}), 429
    
    senders.append(addr)

    result = subprocess.run(['./seed'], stdout=subprocess.PIPE, cwd=bin_dir)
    
    try:
        senders.remove(addr)
    except ValueError:
        pass

    return jsonify(parse_output(result.stdout.decode()))


if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')

