'''
Created on Nov 22, 2014

@author: JGang
'''
from Feature import Feature

class DiffLiberties(Feature):
    '''
    classdocs
    '''
    def calculate_feature(self):
        black_groups = StoneGrouper(self.start, True)
        black_liberties = calculate_liberties(black_groups)
        
        white_groups = StoneGrouper(self.start, False)
        white_liberties = calculate_liberties(white_groups)
        
        first_liberties = black_liberties - white_liberties
        
        black_groups = StoneGrouper(self.move, True)
        black_liberties = calculate_liberties(black_groups)
        
        white_groups = StoneGrouper(self.move, False)
        white_liberties = calculate_liberties(white_groups)
        
        second_liberties = black_liberties - white_liberties
        
        return first_liberties - second_liberties
        
    def calculate_liberties(self, groups):
        ans_libs = 0
        for group in black_groups:
            current_liberties = set()
            for current_x, current_y in group:
                moves = [(current_x - 1, current_y), (current_x + 1, current_y), (current_x, current_y - 1), (current_x, current_y + 1)]
                for cm in moves:
                    if cm[0] < 0 or cm[0] > self.start.x or cm[1] < 0 or cm[1] > self.start.y:
                        continue
                    elif not (cm in self.start.black_moves or cm in self.start.white_moves):
                        current_liberties.add(cm)
            ans_libs += len(current_liberties)
        return ans_libs
