import random

OPTIONS = [
    "rock",
    "paper",
    "scissors",
    "spock",
    "lizard",
    "air",
    "water",
    "fire",
    "sponge",
    "wolf",
    "tree",
    "human",
    "snake",
    "gun",
    "lightning",
    "devil",
    "dragon",
    "alien",
]

RULES = {
    "rock": ["scissors", "lizard", "air", "fire", "snake", "gun", "devil", "alien"],
    "paper": ["rock", "spock", "water", "air", "tree", "human", "lightning", "dragon"],
    "scissors": ["paper", "lizard", "water", "fire", "wolf", "tree", "gun", "devil"],
    "spock": ["scissors", "rock", "fire", "wolf", "human", "snake", "lightning", "alien"],
    "lizard": ["spock", "paper", "water", "sponge", "tree", "human", "gun", "dragon"],
    "air": ["water", "fire", "sponge", "wolf", "snake", "lightning", "devil", "alien"],
    "water": ["fire", "sponge", "wolf", "tree", "human", "gun", "devil", "dragon"],
    "fire": ["sponge", "wolf", "tree", "snake", "human", "lightning", "dragon", "alien"],
    "sponge": ["wolf", "tree", "human", "snake", "gun", "lightning", "devil", "alien"],
    "wolf": ["tree", "human", "snake", "gun", "devil", "dragon", "lightning", "alien"],
    "tree": ["human", "snake", "gun", "lightning", "devil", "dragon", "alien", "air"],
    "human": ["snake", "gun", "lightning", "devil", "dragon", "alien", "air", "water"],
    "snake": ["gun", "lightning", "devil", "dragon", "alien", "air", "water", "fire"],
    "gun": ["lightning", "devil", "dragon", "alien", "air", "water", "fire", "sponge"],
    "lightning": ["devil", "dragon", "alien", "air", "water", "fire", "sponge", "wolf"],
    "devil": ["dragon", "alien", "air", "water", "fire", "sponge", "wolf", "tree"],
    "dragon": ["alien", "air", "water", "fire", "sponge", "wolf", "tree", "human"],
    "alien": ["air", "water", "fire", "sponge", "wolf", "tree", "human", "snake"],
}



def play_round() -> int:
    print("\nChoose one of the options:")
    for idx, option in enumerate(OPTIONS):
        print(f"{idx + 1}: {option}")

    player1_choice = int(input("\nPlayer 1 choice (Enter the number): ")) - 1
    print("\n" * 100)
    print("\nChoose one of the options:")
    for idx, option in enumerate(OPTIONS):
        print(f"{idx + 1}: {option}")
    
    player2_choice = int(input("\nPlayer 2 choice (Enter the number): ")) - 1
    print("\n" * 100)
    print("Player 1 played", OPTIONS[player1_choice])
    print("Player 2 played", OPTIONS[player2_choice])
    if player1_choice == player2_choice:
        print("\nIt's a draw!")
        return 0
    elif OPTIONS[player2_choice] in RULES[OPTIONS[player1_choice]]:
        print("\nPlayer 1 wins!")
        return 1
    else:
        print("\nPlayer 2 wins!")
        return 2


def play_game():
    player1_hp = 100
    player2_hp = 100
    kill = 20
    while(player1_hp > 0 and player2_hp > 0):
        round_winner = play_round()
        if round_winner == 0:
            continue
        elif round_winner == 1:
            player2_hp -= kill
        else:
            player1_hp -= kill

        print("Player 1 HP:", player1_hp)
        print("Player 2 HP:", player2_hp)

    print("\nGame Over!")
    if player1_hp > player2_hp:
        print("Player 1 wins!")
    else:
        print("Player 2 wins!")



if __name__ == "__main__":
    print("Welcome to Multi-Dimensional Rock-Paper-Scissors!")
    play_game() 

