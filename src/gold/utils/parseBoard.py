'''
Created on Oct 28, 2014

@author: Zac1164
'''

from array import array

from gold.models.board import Board

import re

size = 19

currentGame = open("games/5.sgf")

gameData = currentGame.read()

boardSizeLocation = gameData.find("SZ")
sizeString = ''
counter = 0
currentChar = gameData[boardSizeLocation + counter + 3]
while(currentChar != ']'):
  sizeString += currentChar
  counter += 1
  currentChar = gameData[boardSizeLocation + counter + 3]

if(sizeString.isdigit()):
  size = int(sizeString)

currentBoard = Board(size,size)

whitePositionLocations = [m.start() for m in re.finditer('AW', gameData)]
blackPositionLocations = [m.start() for m in re.finditer('AB', gameData)]

stonePositions = whitePositionLocations + blackPositionLocations
stonePositions.sort()

for i in stonePositions:
  isBlack = False
  if i in blackPositionLocations:
    isBlack = True
  counter = 0
  while(True):
    currentChar = gameData[i + counter + 2]
    if (currentChar != '['):
      break
    currentChar = gameData[i + counter + 3]
    y = ord(currentChar) - ord('a')
    currentChar = gameData[i + counter + 4]
    x = ord(currentChar) - ord('a')
    currentBoard.place_stone(x,y,isBlack)
    counter += 4

print currentBoard

currentGame.close()

