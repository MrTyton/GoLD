'''
Created on Nov 28, 2014

@author: JBlackmore
'''
import sys
import time
import os
import csv
import argparse

from gold.extraneous.MoveTreeParser import MoveTreeParser,\
    UnspecifiedProblemType
from gold.models.board import IllegalMove
from random import seed, shuffle
from gold.models.search import MinMaxTree
from gold.extraneous.life import determineLife
from gold.extraneous.terminalLife import findAliveGroups
from gold.learn.Model import Model
from gold.ui.Launcher import Launcher
from glob import glob

class YouLoseException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
def print_move(label, move, sw=-1, sb=-1, w=-1, b=-1, prob=None, etime=None):
    if w<0:
        liveWGr = determineLife(move, False)
        w = len(liveWGr)
    if b<0:
        liveBGr = determineLife(move, True)
        b = len(liveBGr)
    if prob is None:
        probS=''
    else:
        probS = ' {:.3f}'.format(prob)
    if etime is None:
        timeS = ''
    else:
        timeS = ' ({:.1f} seconds).'.format(etime)
    if sw<0 and sb<0:
        print('{}: w={}, b={}, nw={}, nb={}{}{}'.format(label,w,b,len(move.white_stones),len(move.black_stones),probS, timeS))
    else:
        print('{}: w={}, b={}, sw={}, sb={}, nw={}, nb={}{}{}'.format(label,w,b,sw,sb,len(move.white_stones),len(move.black_stones),probS,timeS))

def get_terminal_states(mtp):
    ss = mtp.getSolutionPaths()
    isblack = mtp.blackFirst != mtp.flipColors
    move = mtp.start.clone()
    solutionStates = set()
    terminalIncorrectStates = set()
    print_move('start ({}x{})'.format(move.x, move.y), move)
    longestPath = 0
    isBtL = (mtp.problemType == 1 or mtp.problemType==3)
    print(mtp.getProblemTypeDesc()+' - black={}, isBtL={}'.format(isblack, isBtL))
    print('SOLUTIONS:')
    for spath in ss:
        pathLength = 0
        move = mtp.start.clone()
        sb = len(determineLife(mtp.start, True))
        sw = len(determineLife(mtp.start, False))
        for step in spath:
            pathLength += 1
            if pathLength>longestPath:
                longestPath = pathLength
            fm = mtp.formatMove(mtp.moveID[step])
            move.place_stone(fm['x'], fm['y'], fm['isBlack'])
            color = 'B' if fm['isBlack'] else 'W'
            print_move('{}({},{})'.format(color,fm['x'],fm['y']), move, sw=sw, sb=sb)
            if step in mtp.getTerminalStates():
                if step in mtp.getSolutionStates():
                    solutionStates.add(move.clone())
                else:
                    terminalIncorrectStates.add(move.clone())

        print('------------')
    return [solutionStates, terminalIncorrectStates, longestPath]

def test_problem(mtp, modelBtL, modelWtK, maxdepth=10):
    [solutionStates, terminalIncorrectStates, longestPath] = get_terminal_states(mtp)

    move = mtp.start.clone()
    sb = len(determineLife(mtp.start, True))
    sw = len(determineLife(mtp.start, False))
    pathLength = 0
    isblack = mtp.blackFirst != mtp.flipColors
    isBtL = (mtp.problemType == 1 or mtp.problemType==3)
    print('GOLD:')
    if isblack:
        mmt = MinMaxTree(move, True, not isBtL, blackModel=modelBtL, whiteModel=modelWtK)
    else:
        mmt = MinMaxTree(move, False, isBtL, blackModel=modelBtL, whiteModel=modelWtK)
    passed = False
    firstMove=True
    while( move not in solutionStates and pathLength<2*longestPath+1):
        color = 'B' if isblack else 'W'
        start = time.clock()
        '''
            if firstMove:
            ui=Launcher(400,400,50,max(move.x,move.y))
            ui.setBoard(move)
            ui.drawBoard()
            ui.mainloop()
            move.place_stone(1,5, True)
            nextMove = MinMaxTree(move, False, not isBtL, blackModel=modelBtL, whiteModel=modelWtK)
            nextMove.i = 1
            nextMove.j = 5
            mmt = nextMove
            firstMove=False
            b = len(determineLife(move, True))
            w = len(determineLife(move, False))
            print_move('{}({},{})'.format(color,mmt.i, mmt.j), move, sb=sb, sw=sw, b=b, w=w)
            isblack = not isblack
            pathLength = pathLength+1
            continue
        else:
        '''
        nextMove = mmt.decideNextMove()
        if nextMove is None:
            print('Pass.')
            if passed:
                if isBtL and len(determineLife(move, True))>0:
                    print('Two passes and Black lives. You win!!')
                    return
                raise YouLoseException('Two passes in a row. You Lose!')
            passed=True
            continue
        
        mmt = nextMove
        try:
            move.place_stone(mmt.i, mmt.j, isblack)
        except IllegalMove as im:
            print ('{}: decided it was the next move, no recovery.'.format(im))
            raise im
        #b = len(determineLife(move,True))
        b = len(determineLife(move, True))
        w = len(determineLife(move, False))
        print_move('{}({},{})'.format(color,mmt.i, mmt.j), move, sb=sb, sw=sw, b=b, w=w,prob=mmt.value, etime=time.clock()-start)
        if move in terminalIncorrectStates:
            raise YouLoseException('Haha! You lose!')
        if move in solutionStates:
            print('Solution matched!! You Win!! ')
            return mtp
        if b>sb:
            if isBtL:
                print('You Win!!! Black has {} groups that are unconditionally alive!'.format(b))
                return mtp
            else:
                raise YouLoseException('Black lives!! You Lose!!')
        pathLength = pathLength+1
        if pathLength>=2*longestPath+1:
            if not isBtL:
                start = time.clock()
                print('Searching for black to live...')
                numAliveGroups= len(findAliveGroups(move, True))
                searchTime= time.clock()-start
                print('Search took {:1f} seconds. {} alive.'.format(searchTime, '{} groups are'.format(numAliveGroups) if numAliveGroups !=1 else '1 group is'))
                if searchTime>600.0:
                    if maxdepth>3:
                        maxdepth -=1
                        print('Reducing search depth to {}'.format(maxdepth))
                    else:
                        print('Search depth is already down to 3!')
                if numAliveGroups>0:
                    raise YouLoseException('Too many moves and black can live, you lose!!')
                print('You win!! Black is dead!')
                return mtp
            raise YouLoseException('Too many moves, you lose!!')
            
        isblack = not isblack
        mmt.promote()
    '''
    ui=Launcher(400,400,50,max(move.x,move.y))
    ui.setBoard(move)
    ui.drawBoard()
    ui.mainloop()
    '''
def parse_problem_filename(probfile):
    subpaths = probfile.split('/')
    if subpaths[-1].rfind('\\')>0:
        subsub = subpaths[-1].split('\\')
        problemId = subsub[-1]
        difficulty = subsub[-2]
    else:
        difficulty= probfile.split('/')[-2]
        problemId = probfile.split('/')[-1]
    problemId = problemId.split('.')[-2]
    return [problemId, difficulty]

def call_test_problem(probfile, modelBtL, modelWtK, fout=None, skip=set()):
    ''' Returns 1 if problem is solved
        Returns 0 if problem could not be solved
        Returns -1 if problem could not be executed
    '''
    if probfile[-3:]=='sgf':
        [problemId, difficulty]=parse_problem_filename(probfile)
        if problemId in skip:
            print('Already did {} problem {}'.format(difficulty, problemId))
            return -1
        #print(probdiff)
        problemType = 'error'
        try:
            mtp = MoveTreeParser(probfile) 
            isBtL = (mtp.problemType == 1 or mtp.problemType==3)
            if not isBtL:
                return -1
            problemType = 'black-to-live' if isBtL else 'white-to-kill'
            print probfile
            test_problem(mtp, modelBtL, modelWtK)
            if fout is not None:
                fout.write('{},{},{},1\n'.format(problemId, problemType,difficulty))
            return 1
        except UnspecifiedProblemType:
            return -1
        except IllegalMove as im:
            print(im)
            return -1
        except YouLoseException as yle:
            print(yle)
            if fout is not None:
                fout.write('{},{},{},0\n'.format(problemId, problemType,difficulty))
            return 0
    else:
        raise Exception('{} is not a .sgf file'.format(probfile))
            
def load_model(modelFile, modelType, scalerFile):
    print('Loading model and scaler files...')
    model = Model(modelFile, modelType)
    model.setScaler(scalerFile)
    print('Model and scaler files ready!')
    return model

def test_problems(modelBtl, modelWtK, probdirs, outputfile, rerun=False, maxdepth=3):
    
    #test_problem(sys.argv[1], modelBtL, modelWtK)
    MinMaxTree.maxdepth=maxdepth
    problemsDone = set()
    if not rerun:
        try:
            with open(outputfile, 'r') as csvin: 
                rdr = csv.reader(csvin)
                for row in rdr:
                    problemsDone.add(row[0])
        except Exception:
            with open(outputfile, 'w') as fout:
                fout.write('PROBLEM,TYPE,DIFFICULTY,SCORE\n')

    else:
        with open(outputfile, 'w') as fout:
            fout.write('PROBLEM,TYPE,DIFFICULTY,SCORE\n')
        
    with open(outputfile, 'a') as fout:
        seed(1234567890)
        totalNumCorrect = 0
        totalTotal = 0
        for problemDir in probdirs:
            print problemDir
            numCorrect = 0
            numTotal = 0
            if not os.path.isdir(problemDir):
                if len(problemDir)<3:
                    print('Not a dir or problem file: {}'.format(problemDir))
                elif problemDir[-3:]=='sgf':
                    result = call_test_problem(problemDir, modelBtL, modelWtK, fout, skip=problemsDone)
                    if result>=0:
                        numTotal+=1
                        if result>0:
                            numCorrect+=1
                    if result!=-1:
                        print('Total: {}/{} correct'.format(numCorrect, numTotal))
                else:
                    print('Not a dir or problem file: {}'.format(problemDir))

            else:
                dirs = glob(problemDir+'/*')
                shuffle(dirs)
                for probdiff in dirs:
                    if os.path.isdir(probdiff):
                        files = glob(probdiff+'/*.sgf')
                        for probfile in files:
                            
                            result = call_test_problem(probfile, modelBtL, modelWtK, fout, skip=problemsDone)
                            if result>=0:
                                numTotal+=1
                                if result>0:
                                    numCorrect+=1
                        if result!=-1:
                            print('{}: {}/{} correct'.format(probdiff, numCorrect, numTotal))
                            
                    else:
                        if probdiff[-3:]=='sgf':
                            result = call_test_problem(probdiff, modelBtL, modelWtK, fout, skip=problemsDone)
                            if result>=0:
                                numTotal+=1
                                if result>0:
                                    numCorrect+=1
                        if result!=-1:
                            print('{}: {}/{} correct'.format(problemDir, numCorrect, numTotal))

            totalNumCorrect+=numCorrect
            totalTotal+=numTotal
            
        print('Total: {}/{} correct'.format(totalNumCorrect, totalTotal))
    

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="", conflict_handler='resolve', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # rerun problems, 
    parser.add_argument('--rerun_problems', '-r', action='store_true', help='rerun problems already run')
    parser.add_argument('--max_depth', '-d', default='3', metavar='int', type=int, choices=[x+1 for x in range(5)], help='maximum depth to search for the next move')
    parser.add_argument('model_dir', help='location of machine learning models')
    parser.add_argument('problem_dir_or_file', nargs='+', help='path to problem directory or file')
    '''
    parser.add_argument('json_file', help='json file with data for PPI forms to make predictions about', type=str)
    parser.add_argument('--specificity_model_file', help='stored specificity model', type=str, default=None, required=True)
    parser.add_argument('--ratings_model_file', help='stored ratings model', type=str, default=None, required=True)
    parser.add_argument('--sentiment_model_file', help='stored sentiment model', type=str, default=None, required=True)
    parser.add_argument('--n_jobs', help='number of parallel jobs for grid search', type=int, default=1)
        
    # load the models and args used to create them
    with open(args.specificity_model_file, 'rb') as f:
        specificity_clf, saved_args_specificity = pickle.load(f)
    with open(args.ratings_model_file, 'rb') as f:
    '''
    args = parser.parse_args()
    #if args.rerun_problems:
    
    # Sample main... make your own if you want something different
    # Just import load_model and test_problems
    modelDir = args.model_dir
    #modelFile = modelDir+'/modelNBBtL.txt'
    modelFile = modelDir+'/modelRF100BtL.txt'
    modelType = 3 
    scalerFile = modelDir+'/trainfeaturesBtLScaler.txt'
    modelBtL = load_model(modelFile, modelType, scalerFile)
    #modelFile = modelDir+'/modelNBWtK.txt'
    modelFile = modelDir+'/modelRF100WtK.txt'
    modelType = 3
    scalerFile = modelDir+'/trainfeaturesWtKScaler.txt'
    modelWtK = load_model(modelFile, modelType, scalerFile)
    problemDirs = args.problem_dir_or_file

    outputfile = modelDir+'/problem-test-results.txt'
    test_problems(modelBtL, modelWtK, problemDirs, outputfile, rerun=args.rerun_problems, maxdepth=args.max_depth)
    