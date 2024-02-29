from ..things.items import Item
import persona #TODO: update with persona
from ..things.characters import Character
from collections import defaultdict, Counter

class Dialogue:
    """This class handles dialogue happening between 2 or more characters.
    """

    def __init__(self, participants):
        """
        Args:
            participants (List(Character)): sorted list of characters by initiative.
        """

        self.participants = participants
        self.participants_number = len(participants)
        self.dialogue_history = 'This dialogue just started. The people participating in this dialogue are: '
        for participant in self.participants:
            self.dialogue_history += f"{participant.name}, "

    def get_persona(self, character):
        """This method turns a character's persona into a string for prompting
        """
        return character.persona

    def get_memory(self, character):
        """This method turns a character's memories into a string for prompting
        """
        return character.memory
    
    def get_dialogue_history(self):
        return self.dialogue_history

    def add_to_dialogue_history(self, message):
        self.dialogue_history = f"{self.dialogue_history}\n{message}"

    def speak(self, character, prompt):
        prompt = f"What would {character.name} say?"
        gpt_reply = "TEST"  #TODO: fix with gpt reply
        return gpt_reply

    def is_dialogue_over(self):
        if len(self.participants) <= 1:
            return True
        return False
    
    def dialogue_loop(self):
        # start with character with highest initiative
        # get their persona, memory and dialogue history
        # build a prompt, pass to gpt and ask if they want to let someone else speak, speak themselves or end the dialogue
        # if speak, add comment to dialogue history and move ot next character
        # if pass, move on to next character. 
        # if vote end, remove character from participants and move on to next character. 
        # if all but one leave, end dialogue.
        while True:
            for character in self.participants:
                persona = self.get_persona(character)
                memory = self.get_memory(character)
                history = self.get_dialogue_history()
                prompt_question = f"It's now {character.name}'s turn to speak. Would {character.name} say something, let someone else talk, or walk away from the conversation?"
                prompt = persona + memory + history + prompt_question
                #add a function to interpret answer from GPT
                answer = 'speak'  #TODO: fix with GPT reply
                if answer == 'speak':
                    reply = self.speak(character, prompt)
                    self.add_to_dialogue_history(f"{character.name} said: {reply}")
                elif answer == 'skip':
                    self.add_to_dialogue_history(f"{character.name} didn't say anything.")
                elif answer == 'end':
                    self.add_to_dialogue_history(f"{character.name} left the conversation.")
                    #TODO: remove participant from list
            if self.is_dialogue_over():
                break
        # when dialogue ends, add entire dialogue history to character's memories
                
