'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot


class Player(Bot):
    '''
    A pokerbot.
    '''

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.
        Arguments:
        Nothing.
        Returns:
        Nothing.
        '''
        
        self.have_pair = False #keep track of whether or not we have strong hole cards
        self.have_full_house = False
        self.have_three = False
        self.raiseflag = False
        self.double_pair = False
    def look_for_matches(self, my_cards,board_cards = None):
        self.ranks = {}
        if board_cards !=None:
            all_cards = my_cards+board_cards
        else:
            all_cards = my_cards



        for card in all_cards:
            card_rank  = card[0]
            card_suit = card[1]


            if card_rank in self.ranks:
                self.ranks[card_rank].append(card)
            else:
                self.ranks[card_rank] = [card]

        threes = []
        pairs = [] #keeps track of the pairs that we have 
        singles = [] #other 

        for rank in self.ranks:
            cards = self.ranks[rank]

            if len(cards) == 1: #single card, can't be in a pair
                singles.append(cards[0])
            elif len(cards) == 3:
                threes.append(cards[0])
            
            else: #len(cards) == 2: #a single pair can be made here, add them all
                pairs += cards
                pairs.append(cards[0])
            



        if len(pairs) > 0: #we found a pair! update our state to say that this is a strong round
            self.have_pair = True
            self.raiseflag = True
            if len(pairs) ==2:
                self.double_pair = True

        if len(threes) > 0:
            self.have_three = True
            self.raiseflag = True
        if len(threes) > 0 and len(pairs) > 0:
            self.have_full_house = True
            self.raiseflag = True
        
        
        allocation = pairs + singles 
        pass

    

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.
        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.
        Returns:
        Nothing.
        '''
        my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your cards
        
        big_blind = bool(active)  # True if you are the big blind
        

        self.look_for_matches(my_cards) #allocate our cards to our board allocations

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.
        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.
        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed

        self.have_pair = False #keep track of whether or not we have strong hole cards
        self.have_full_house = False
        self.have_three = False
        self.raiseflag = False
        self.double_pair = False

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.
        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.
        Returns:
        Your action.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
       
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        net_upper_raise_bound = round_state.raise_bounds()
        stacks = [my_stack, opp_stack] #keep track of our stacks

        net_cost = 0
        my_action = None

        self.look_for_matches(my_cards,board_cards)
        if (RaiseAction in legal_actions and self.raiseflag): #only consider raising if the hand we have is strong
            min_raise, max_raise = round_state.raise_bounds()
            max_cost = max_raise - my_pip
            max_cost_affordable = max_cost <= my_stack - net_cost

            if max_cost_affordable:
                if self.have_full_house:
                    my_action = RaiseAction(max_raise) #GO ALL IN!!!
                    net_cost += max_cost
                    
                    print("FULL HOUSE")
                elif self.have_three: #make sure the max_cost is something we can afford! Must have at least this much left after our other costs
                    my_action = RaiseAction(round(max_raise-((max_raise-min_raise)/5))) 
                    net_cost += max_cost
                    print("three of a kind")
                elif self.double_pair:
                    my_action = RaiseAction(round(min_raise+((max_raise-min_raise)/2))) 
                    net_cost += max_cost
                    print("double pair")
                elif self.have_pair: #make sure the max_cost is something we can afford! Must have at least this much left after our other costs
                    my_action = RaiseAction(round(min_raise+((max_raise-min_raise)/10))) #half bet
                    net_cost += max_cost
                    print("pair")
                
                elif CallAction in legal_actions[i]: # check-call
                    my_action = CallAction()
                    net_cost += continue_cost

                else:
                    my_action = CheckAction()
        elif CheckAction in legal_actions: #if we can call, do so
            my_action = CheckAction()
        else:
            my_action = CallAction()
            net_cost += continue_cost #add the cost of the continue to our net cost


        return my_action




        


if __name__ == '__main__':
    run_bot(Player(), parse_args())