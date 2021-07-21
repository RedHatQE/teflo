from teflo.resources.scenario import Scenario


class ScenarioGraph():

    def __init__(self, root_scenario: Scenario = None, iterate_method: str = "by_level"):
        '''
        Initialization of a Sceanario Graph
        :param root_scenario: root teflo scenario object containing
        all scenario data and included scenarios
        :type root_scenario: scenario object
        :param iterate_method: iterate method for the graph traversal
        :type iterate_method: str
        '''
        self._root = root_scenario
        self._stack = []
        if iterate_method == "by_depth":

            self._stack = [root_scenario]
        elif iterate_method == "by_level":
            self._stack.append([self.root])
        self._prev = None
        self._current = None
        self._visited = {}
        # There are two ways of loading resource
        # 1. by_depth
        # 2. by_level
        self._iterate_method = iterate_method
        # TODO: This should be reading from root.config["included_sdf_iterate_method"]

# root
    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, root):
        self.__init__(root, self.iterate_method)

# stack
    @property
    def stack(self):
        return self._stack

    @stack.setter
    def stack(self, stack):
        self._stack = stack

# prev
    @property
    def prev(self):
        return self._prev

    @prev.setter
    def prev(self, prev):
        self._prev = prev

# current
    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, current):
        self._current = current

# visited
    @property
    def visited(self):
        return self._visited

    @visited.setter
    def visited(self, visited):
        self._visited = visited

# iterate_method
    @property
    def iterate_method(self):
        return self._iterate_method

    @iterate_method.setter
    def iterate_method(self):
        #  TODO: allow modify iterate_method from cli
        raise ValueError("you cannot set iterate_method of the scenario_graph")

# iteration implemetation
    def is_visited(self, sc):
        '''
        Check if a scenario object has been visited or not
        '''
        return self.visited.get(sc, False)

    def next_unvisited_sc(self, sc_list):
        for sc in sc_list:
            if not self.is_visited(sc):
                return sc
        return None

# TODO: Make this to static attribute
# size
    @property
    def size(self):
        count = 0
        for sc in self:
            count += 1
        return count

    @size.setter
    def size(self, size):
        raise ValueError("you cannot set the size of the scenario_graph")

    def __len__(self):
        return self.size

    def hasChild(self, sc_list):
        '''
        Check if any scenario obejct in a list of scenarios
        contains a child
        '''
        return True in [len(sc.child_scenarios) != 0 for sc in sc_list]

    def __iter__(self):
        return self

    def __next__(self):
        '''
        The iterator method of Scenario Graph
        It is also the most important place of the ScenarioGraph Class
        It has two `iterate_method` way of traversal order

        Example:

        ->sdf0.yml
            ->sdf1.yml
                ->sdf3.yml
                ->sdf8.yml
                    ->sdf12.yml
                    ->sdf13.yml
                ->sdf5.yml
            ->sdf7.yml
                ->sdf10.yml
                ->sdf11.yml
            ->sdf2.yml
                ->sdf4.yml
                ->sdf9.yml
                ->sdf6.yml


        if iterate_method is by_depth: the traversal order will be:
            12,13,3,8,5,1,10,11,7,4,9,6,2,0
        if iterate_method is by_level: the traversal order will be:
            12,13,3,8,5,10,11,4,9,6,1,7,2,0
        '''

        if self.root is None:
            raise StopIteration

        if self.iterate_method == "by_depth":

            while len(self.stack) is not 0:
                self.current = self.stack[-1]
                if self.prev is None or self.current in self.prev.child_scenarios:

                    if self.next_unvisited_sc(self.current.child_scenarios) is not None:
                        next_sc = self.next_unvisited_sc(self.current.child_scenarios)
                        self.stack.append(next_sc)
                        self.visited[next_sc] = True
                    else:
                        self.visited[self.stack.pop()] = True
                        self.prev = self.current
                        return self.current
                elif(self.prev in self.current.child_scenarios and self.prev is not self.current.child_scenarios[-1]):
                    if self.next_unvisited_sc(self.current.child_scenarios) is not None:
                        next_sc = self.next_unvisited_sc(self.current.child_scenarios)
                        self.stack.append(next_sc)
                        self.visited[next_sc] = True
                    else:
                        self.visited[self.stack.pop()] = True
                        self.prev = self.current
                        return self.current
                else:
                    self.visited[self.stack.pop()] = True
                    self.prev = self.current
                    return self.current
                self.prev = self.current

            self.__init__(self.root, self.iterate_method)
            raise StopIteration

        elif self.iterate_method == "by_level":

            def addChildren(sc_list):
                size = len(sc_list)
                for i in range(size - 1, -1, -1):
                    sc = sc_list[i]
                    child = sc.child_scenarios
                    if len(child) != 0:
                        self.stack.append(child)

            while len(self.stack) is not 0:
                # current scenario list
                self.current = self.stack[-1]

                # From top to down
                top_down = self.prev is not None and True in [(self.current == sc.child_scenarios) for sc in self.prev]
                if self.prev is None or top_down:
                    # current is a list of scenario
                    if self.hasChild(self.current):
                        addChildren(self.current)
                    else:
                        for sc in self.current:
                            if not self.is_visited(sc):
                                self.visited[sc] = True
                                return sc
                        self.stack.pop()
                else:
                    for sc in self.current:
                        if not self.is_visited(sc):
                            self.visited[sc] = True
                            return sc
                    self.stack.pop()

                self.prev = self.current

            self.__init__(self.root, self.iterate_method)
            raise StopIteration

    def __str__(self):
        '''
        This will return a string containing the structure of the scenario graph
        '''
        return self.root.graph_str()
