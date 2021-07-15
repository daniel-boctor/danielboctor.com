from django.shortcuts import render
from django.http import JsonResponse
import json, ast
from .tictactoe_AI.tictactoe import *
from .nim_AI.nim import NimAI
from .neuralnets_AI.mnist import classify
import os

# Create your views here.

def tictactoe(request):
    return render(request, "ai/tictactoe.html")

def tictactoe_api(request, algorithm, training):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    state = json.loads(request.body)["state"]
    if terminal(state) == True:
        return JsonResponse({"won": winner(state)})

    if algorithm == "Q":
        file = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tictactoe_AI"), f"{training}.json")
        with open(file, 'r') as f:
            q = json.load(f)
            q = {ast.literal_eval(k):v for k, v in q.items()}
            AI = tictactoe_AI()
            AI.q = q

        move = AI.choose_action(state, epsilon=False)
    if algorithm == "M":
        move = minimax(state)

    current_player = player(state)
    state[move[0]][move[1]] = current_player
    if terminal(state) == True:
        return JsonResponse({"move": move, "player": current_player, "won": winner(state)})
    return JsonResponse({"move": move, "player": current_player})


def nim(request):
    return render(request, "ai/nim.html")

def nim_api(request, algorithm, training):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    state = json.loads(request.body)["state"]
    if NimAI.terminal(state) == True:
        return JsonResponse({"won": "ai"})

    if algorithm == "Q":
        file = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nim_AI"), f"{training}.json")
        with open(file, 'r') as f:
            q = json.load(f)
            q = {ast.literal_eval(k):v for k, v in q.items()}
            AI = NimAI()
            AI.q = q

        move = AI.choose_action(state, epsilon=False)

    state[move[0]] -= move[1]

    if NimAI.terminal(state) == True:
        return JsonResponse({"state": state, "won": "human"})
    return JsonResponse({"state": state})

def neural_nets(request):
    return render(request, "ai/nn.html")

def neural_nets_api(request, width):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    pixels = json.loads(request.body)["pixels"]
    nd_pixels = []
    for _ in range(width):
        nd_pixels.append([pixels.pop(0)/255.0 for _ in range(width)])
    file = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), "neuralnets_AI"), f"{'model'}.h5")
    image = deepcopy(nd_pixels)
    for i in range(width):
        for j in range(width):
            if nd_pixels[i][j]:
                image[i][j] = (250 / 255)
                if i + 1 < width:
                    image[i + 1][j] = max((220 / 255), nd_pixels[i + 1][j])
                if j + 1 < width:
                    image[i][j + 1] = max((220 / 255), nd_pixels[i][j + 1])
                if i + 1 < width and j + 1 < width:
                    image[i + 1][j + 1] = max((190 / 255), nd_pixels[i + 1][j + 1])
    classification, confidence = classify(file, image)
    return JsonResponse({"classification": f"{classification}", "confidence": f"{round(confidence*100, 6)}%"})