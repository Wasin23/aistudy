from collections import deque
import math
import random
import numpy
import pandas
import time
import ollama
import json
import ast

# this project will be a way for me to practice my code.
# It will build upon itself
# I want to create a game of life with multiple characters that move around and make decisions
# The world will have natural disasters as well

# TODO LIST
# create fire using BFS: DONE
# Create earthquake using DFS: DONE
# sliding window algo for snow / heat: DONE
# Character memories for previous x positions to skew movement towards something, assigned to self.posHistory: DONE
# Food / resources: DONE

# use DSA for complex character movement, assignment of traits, and other environmental factors
# Have the list print every second with updates

# Currently, new characters are given random positions on the map, added to a dict, and then the dict is written to a characters file
# The characters file is retrieved on each startup
# Old characters that are not initialized persist despite not being initialized as the app pulls from what exists (in get_stats()) first

class world:
    def __init__(self, size, character: list[str]):
        self.size = size # set size input
        self.character = character # set character amount
        self.tick = None # create time 
        self.positions = {} # create dict of positions
        self.worlddict = {} # create dict of world info
        self.posHistory = {} # set dict of position history
        self.grid = []
        self.marked = []
        for char in self.character: self.positions[char] = None

    def time(self): # build time function
        with open("Time.txt", "r") as w:
            contents = w.read()
            time = contents.split(",")
            if contents:
                print(time)
                self.worlddict["Time"] = time
                self.tick = int(time[0]) 
        if self.worlddict: # if the time is recorded
            self.worlddict["Time"] = self.tick # set time equal to the current time
            self.tick += 1 # increment time by 1
        else: # else
            self.tick = 0 # set time equal to 0 if time is none
            self.worlddict["Time"] = self.tick # then create the key in the dict with the time
            self.tick += 1 # increment time by 1
            print(self.tick) # print the current time

    def trigger_disaster(self):
        class natural_disasters():
            def __init__(nd, left, right, up, down, leftup, leftdown, rightup, rightdown): # create disaster directions
                nd.left = left
                nd.right = right
                nd.up = up
                nd.down = down
                nd.leftup = leftup
                nd.leftdown = leftdown
                nd.rightup = rightup
                nd.rightdown = rightdown
                nd.dirlist = [nd.right, nd.left, nd.up, nd.down, nd.leftup, nd.leftdown, nd.rightup, nd.rightdown]
                nd.visited = {} # create dict of coordinates to show whats been visited

            def update(nd):
                with open("Disaster.txt", "r") as d:
                    contents = d.read()
                    spots = contents.split("\n")
                    for spot in spots: # loop through lists of coords per key
                        if not spot:
                            continue # if the line is only an empty string, continue
                        spottype = spot.split(",") # split the stats of each spot found into parts
                        if spottype[0] in self.worlddict: # if the particular key does exist
                            self.worlddict[spottype[0]].append([int(x) for x in spottype[1:]]) # at spottype (the key), convert the list to ints and append each list to the key values
                            coord = tuple(int(x) for x in spottype[1:]) # set coord equal to a tuple of the lists
                            nd.visited[coord] = spottype[0] # create a key for the lists at the coord tuple
                        else:
                            self.worlddict[spottype[0]] = [[int(x) for x in spottype[1:]]] # rebuild self.worlddict dict from Disaster.txt and set the positions as integers
                            coord = tuple(int(x) for x in spottype[1:])
                            nd.visited[coord] = spottype[0]
            
            def fire_BFS(nd): # create fire function
                if self.tick % 30 == 0: # if the tick is a multiple of 30, kill the fire
                    self.worlddict["Fire"] = [] # set fire to an empty list
                else:
                    oldfire_coords = [coord for coord, type in nd.visited.items() if type == "Fire"] # find the fire coordinates from the previous round and set it to oldfire
                    for coord in oldfire_coords: # loop through oldfire
                        del nd.visited[coord] # delete the previous records of oldfire inside the visited dict
                    if oldfire_coords:
                        queue = deque(oldfire_coords) # build queue for bfs by creating a list with the start coordinates 
                        dir = random.sample(nd.dirlist, 3) # set dir to a list of 3 randomly selected directions
                        for spot in list(oldfire_coords): # loop through the oldfire coordinates
                            spot = queue.popleft() # pop the first coordinate and set equal to spot
                            for i in dir: # loop through directions
                                # pick a random number between the 0 and the amount of fire spots times 5, 
                                # and if the remainer of that number divided by the fire spots divided by 2 is 0, spread the fire in the selected direction
                                if random.randint(0, len(self.worlddict["Fire"]) * 5) % ((len(self.worlddict["Fire"]) + 1) // 2) == 0:  
                                    s = list(spot) # s is the listed version of the tuple, spot
                                    newcoords = [(s[0] + i[0]) % (self.size), (s[1] + i[1]) % (self.size // 2)] # newcoords is the corrected coordinates (for out of bounds) of the fire
                                    newspot = tuple(newcoords) # convert newcoords list of updated coordinates back to a tuple
                                    if newspot in nd.visited: # if these coords already exist, ignore them
                                        continue
                                    else: # if they don't exist, add to the visited dict with the value "fire"
                                        queue.append(newspot) 
                                        nd.visited[tuple(newspot)] = "Fire"
                                else:
                                    continue
                            
                    elif self.tick % 21 == 0: # if the time is a multiple of 21 start a fire
                        print("A fire has started! (marked as X)")
                        start = [random.randint(0, self.size - 1), random.randint(0, (self.size // 2) - 1)] # set a random coordinate on the map on fire
                        queue = deque([start]) # build queue for bfs by creating a list with the start coordinates tupled
                        dir = random.sample(nd.dirlist, 3)
                        nd.visited[tuple(start)] = "Fire" # add the new start coords to fire inside visited

                    self.worlddict["Fire"] = list(coord for coord, type in nd.visited.items() if type == "Fire") # set worlddict at fire to the updated visited list

            def earthquake_DFS(nd): # create earthquake function
                if self.worlddict.get("Earthquake", []):
                    self.worlddict["Earthquake"] = []
                else:          
                    if self.tick % 5 == 0: # if the time is a multiple of 50 start an earthquake
                        print("An Earthquake has started! (marked as /)")
                        start = [random.randint(0, self.size - 1), random.randint(0, (self.size // 2) - 1)] # set a random coordinate on the map on Earthquake
                        dir = random.sample(nd.dirlist, 4)
                        nd.visited[tuple(start)] = "Earthquake" # add the new start coords to Earthquake inside visited
                        spot = start
                        for i in dir: # want to add this direction until it hits the end of the map
                            s = list(spot) # the selected coordinate taken from the queue
                            while 0 <= s[0] < self.size and 0 <= s[1] < self.size // 2: # while both coordinates are within the map
                                newcoords = [(s[0] + i[0]), (s[1] + i[1])] # set newcoords to the current coords + direction
                                newspot = tuple(newcoords) # set new coords to a tuple
                                s = list(newspot) # set s to a list again
                                if newspot in nd.visited: # if newspot already exists ignore
                                    continue
                                elif 0 <= s[0] < self.size and 0 <= s[1] < self.size // 2: # if s coords are in bounds 
                                    nd.visited[tuple(newspot)] = "Earthquake" # add to visited

                    self.worlddict["Earthquake"] = list([coord for coord, type in nd.visited.items() if type == "Earthquake"]) # set worlddict at earthquake to the updated visited list

            def storm_SW(nd):
                if self.tick % 10 == 0: # if tick is a multiple of 10 start a storm
                    grid = [self.size // 2, self.size] # set copy o the real grid
                    chargegrid = [] # use chargegrid to store charged values
                    for row in range(grid[0]): # loop through grid copy 
                        chargegrid.append([]) # add list to each row
                        for column in range(grid[1]): # loop through each item in row
                            column = random.randint(-10, 10) # assign a random value between -10 and 10
                            chargegrid[row].append(column) # add the value back to chargegrid
                    k = int(self.size * 0.1) # set k window size to 10% the x value of the grid
                    listOfGreatestValues = [] # initialize greatest values per row list
                    for row in chargegrid: # loop through chargegrid rows
                        bestlist = [] # initialize the list per row that tracks the greatest sum values from each k len window in the row
                        currentsum = sum(row[:k]) # start with a sum from start to k
                        bestlist.append(currentsum) # add to bestlist for this row
                        for item in range(k, len(row)): # loop through every other k len window
                            # set currentsum to its previous value added to the next value in the row, then subtract the back value (next window)
                            currentsum = currentsum + row[item] - row[item - k] 
                            bestlist.append(currentsum) # add the sum to bestlist
                        rowmax = max(bestlist) # find the max inside the rows list
                        rowmin = min(bestlist) # find the min inside the rows list
                        listOfGreatestValues.append([rowmax, rowmin]) # set greatest values per row into the list of the smallest and largest values inside each window
                    a = int(max(value[0] for value in listOfGreatestValues) / k) # set a to the largest sum in that set then averaged 
                    b = int(min(value[1] for value in listOfGreatestValues) / k) # set b to the smallest sum in that set then averaged 
                    deviationOfAllCharges = numpy.std(chargegrid) // random.randint(1, 4) # take standard deviation of all values and half it
                    if abs(a) > abs(b): # if heat is more extreme
                        for y, row in enumerate(chargegrid): # loop thru rows chargegrid
                            for x, item in enumerate(row): # loop through items in row
                                if item >= a - deviationOfAllCharges: # if each item is within a single sd of the averaged maxxed value
                                    nd.visited[(x, y)] = "Heat" # add the item's coords to the visited dict with value "Heat"
                        self.worlddict["Heat"] = list([coord for coord, type in nd.visited.items() if type == "Heat"]) # add to worlddict
                    elif abs(b) > abs(a): # if cold is more extreme
                        for y, row in enumerate(chargegrid): # loop thru rows chargegrid
                            for x, item in enumerate(row): # loop through items in row
                                if item <= b + deviationOfAllCharges: # if each item is within a single sd of the averaged maxxed value
                                    nd.visited[(x, y)] = "Snow" # add the item's coords to the visited dict with value "Snow"
                        self.worlddict["Snow"] = list([coord for coord, type in nd.visited.items() if type == "Snow"]) # add to worlddict
                elif (self.tick % 10) - 5 == 0: # after 5 rounds make the storm go away
                    self.worlddict["Heat"] = []
                    self.worlddict["Snow"] = []
                
        nd = natural_disasters([-1, 0], [1, 0], [0, 1], [0, -1], [-1, 1], [-1, -1], [1, 1], [1, -1]) # initialize natural disaster class with movement directions
        # call each natural disaster
        nd.update()
        nd.fire_BFS()
        nd.earthquake_DFS()
        nd.storm_SW()

    def food(self):
        self.worlddict["Food"] = None
        with open("Disaster.txt", "r") as r:
            contents = r.read()
            lines = contents.split("\n")
            for line in lines:
                if line.split(",")[0] == "Food":
                    self.worlddict["Food"] = [[int(line.split(",")[1]), int(line.split(",")[2])]]

        if self.worlddict["Food"] is None: # if no food exists
            disastercoordlist = [coord for value in self.worlddict if value != "Time" and value != "Food" for coord in self.worlddict[value]] # make list of coords of all disasters
            differenceDict = {} # set dict of all point differences between disasters
            for row in range(self.size // 2): # loop thru rows in grid
                for column in range(self.size): # loop thru each value in the row
                    bigx = []
                    bigy = []
                    for coord in disastercoordlist: # loop through disaster list
                        bigx.append(abs(column - coord[0])) # add the difference between the point and each disaster coordinate at x
                        bigy.append(abs(row - coord[1])) # add the difference between the point and each disaster coordinate at y
                    a = sum(bigx) + sum(bigy) # add both values per point
                    differenceDict[(row, column)] = a # append the value to difference dict with the key as its coordinates
            best = max(differenceDict.values()) # return the biggest value in the dict
            coordinatesToAddFood = [key for key, value in differenceDict.items() if value == best] # find the coordinates that key that value
            self.worlddict["Food"] = [[coordinatesToAddFood[0][1], coordinatesToAddFood[0][0]]] # set food to those coordinates
        else:
            pass

    def land(self):    
        self.grid = [["."] * self.size for i in range(self.size // 2)] # create a grid for the characters to traverse
        for char in self.positions: # for each character in the dict
            x = self.positions[char][0] # x coordinate value in self.positions 
            y = self.positions[char][1] # y coordinate value in self.positions 
            self.grid[y][x] = "@" # set the grid spot at position row x col to an @ symbol to indicate a character's position
        for condition in self.worlddict: # loop through worlddict
            if condition != "Time" and condition: # if the condition name is not time and exists
                assign = self.worlddict[condition] # set assign to the list of lists at condition
                for coords in assign: # loop through the list
                    x = coords[0] # set x to the 0th index in the list
                    y = coords[1] # set y to the 1st index in the list
                    if condition == "Fire": # if condition string is fire mark the grid coords wih an X
                        self.grid[y][x] = "X"
                    if condition == "Earthquake": # if condition string is earthquake mark the grid coords wih /
                        self.grid[y][x] = "/"
                    if condition == "Heat": # if condition is head mark coords with "^"
                        self.grid[y][x] = "^"
                    if condition == "Snow": # if condition is snow mark coords with "*"
                        self.grid[y][x] = "*"
                    if condition == "Food": # if condition is food mark coords with "O"
                        self.grid[y][x] = "O"
        return self.grid

    def get_stats(self):
            with open("characters.txt", "r") as f: # open db of characters and their positions
                contents = f.read() # create object of contents
                lines = contents.split("\n") # becomes a list of the contents split by newline (endl)
                for line in lines: # loop through list of lines
                    if not line:
                        continue # if the line is only an empty string, continue
                    charstat = line.split(",") # split the stats of each character found into parts
                    print(charstat) # print the stats
                    self.positions[charstat[0]] = [int(x) for x in charstat[1:]] # rebuild self.positons dict from characters.txt and set the positions as integers
            with open("PositionHistory.txt", "r") as r:
                contents = r.read()
                lines = contents.split("\n")
                for line in lines:
                    if not line:
                        continue
                    pastpos = [int(line.split(",")[3]), int(line.split(",")[4])]
                    currentpos = [int(line.split(",")[1]), int(line.split(",")[2])]
                    self.posHistory[line.split(",")[0]] = [currentpos, pastpos]

    def characters(self):
        for char in self.character:
            c = [x for x in self.positions.values() if x is not None] # create a list of the positions recorded
            if len(c) >= (self.size // 2) * self.size: # if the length of the positions exceeds or is equal to the size of the map
                print("Cannot Assign Character, All Spots Full") # print this message and break
                break
            if self.positions[char] is None: # if the character is already found, leave it be, if not found, assign a position
                while True:
                    x = random.randint(0, self.size - 1) # set random col from 0 to the input size
                    y = random.randint(0, (self.size // 2) - 1) # set random row from 0 to the input size
                    s = [x, y] # set s to a list with the x and y coords of the char
                    for value in self.positions.values(): # loop thru values inside self.positions
                        if value == s: # if a value (a current char position) already matches s, try again
                            print("reassigning")
                            break
                    else: # if not
                        self.positions[char] = s # set the random position in the dict given the new character 
                        break

    def movement(self):
        class moves():
            def __init__(move, left, right, up, down, chanceToMove=0): # initialize move object, then directions
                move.left = left
                move.right = right
                move.up = up
                move.down = down
                move.chanceToMove = chanceToMove

        for char in self.positions:
            for key in self.worlddict:
                if key != "Time" and key != "Heat" and key != "Snow" and key != "Food" and tuple(self.positions[char]) in self.worlddict[key]:
                    self.marked.append(char)
            charRadius = []
            xpos = self.positions[char][0]
            ypos = self.positions[char][1]
            for entry in self.worlddict:
                if entry != "Time" and entry != "Food":
                    for coord in self.worlddict[entry]:
                        if abs(coord[0] - xpos) <= 5 and abs(coord[1] - ypos) <= 5:
                            lista = [coord[0], coord[1]]
                            charRadius.append(lista)
            if char in self.marked: # if the current character is marked for death, skip
                continue
            else:
                dirDict = {}
                dirDict["0"] = [self.positions[char][0] - 1, self.positions[char][1] + 0] # left
                dirDict["1"] = [self.positions[char][0] + 1, self.positions[char][1] + 0] # right
                dirDict["2"] = [self.positions[char][0] + 0, self.positions[char][1] - 1] # down
                dirDict["3"] = [self.positions[char][0] + 0, self.positions[char][1] + 1] # up
                dirDict["4"] = [self.positions[char][0] - 1, self.positions[char][1] + 1] # leftup
                dirDict["5"] = [self.positions[char][0] - 1, self.positions[char][1] - 1] # leftdown
                dirDict["6"] = [self.positions[char][0] + 1, self.positions[char][1] + 1] # rightup
                dirDict["7"] = [self.positions[char][0] + 1, self.positions[char][1] - 1] # rightdown
                schema = { # set schema for ollama
                    "type": "object",
                    "properties": {
                        "choice": {"type": "integer", "enum": [0,1,2,3,4,5,6,7]}
                    },
                    "required": ["choice"]
                }
                response = ollama.chat( # get model then systemprompt the model, then set return format to json 
                    model = 'llama3.2',
                    messages = [
                        {'role': 'user', 'content': f'Your current position is {self.positions[char]}. The positions of the danger around you are {charRadius}. Your past position was {self.posHistory.get(char, [None, None])[1]}. The food is located at {self.worlddict["Food"]}. Your goal is to avoid danger and eat food. Your options of movement are {dirDict["0"]}, {dirDict["1"]}, {dirDict["2"]}, {dirDict["3"]}, {dirDict["4"]}, {dirDict["5"]}, {dirDict["6"]}, {dirDict["7"]}. Minimize the distance between your position and the food. Return your answer as an int 0 through 7'}
                    ],
                    format = schema
                )
                print(f"Ai Choice: {str(json.loads(response.message.content)["choice"])}") # print model's answer json parsed
                aimove = str(json.loads(response.message.content)["choice"]) # set answer
                coords = dirDict[aimove] # set coords to the dict at answer
                coords[0] = coords[0] % self.size # wrap coords
                coords[1] = coords[1] % (self.size // 2) 
                checkedAIMove = coords
                self.posHistory[char] = [checkedAIMove, self.positions[char]]
                self.positions[char] = checkedAIMove # set char position to ai's decision
                if char == "Test":
                    move = moves(random.randint(0, 1), random.randint(0, 1), random.randint(0, 1), random.randint(0, 1)) # set directions to random values
                    for key in self.worlddict:
                        if key == "Heat" and tuple(self.positions[char]) in self.worlddict[key]:
                            move.chanceToMove = 2
                        elif key == "Snow" and tuple(self.positions[char]) in self.worlddict[key]:
                            move.chanceToMove = 1
                    xchange = move.right - move.left # simplify down to a move on x axis
                    ychange = move.up - move.down # simplify to a move on y axis
                    if move.chanceToMove == 1:
                        xchange = 0
                        ychange = 0
                    elif move.chanceToMove == 2:
                        xchange = random.randint(-4, 4)
                        ychange = random.randint(-4, 4)
                    else:
                        pass
                    self.positions[char][0] = (self.positions[char][0] + xchange) % self.size # keep positions within bounds
                    self.positions[char][1] = (self.positions[char][1] + ychange) % (self.size // 2)
            for x in self.positions:
                if x in self.marked: # if the other character has been added to marked, skip
                    continue
                # if the second character is equal to the current moving character's position and the current moving isn't itself, do...
                elif self.positions[x] == self.positions[char] and self.positions[x] is not self.positions[char]: 
                    roll = random.randint(0, 1) # random interaction picker
                    if roll == 1: # first interaction --> random death
                        s = random.randint(0, 10)
                        if s >= 6: # if coinflip is greater than 5
                            self.marked.append(char) # mark current moving char for death
                        if s <= 5: # if coinflip is less than 6
                            self.marked.append(x) # mark char already in position for death
                if self.worlddict["Food"] and self.positions[x] == self.worlddict["Food"][0]:
                    self.worlddict["Food"] = None
            for key in self.worlddict:
                # if the key (uniterable so checked for first) is not time and the tuple of a characters position is inside the worlddict
                if key != "Time" and key != "Food" and key != "Heat" and key != "Snow" and tuple(self.positions[char]) in self.worlddict[key]:
                    self.marked.append(char) # add to marked for death
        for name in set(self.marked): 
            print(f"{name} dies!")
            del self.positions[name] 
                           
    def save(self):
        with open("characters.txt", "w") as f: 
            for char in self.positions: # loop though positions dict
                f.write(f"{char},{self.positions[char][0]},{self.positions[char][1]}\n") # write character positions to the charcters file as a save
        with open("PositionHistory.txt", "w") as w:
            for char in self.posHistory:
                w.write(f"{char},{self.posHistory[char][0][0]},{self.posHistory[char][0][1]},{self.posHistory[char][1][0]},{self.posHistory[char][1][1]}\n")
        with open("Time.txt", "w") as w: # open time file save
            w.write(f"{self.tick}") # save self.tick written from the loop in time()
        with open("Disaster.txt", "w") as w: # open disaster progress file
            if self.worlddict.get("Fire", []): # if the worlddict at fire exists
                for coord in self.worlddict.get("Fire", []): # loop through the coordinates at the fire key
                    w.write(f"Fire,{coord[0]},{coord[1]}\n") # split each coordinate value by comma and key with "Fire"
            if self.worlddict.get("Earthquake", []): # if the worlddict at earthquake exists
                for coord in self.worlddict.get("Earthquake", []): # loop through the coordinates at the Earthquake key
                    w.write(f"Earthquake,{coord[0]},{coord[1]}\n") # split each coordinate value by comma and key with "Earthquake"
            if self.worlddict.get("Heat", []): # if worlddict at heat exists
                for coord in self.worlddict.get("Heat", []): # loop through the coordinates at the Heat key
                    w.write(f"Heat,{coord[0]},{coord[1]}\n") # split each coordinate value by comma and key with "Heat"
            if self.worlddict.get("Snow", []): # if worlddict at snow exists
                for coord in self.worlddict.get("Snow", []): # loop through the coordinates at the snow key
                    w.write(f"Snow,{coord[0]},{coord[1]}\n") # split each coordinate value by comma and key with "Snow"
            if self.worlddict.get("Food", []): # if worlddict at Food exists
                for coord in self.worlddict.get("Food", []): # loop through the coordinates at the Food key
                    w.write(f"Food,{coord[0]},{coord[1]}\n") # split each coordinate value by comma and hea with "Food"

userInput = input("Would you like to start the game? ")
if userInput.upper() == "YES":
    peopleList = [input("Who would you like to add to the game? ")]
    while True:
        w = world(50, peopleList)
        w.time()
        w.get_stats()
        w.characters()
        w.trigger_disaster()
        w.food()
        w.movement()
        w.save()
        for row in w.land():
            print("".join(row))
        time.sleep(1)
else:
    print("Ending Program")